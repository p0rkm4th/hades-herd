#!/usr/bin/env python3
"""Join sanitized Codex event times to sanitized Herd Responses metadata.

This reports temporal proximity only. It has no call IDs or command text, so it
cannot prove a one-to-one relationship when requests overlap or tools run in
parallel.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


class TraceError(ValueError):
    pass


def load_summary(path: Path) -> list[dict[str, Any]]:
    try:
        root = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise TraceError(f"cannot read proxy summary {path}: {exc}") from exc
    if not isinstance(root, dict) or not isinstance(root.get("requests"), list):
        raise TraceError("proxy summary must contain a requests array")
    requests = []
    for request in root["requests"]:
        if not isinstance(request, dict):
            raise TraceError("proxy request entry must be an object")
        if (
            request.get("method") != "POST"
            or urlsplit(str(request.get("path", ""))).path.rstrip("/") != "/v1/responses"
        ):
            continue
        sequence = request.get("request_sequence")
        started = request.get("request_started_monotonic_ns")
        finished = request.get("response_finished_monotonic_ns")
        if any(type(value) is not int or value < 0 for value in (sequence, started, finished)):
            raise TraceError("proxy requests need nonnegative integer sequence/start/finish timestamps")
        if finished < started:
            raise TraceError(f"request {sequence} finishes before it starts")
        requests.append(request)
    requests.sort(key=lambda item: item["request_sequence"])
    sequences = [item["request_sequence"] for item in requests]
    if len(sequences) != len(set(sequences)):
        raise TraceError("proxy request_sequence values must be unique")
    return requests


def load_events(path: Path) -> list[dict[str, Any]]:
    events = []
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        raise TraceError(f"cannot read Codex event index {path}: {exc}") from exc
    for number, line in enumerate(lines, 1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TraceError(f"invalid event JSON on line {number}: {exc}") from exc
        if not isinstance(event, dict) or type(event.get("monotonic_ns")) is not int:
            raise TraceError(f"event line {number} needs an integer monotonic_ns")
        if event["monotonic_ns"] < 0:
            raise TraceError(f"event line {number} has a negative monotonic_ns")
        events.append(event)
    return sorted(events, key=lambda item: item["monotonic_ns"])


def correlate(requests: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
    """Count command events in each non-overlapping response-to-next-request gap."""
    requests = sorted(requests, key=lambda item: item["request_sequence"])
    events = sorted(events, key=lambda item: item["monotonic_ns"])
    rows = []
    unassigned = 0
    for index, request in enumerate(requests):
        request_meta = request.get("request", {})
        if not isinstance(request_meta, dict):
            request_meta = {}
        output_items = request.get("response_items", [])
        if not isinstance(output_items, list):
            output_items = []
        function_items = [
            item for item in output_items
            if isinstance(item, dict) and item.get("type") == "function_call"
        ]
        boundary = requests[index + 1]["request_started_monotonic_ns"] if index + 1 < len(requests) else None
        finished = request["response_finished_monotonic_ns"]
        overlap = boundary is not None and boundary < finished
        if overlap:
            gap_events = []
        else:
            gap_events = [
                event for event in events
                if event["monotonic_ns"] > finished
                and (boundary is None or event["monotonic_ns"] < boundary)
                and event.get("item_type") == "command_execution"
            ]
        starts = sum(event.get("type") == "item.started" for event in gap_events)
        completed = sum(
            event.get("type") == "item.completed" and event.get("item_status") == "completed"
            for event in gap_events
        )
        failed = sum(
            event.get("type") == "item.completed" and event.get("item_status") == "failed"
            for event in gap_events
        )
        if overlap:
            unassigned += 1
        rows.append({
            "request_sequence": request["request_sequence"],
            "tools_field_present": request_meta.get("tools_field_present"),
            "advertised_tool_count": request_meta.get("top_level_tool_count"),
            "additional_tool_count": request_meta.get("additional_tool_count"),
            "prior_function_call_count": len(request_meta.get("prior_function_call_names", []))
                if isinstance(request_meta.get("prior_function_call_names"), list) else None,
            "prior_tool_result_count": request_meta.get("tool_result_count"),
            "response_function_call_count": len(function_items),
            "response_function_names": sorted({
                item["name"] for item in function_items if isinstance(item.get("name"), str)
            }),
            "next_request_started_before_response_finished": overlap,
            "command_starts_in_gap": None if overlap else starts,
            "command_completions_in_gap": None if overlap else completed,
            "command_failures_in_gap": None if overlap else failed,
            "response_terminal_status": request.get("terminal_status"),
        })
    return {
        "requests": rows,
        "overlapping_request_gaps_unassigned": unassigned,
        "correlation_limit": (
            "A non-overlapping time gap is suggestive, not an ID-level match. "
            "Overlapping requests and parallel commands cannot be paired from sanitized metadata alone."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proxy_summary", type=Path)
    parser.add_argument("codex_event_index", type=Path)
    args = parser.parse_args()
    try:
        output = correlate(load_summary(args.proxy_summary), load_events(args.codex_event_index))
    except TraceError as exc:
        print(f"correlate_codex_trace: {exc}", file=sys.stderr)
        return 2
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
