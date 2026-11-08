#!/usr/bin/env python3
"""Loopback-only Codex-to-Herd proxy that records metadata, never message text."""

from __future__ import annotations

import argparse
import http.client
import json
import os
import select
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

try:
    from .tool_schema_metadata import tool_schema_metadata
except ImportError:  # Direct execution as a fixture script.
    from tool_schema_metadata import tool_schema_metadata


def tool_names(tools: Any) -> tuple[list[str], list[dict[str, Any]]]:
    """Return advertised names and structural metadata without schemas."""
    names: set[str] = set()
    shapes: list[dict[str, Any]] = []
    if not isinstance(tools, list):
        return [], []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        name = tool.get("name")
        nested = tool.get("tools", [])
        nested = nested if isinstance(nested, list) else []
        nested_names = sorted(
            item["name"] for item in nested
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        )
        if isinstance(name, str):
            names.add(name)
        names.update(nested_names)
        shapes.append({"type": tool.get("type"), "name": name, "nested_names": nested_names})
    return sorted(names), shapes


class SSEMetadata:
    """Incrementally extract response item metadata, discarding all text/args."""

    def __init__(self) -> None:
        self._buffer = b""
        self.items: list[dict[str, Any]] = []
        # IDs are used only transiently to merge added/done/completed events.
        # They are never included in the serialized trace.
        self._seen_call_ids: set[str] = set()
        self._seen_items = False
        self.terminal_status: str | None = None
        self.usage: dict[str, int] | None = None

    def feed(self, chunk: bytes) -> None:
        self._buffer += chunk
        while True:
            # Search the entire buffer: ordinary line endings occur before the
            # blank-line frame delimiter. Keeping the bytes intact also handles
            # either delimiter being split across feed() calls.
            markers = [
                (position, delimiter)
                for delimiter in (b"\n\n", b"\r\n\r\n")
                if (position := self._buffer.find(delimiter)) >= 0
            ]
            if not markers:
                return
            marker, delimiter = min(markers, key=lambda pair: pair[0])
            frame, self._buffer = self._buffer[:marker], self._buffer[marker + len(delimiter):]
            self._frame(frame.replace(b"\r\n", b"\n"))

    def _frame(self, frame: bytes) -> None:
        data = b"\n".join(line[5:].lstrip() for line in frame.splitlines() if line.startswith(b"data:"))
        if not data or data == b"[DONE]":
            return
        try:
            event = json.loads(data)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        if not isinstance(event, dict):
            return
        kind = event.get("type")
        if kind in {"response.output_item.added", "response.output_item.done"}:
            item = event.get("item", {})
            if isinstance(item, dict):
                if item.get("type") == "function_call":
                    call_id = item.get("call_id")
                    if isinstance(call_id, str):
                        if call_id in self._seen_call_ids:
                            return
                        self._seen_call_ids.add(call_id)
                    elif kind == "response.output_item.added":
                        return
                self._append_item(item)
        elif kind == "response.completed":
            response = event.get("response", {})
            if isinstance(response, dict):
                self.terminal_status = response.get("status")
                usage = response.get("usage")
                if isinstance(usage, dict):
                    safe_usage = {
                        key: usage[key] for key in ("input_tokens", "output_tokens", "total_tokens")
                        if isinstance(usage.get(key), int)
                    }
                    self.usage = safe_usage or None
                had_event_calls = self._seen_items
                for item in response.get("output", []):
                    if isinstance(item, dict):
                        call_id = item.get("call_id") if item.get("type") == "function_call" else None
                        if isinstance(call_id, str):
                            if call_id in self._seen_call_ids:
                                continue
                            self._seen_call_ids.add(call_id)
                        elif item.get("type") == "function_call" and had_event_calls:
                            continue
                        self._append_item(item)

    def _append_item(self, item: dict[str, Any]) -> None:
        record = {"type": item.get("type")}
        if item.get("type") == "function_call":
            record["name"] = item.get("name")
            record["call_id_present"] = isinstance(item.get("call_id"), str)
            self._seen_items = True
        self.items.append(record)


def request_metadata(body: bytes) -> dict[str, Any]:
    try:
        request = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"json_request": False}
    if not isinstance(request, dict):
        return {"json_request": False}
    input_items = request.get("input", [])
    top_level_tools = request.get("tools", [])
    additional_tools: list[dict[str, Any]] = []
    prior_calls = []
    tool_results = 0
    input_item_types: list[str] = []
    if isinstance(input_items, list):
        for item in input_items:
            if not isinstance(item, dict):
                continue
            if isinstance(item.get("type"), str):
                input_item_types.append(item["type"])
            if item.get("type") == "additional_tools" and isinstance(item.get("tools"), list):
                additional_tools.extend(tool for tool in item["tools"] if isinstance(tool, dict))
            if item.get("type") == "function_call":
                prior_calls.append(item.get("name"))
            elif item.get("type") == "function_call_output":
                tool_results += 1
    top_names, top_shapes = tool_names(top_level_tools)
    additional_names, additional_shapes = tool_names(additional_tools)
    names = sorted(set(top_names) | set(additional_names))
    reasoning = request.get("reasoning")
    effort = reasoning.get("effort") if isinstance(reasoning, dict) else None
    if effort not in {"none", "minimal", "low", "medium", "high", "xhigh"}:
        effort = "other" if effort is not None else None
    return {
        "json_request": True,
        "tool_names": names,
        "top_level_tool_count": len(top_level_tools) if isinstance(top_level_tools, list) else 0,
        "additional_tool_count": len(additional_tools),
        "tools_field_present": "tools" in request,
        "additional_tools_present": bool(additional_tools),
        "tool_shapes": top_shapes + additional_shapes,
        "tool_schemas": (
            tool_schema_metadata(top_level_tools, source="top_level")
            + tool_schema_metadata(additional_tools, source="additional_tools")
        ),
        "read_file_advertised": "read_file" in names,
        "tool_choice_type": (request.get("tool_choice") or {}).get("type")
            if isinstance(request.get("tool_choice"), dict) else None,
        "reasoning_effort": effort,
        "think_field_present": "think" in request,
        "prior_function_call_names": prior_calls,
        "tool_result_count": tool_results,
        "input_item_types": input_item_types,
        "input_item_count": len(input_items) if isinstance(input_items, list) else None,
        "previous_response_id_present": bool(request.get("previous_response_id")),
    }


