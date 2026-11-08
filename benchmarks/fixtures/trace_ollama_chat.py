#!/usr/bin/env python3
"""Loopback-only Ollama proxy that records content-free /api/chat metadata."""

from __future__ import annotations

import argparse
import http.client
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

_HOP_HEADERS = {
    "connection",
    "content-length",
    "date",
    "host",
    "keep-alive",
    "proxy-connection",
    "server",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def _tool_names(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    names = []
    for tool in value:
        if not isinstance(tool, dict):
            continue
        function = tool.get("function")
        name = function.get("name") if isinstance(function, dict) else tool.get("name")
        if isinstance(name, str):
            names.append(name)
    return names


def request_metadata(path: str, body: bytes) -> dict[str, Any]:
    """Return only model/tool-shape metadata; never retain prompts or schemas."""
    endpoint = urlsplit(path).path
    if endpoint != "/api/chat":
        return {"endpoint": endpoint}
    try:
        request = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"endpoint": endpoint, "json_request": False}
    if not isinstance(request, dict):
        return {"endpoint": endpoint, "json_request": False}
    tools = request.get("tools")
    return {
        "endpoint": endpoint,
        "json_request": True,
        "model": request.get("model") if isinstance(request.get("model"), str) else None,
        "stream": request.get("stream") if isinstance(request.get("stream"), bool) else None,
        "tools_field_present": "tools" in request,
        "tool_count": len(tools) if isinstance(tools, list) else None,
        "tool_names": _tool_names(tools),
        "message_count": (
            len(request["messages"]) if isinstance(request.get("messages"), list) else None
        ),
    }


def response_metadata(line_or_body: bytes, streaming: bool) -> dict[str, Any]:
    """Extract content-free response shape, tool names, and token counters."""
    try:
        value = json.loads(line_or_body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    if not isinstance(value, dict):
        return {}
    message = value.get("message") if isinstance(value.get("message"), dict) else {}
    calls = message.get("tool_calls")
    if calls is None and not streaming:
        calls = value.get("tool_calls")
    names = _tool_names(calls)
    result: dict[str, Any] = {}
    for key in ("content", "thinking"):
        value_for_key = message.get(key)
        result[f"{key}_field_present"] = key in message
        if isinstance(value_for_key, str):
            result[f"{key}_chars"] = len(value_for_key)
    if names:
        result["tool_call_names"] = names
    if value.get("done") is True:
        result["done"] = True
    if isinstance(value.get("done_reason"), str):
        result["done_reason"] = value["done_reason"]
    for key in ("prompt_eval_count", "eval_count"):
        if isinstance(value.get(key), int):
            result[key] = value[key]
    return result


class OllamaTraceServer(ThreadingHTTPServer):
    """Forward to one Ollama origin and write sanitized request records."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        address: tuple[str, int],
        upstream: str,
        capture_path: str,
        timeout: float = 300,
    ):
        if address[0] != "127.0.0.1":
            raise ValueError("the metadata proxy must bind to 127.0.0.1")
        parsed = urlsplit(upstream)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            raise ValueError("upstream must be an http(s) origin without credentials")
        if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError(
                "upstream must be loopback; use an SSH tunnel for a remote Ollama node"
            )
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError("upstream must be an origin without path, query, or fragment")
        self.upstream_scheme = parsed.scheme
        self.upstream_host = parsed.hostname
        self.upstream_port = parsed.port or (443 if parsed.scheme == "https" else 80)
        self.upstream_authority = parsed.netloc
        self.timeout = timeout
        self.capture_path = Path(capture_path)
        self.capture_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.capture_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        self.capture_path.chmod(0o600)
        self._capture_lock = threading.Lock()
        self._sequence = 0
        super().__init__(address, OllamaTraceHandler)

    def record(self, record: dict[str, Any]) -> None:
        with self._capture_lock:
            self._sequence += 1
            record["sequence"] = self._sequence
            with self.capture_path.open("a", encoding="utf-8") as capture:
                capture.write(json.dumps(record, sort_keys=True) + "\n")
                capture.flush()


class OllamaTraceHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args) -> None:
        pass

    def do_GET(self) -> None:
        self._proxy()

    def do_POST(self) -> None:
        self._proxy()

    def do_DELETE(self) -> None:
        self._proxy()

    def do_HEAD(self) -> None:
        self._proxy()

    def _proxy(self) -> None:
        server: OllamaTraceServer = self.server  # type: ignore[assignment]
        started_ns = time.monotonic_ns()
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400)
            return
        if length < 0 or length > 64 * 1024 * 1024:
            self.send_error(413)
            return
        body = self.rfile.read(length) if length else b""
        request_meta = request_metadata(self.path, body)
        record: dict[str, Any] = {
            "started_monotonic_ns": started_ns,
            "method": self.command,
            "request": request_meta,
        }
        endpoint = request_meta.get("endpoint")
        streaming = endpoint == "/api/chat" and request_meta.get("stream") is True
        conn_type = (
            http.client.HTTPSConnection
            if server.upstream_scheme == "https"
            else http.client.HTTPConnection
        )
        conn = conn_type(server.upstream_host, server.upstream_port, timeout=server.timeout)
        headers_sent = False
        try:
            headers = {
                key: value for key, value in self.headers.items()
                if key.lower() not in _HOP_HEADERS
            }
            headers["Host"] = server.upstream_authority
            headers["Accept-Encoding"] = "identity"
            if body:
                headers["Content-Length"] = str(len(body))
            conn.request(self.command, self.path, body=body or None, headers=headers)
            response = conn.getresponse()
            record["status_code"] = response.status
            self.send_response(response.status, response.reason)
            for key, value in response.getheaders():
                if key.lower() not in _HOP_HEADERS:
                    self.send_header(key, value)
            no_body = self.command == "HEAD" or response.status in {204, 304}
            if not no_body:
                self.send_header("Transfer-Encoding", "chunked")
            self.send_header("Connection", "close")
            self.end_headers()
            headers_sent = True
            self.close_connection = True

            if no_body:
                return

            calls: dict[int, str] = {}
            aggregate: dict[str, Any] = {}
            buffer = bytearray()
            while True:
                chunk = response.readline() if streaming else response.read(8192)
                if not chunk:
                    break
                if endpoint == "/api/chat":
                    if streaming:
                        buffer.extend(chunk)
                        while b"\n" in buffer:
                            line, _, rest = buffer.partition(b"\n")
                            buffer[:] = rest
                            _merge_response_metadata(aggregate, calls, line + b"\n", True)
                    else:
                        buffer.extend(chunk)
                self.wfile.write(f"{len(chunk):X}\r\n".encode("ascii") + chunk + b"\r\n")
                self.wfile.flush()
            if endpoint == "/api/chat":
                if buffer:
                    _merge_response_metadata(aggregate, calls, bytes(buffer), streaming)
                record["response"] = aggregate
                if calls:
                    record["response"]["tool_call_count"] = len(calls)
                    record["response"]["tool_call_names"] = [
                        calls[index] for index in sorted(calls)
                    ]
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except (OSError, http.client.HTTPException, TimeoutError) as exc:
            record["error_type"] = type(exc).__name__
            if not headers_sent and not self.wfile.closed:
                try:
                    error_body = b'{"error":"upstream unavailable"}'
                    self.send_response(502)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(error_body)))
                    self.send_header("Connection", "close")
                    self.end_headers()
                    self.wfile.write(error_body)
                    self.close_connection = True
                except OSError:
                    pass
        finally:
            conn.close()
            record["finished_monotonic_ns"] = time.monotonic_ns()
            server.record(record)


def _merge_response_metadata(
    aggregate: dict[str, Any], calls: dict[int, str], body: bytes, streaming: bool
) -> None:
    metadata = response_metadata(body, streaming)
    for key, value in metadata.items():
        if key == "tool_call_names":
            continue
        if key.endswith("_chars") and isinstance(value, int):
            aggregate[key] = aggregate.get(key, 0) + value
        elif key.endswith("_field_present"):
            aggregate[key] = aggregate.get(key, False) or value
        else:
            aggregate[key] = value
    names = metadata.get("tool_call_names", [])
    if names:
        # Ollama streams calls by list position; replace repeated partial
        # sightings at the same position while preserving same-name calls.
        for index, name in enumerate(names):
            calls[index] = name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", required=True, help="Ollama http(s) origin")
    parser.add_argument("--capture", required=True, help="new mode-0600 JSONL metadata path")
    parser.add_argument(
        "--port", type=int, default=0,
        help="loopback port (0 chooses an ephemeral port)",
    )
    parser.add_argument(
        "--timeout", type=float, default=300,
        help="upstream inactivity timeout seconds",
    )
    args = parser.parse_args()
    if not 0 <= args.port <= 65535 or args.timeout <= 0:
        parser.error("port must be 0–65535 and timeout must be positive")
    try:
        server = OllamaTraceServer(
            ("127.0.0.1", args.port), args.upstream, args.capture, args.timeout
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Loopback Ollama metadata proxy: http://127.0.0.1:{server.server_port}", flush=True)
    print(f"Content-free capture: {server.capture_path}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
