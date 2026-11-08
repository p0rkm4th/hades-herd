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


def load_ollama_summary(path: Path) -> list[dict[str, Any]]:
    """Load content-free Ollama proxy JSONL records for /api/chat only."""
    records = []
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        raise TraceError(f"cannot read Ollama proxy summary {path}: {exc}") from exc
    for number, line in enumerate(lines, 1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TraceError(f"invalid Ollama JSON on line {number}: {exc}") from exc
        if not isinstance(record, dict):
            raise TraceError(f"Ollama record on line {number} must be an object")
        request = record.get("request")
        if (
            record.get("method") != "POST"
            or not isinstance(request, dict)
            or request.get("endpoint") != "/api/chat"
        ):
            continue
        started = record.get("started_monotonic_ns")
        finished = record.get("finished_monotonic_ns")
        if any(type(value) is not int or value < 0 for value in (started, finished)):
            raise TraceError(f"Ollama chat record on line {number} needs monotonic timestamps")
        if finished < started:
            raise TraceError(f"Ollama chat record on line {number} finishes before it starts")
        records.append(record)
    return sorted(records, key=lambda item: item["started_monotonic_ns"])


def correlate_tool_names(
    codex_requests: list[dict[str, Any]], ollama_records: list[dict[str, Any]]
) -> dict[str, Any]:
    """Compare ordered tool-name sequences within non-overlapping request windows.

    No IDs, arguments, content, or exact call identity are used. Ambiguous
    backend records remain unassigned instead of being matched by proximity.
    """
    ordered_codex = sorted(codex_requests, key=lambda item: item["request_sequence"])
    ordered_ollama = sorted(ollama_records, key=lambda item: item["started_monotonic_ns"])
    backend_by_codex: dict[int, list[dict[str, Any]]] = {
        item["request_sequence"]: [] for item in ordered_codex
    }
    unassigned_backend = 0
    for backend in ordered_ollama:
        start = backend["started_monotonic_ns"]
        finish = backend["finished_monotonic_ns"]
        candidates = [
            request for request in ordered_codex
            if request["request_started_monotonic_ns"] <= start
            and finish <= request["response_finished_monotonic_ns"]
        ]
        if len(candidates) != 1:
            unassigned_backend += 1
            continue
        backend_by_codex[candidates[0]["request_sequence"]].append(backend)

    rows = []
    for index, request in enumerate(ordered_codex):
        response_items = request.get("response_items", [])
        codex_names = [
            item["name"] for item in response_items
            if isinstance(item, dict) and item.get("type") == "function_call"
            and isinstance(item.get("name"), str)
        ] if isinstance(response_items, list) else []
        matched_backend = sorted(
            backend_by_codex[request["request_sequence"]],
            key=lambda item: item["started_monotonic_ns"],
        )
        ollama_names = []
        exchange_summaries = []
        successful_backend = [item for item in matched_backend if item.get("status_code") == 200]
        for backend in successful_backend:
            backend_request = backend.get("request", {})
            if not isinstance(backend_request, dict):
                backend_request = {}
            offer_present = backend_request.get("tools_field_present")
            offered_names = backend_request.get("tool_names", [])
            if not isinstance(offered_names, list):
                offered_names = []
            offered_names = [name for name in offered_names if isinstance(name, str)]
            response = backend.get("response", {})
            names = response.get("tool_call_names", []) if isinstance(response, dict) else []
            if not isinstance(names, list):
                names = []
            names = [name for name in names if isinstance(name, str)]
            if isinstance(names, list):
                ollama_names.extend(names)
            exchange_summaries.append({
                "tools_field_present": offer_present if isinstance(offer_present, bool) else None,
                "offered_tool_names": offered_names,
                "returned_tool_names": names,
                "unadvertised_tool_names": list(dict.fromkeys(
                    name for name in names
                    if isinstance(offer_present, bool)
                    and (not offer_present or name not in offered_names)
                )),
            })
        unadvertised_names = list(dict.fromkeys(
            name for exchange in exchange_summaries
            for name in exchange["unadvertised_tool_names"]
        ))

        next_prior_names = None
        next_prior_results = None
        for later in ordered_codex[index + 1:]:
            meta = later.get("request", {})
            if isinstance(meta, dict) and isinstance(meta.get("prior_function_call_names"), list):
                next_prior_names = [
                    name for name in meta["prior_function_call_names"] if isinstance(name, str)
                ]
                count = meta.get("tool_result_count")
                next_prior_results = count if type(count) is int and count >= 0 else None
                break
        suffix_matches = (
            next_prior_names[-len(codex_names):] == codex_names
            if codex_names and next_prior_names is not None
            and len(next_prior_names) >= len(codex_names)
            else (not codex_names if next_prior_names is not None else None)
        )
        rows.append({
            "request_sequence": request["request_sequence"],
            "codex_response_tool_names": codex_names,
            "ollama_response_tool_names": ollama_names,
            "ollama_exchanges": exchange_summaries,
            "unadvertised_ollama_tool_names": unadvertised_names,
            "ollama_chat_request_count": len(matched_backend),
            "successful_ollama_response_count": len(successful_backend),
            "backend_observation": (
                "missing" if not matched_backend
                else "complete" if len(successful_backend) == len(matched_backend)
                else "partial" if successful_backend
                else "failed"
            ),
            "ordered_names_match": (
                ollama_names == codex_names
                if matched_backend and len(successful_backend) == len(matched_backend) else None
            ),
            "next_request_prior_tool_names": next_prior_names,
            "next_request_prior_tool_result_count": next_prior_results,
            "next_request_names_end_with_response_calls": suffix_matches,
        })
    return {
        "requests": rows,
        "unassigned_ollama_chat_records": unassigned_backend,
        "correlation_limit": (
            "Matching timestamps and tool-name order is evidence of sequence consistency, "
            "not call identity. Overlapping or incomplete observations remain unassigned."
        ),
    }


def correlate(requests: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
    """Count command events in each non-overlapping response-to-next-request gap."""
    requests = sorted(requests, key=lambda item: item["request_sequence"])
    events = sorted(events, key=lambda item: item["monotonic_ns"])
    rows = []
    unassigned = 0
    assigned_event_indexes: set[int] = set()
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
            gap_event_indexes = []
        else:
            gap_event_indexes = [
                event_index for event_index, event in enumerate(events)
                if event["monotonic_ns"] > finished
                and (boundary is None or event["monotonic_ns"] < boundary)
                and event.get("item_type") == "command_execution"
            ]
            gap_events = [events[event_index] for event_index in gap_event_indexes]
            assigned_event_indexes.update(gap_event_indexes)
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
    command_events = [
        (index, event) for index, event in enumerate(events)
        if event.get("item_type") == "command_execution"
        and event.get("type") in {"item.started", "item.completed"}
    ]

    def count_command_events(indexes: set[int]) -> dict[str, int]:
        selected = [(index, event) for index, event in command_events if index in indexes]
        completed = [event for _, event in selected if event.get("type") == "item.completed"]
        return {
            "started": sum(event.get("type") == "item.started" for _, event in selected),
            "completed": len(completed),
            "completed_successfully": sum(event.get("item_status") == "completed" for event in completed),
            "completed_failed": sum(event.get("item_status") == "failed" for event in completed),
            "completed_other": sum(event.get("item_status") not in {"completed", "failed"} for event in completed),
        }

    all_command_indexes = {index for index, _ in command_events}
    return {
        "requests": rows,
        "overlapping_request_gaps_unassigned": unassigned,
        "command_event_summary": {
            "total": count_command_events(all_command_indexes),
            "assigned_to_nonoverlapping_gaps": count_command_events(assigned_event_indexes),
            "unassigned": count_command_events(all_command_indexes - assigned_event_indexes),
        },
        "correlation_limit": (
            "A non-overlapping time gap is suggestive, not an ID-level match. "
            "Overlapping requests and parallel commands cannot be paired from sanitized metadata alone."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proxy_summary", type=Path)
    parser.add_argument("codex_event_index", type=Path)
    parser.add_argument("--ollama-summary", type=Path,
                        help="optional content-free Ollama /api/chat JSONL capture")
    args = parser.parse_args()
    try:
        output = correlate(load_summary(args.proxy_summary), load_events(args.codex_event_index))
        if args.ollama_summary:
            output["tool_name_correlation"] = correlate_tool_names(
                load_summary(args.proxy_summary), load_ollama_summary(args.ollama_summary)
            )
    except TraceError as exc:
        print(f"correlate_codex_trace: {exc}", file=sys.stderr)
        return 2
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