class TraceHandler(BaseHTTPRequestHandler):
    server: "TraceServer"

    def log_message(self, *_args: Any) -> None:
        return

    def _forward(self) -> None:
        with self.server.capture_lock:
            request_sequence = self.server.next_request_sequence
            self.server.next_request_sequence += 1
        request_started_ns = time.monotonic_ns()
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        target = self.server.upstream
        path = target.path.rstrip("/") + urlsplit(self.path).path
        connection_type = http.client.HTTPSConnection if target.scheme == "https" else http.client.HTTPConnection
        connection = connection_type(target.hostname, target.port, timeout=600)
        response_started = False
        response = None
        summary: dict[str, Any] | None = None
        monitor_stop = threading.Event()
        client_disconnected = threading.Event()
        monitor: threading.Thread | None = None
        headers = {
            key: value for key, value in self.headers.items()
            if key.lower() not in {"host", "connection", "transfer-encoding", "content-length"}
        }
        if body:
            headers["Content-Length"] = str(len(body))
        try:
            connection.request(self.command, path, body=body or None, headers=headers)
            response = connection.getresponse()
            response_headers = {
                key: value for key, value in response.getheaders()
                if key.lower() not in {"connection", "transfer-encoding", "content-length", "keep-alive"}
            }
            self.send_response(response.status, response.reason)
            for key, value in response_headers.items():
                self.send_header(key, value)
            self.send_header("Connection", "close")
            self.end_headers()
            response_started = True

            metadata = request_metadata(body) if self.command == "POST" else {"json_request": False}
            summary = {
                "request_sequence": request_sequence,
                "request_started_monotonic_ns": request_started_ns,
                "method": self.command,
                "path": self.path,
                "http_status": response.status,
                "request": metadata,
            }
            def watch_client() -> None:
                # The proxy may be blocked reading a slow upstream SSE stream
                # after Codex exits. Detect EOF independently and cancel that
                # upstream read; merely noticing a later BrokenPipe is too late.
                while not monitor_stop.is_set():
                    try:
                        readable, _, _ = select.select([self.connection], [], [], 0.05)
                        if readable and self.connection.recv(1, socket.MSG_PEEK) == b"":
                            client_disconnected.set()
                            response.close()
                            connection.close()
                            return
                    except (OSError, ValueError):
                        client_disconnected.set()
                        response.close()
                        connection.close()
                        return

            monitor = threading.Thread(target=watch_client, daemon=True)
            monitor.start()
            sse = SSEMetadata()
            is_sse = "text/event-stream" in response.getheader("Content-Type", "")
            while True:
                read_chunk = getattr(response, "read1", response.read)
                chunk = read_chunk(16_384)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
                if is_sse:
                    sse.feed(chunk)
            if is_sse:
                summary["response_items"] = sse.items
                summary["terminal_status"] = sse.terminal_status
                summary["usage"] = sse.usage
                summary["response_finished_monotonic_ns"] = time.monotonic_ns()
        except Exception as exc:
            if summary is not None:
                summary["error_type"] = type(exc).__name__
            if not response_started and not self.wfile.closed:
                try:
                    self.send_error(502, "upstream request failed")
                except (BrokenPipeError, ConnectionResetError):
                    pass
        finally:
            monitor_stop.set()
            if monitor is not None:
                monitor.join(timeout=0.2)
            if summary is not None:
                summary["client_disconnected"] = client_disconnected.is_set()
                summary.setdefault("response_finished_monotonic_ns", time.monotonic_ns())
                with self.server.capture_lock:
                    self.server.capture["requests"].append(summary)
                    self.server.capture_path.write_text(json.dumps(self.server.capture, indent=2) + "\n")
            connection.close()

    do_GET = _forward
    do_POST = _forward
    do_PUT = _forward


class TraceServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port: int, upstream: str, capture_path: str) -> None:
        parsed = urlsplit(upstream)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("upstream must be an http(s) URL without embedded credentials")
        super().__init__(("127.0.0.1", port), TraceHandler)
        self.upstream = parsed
        self.capture_path = Path(capture_path)
        self.capture: dict[str, Any] = {"requests": []}
        self.capture_lock = threading.Lock()
        self.next_request_sequence = 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--upstream", default=os.environ.get("HERD_TRACE_UPSTREAM"))
    parser.add_argument("--capture", default="/tmp/codex-herd-trace-summary.json")
    args = parser.parse_args()
    if not args.upstream:
        parser.error("set HERD_TRACE_UPSTREAM or pass --upstream")
    server = TraceServer(args.port, args.upstream, args.capture)
    print(f"Loopback Codex-to-Herd trace proxy: http://127.0.0.1:{server.server_port}", flush=True)
    print(f"Sanitized metadata only: {server.capture_path}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
