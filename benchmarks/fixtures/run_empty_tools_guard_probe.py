#!/usr/bin/env python3
"""Run a loopback Codex protocol control for an adapter's empty-tool guard.

This is a contract probe, not a Herd server or model benchmark. It compares a
buggy adapter response (forwarding an unoffered exec_command) with the proposed
guard response (visible assistant text, no function_call).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Server(ThreadingHTTPServer):
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args: object) -> None:
        pass

    def do_POST(self) -> None:
        request = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        if self.path != "/v1/responses":
            self.send_error(404)
            return
        self.server.request_summaries.append({
            "codex_tool_count": len(request.get("tools") or []),
            # The empty backend offer is injected by this control fixture.
            "simulated_backend_tool_count": 0,
        })
        number = len(self.server.request_summaries)
        now = int(time.time())
        response_id = f"resp_{number}"

        def event(name: str, sequence: int, **fields: object) -> dict:
            return {"type": name, "sequence_number": sequence, **fields}

        if number == 1 and self.server.mode == "stock":
            arguments = '{"cmd":"touch executed.txt"}'
            item = {
                "id": "fc_1", "type": "function_call", "status": "completed",
                "call_id": "call_1", "name": "exec_command", "arguments": arguments,
            }
            events = [
                event("response.created", 0, response={
                    "id": response_id, "object": "response", "status": "in_progress",
                    "created_at": now, "model": "mock-codex", "output": [],
                }),
                event("response.output_item.added", 1, output_index=0,
                      item={**item, "status": "in_progress", "arguments": ""}),
                event("response.function_call_arguments.delta", 2, output_index=0,
                      item_id="fc_1", delta=arguments),
                event("response.function_call_arguments.done", 3, output_index=0,
                      item_id="fc_1", arguments=arguments),
                event("response.output_item.done", 4, output_index=0, item=item),
            ]
            output = [item]
        else:
            text = (
                "No tool was run because no tool was offered."
                if number == 1 and self.server.mode == "guard"
                else "Diagnostic complete."
            )
            item = {
                "id": f"msg_{number}", "type": "message", "status": "completed",
                "role": "assistant",
                "content": [{"type": "output_text", "text": text, "annotations": []}],
            }
            events = [
                event("response.created", 0, response={
                    "id": response_id, "object": "response", "status": "in_progress",
                    "created_at": now, "model": "mock-codex", "output": [],
                }),
                event("response.output_item.added", 1, output_index=0,
                      item={**item, "status": "in_progress", "content": []}),
                event("response.content_part.added", 2, output_index=0,
                      item_id=item["id"], content_index=0,
                      part={"type": "output_text", "text": ""}),
                event("response.output_text.delta", 3, output_index=0,
                      item_id=item["id"], content_index=0, delta=text),
                event("response.output_text.done", 4, output_index=0,
                      item_id=item["id"], content_index=0, text=text),
                event("response.output_item.done", 5, output_index=0, item=item),
            ]
            output = [item]

        response = {
            "id": response_id, "object": "response", "status": "completed",
            "created_at": now, "model": "mock-codex", "output": output, "error": None,
        }
        events.append(event("response.completed", len(events), response=response))
        body = "".join(
            f"event: {item['type']}\ndata: {json.dumps(item, separators=(',', ':'))}\n\n"
            for item in events
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()


def run_mode(codex: str, mode: str, timeout: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="codex-empty-tools-guard-") as temporary:
        root = pathlib.Path(temporary)
        repo, codex_home = root / "repo", root / "codex-home"
        repo.mkdir()
        codex_home.mkdir()
        (repo / "README.md").write_text("Disposable local protocol probe.\n")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)

        server = Server(("127.0.0.1", 0), Handler)
        server.mode = mode
        server.request_summaries = []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}/v1"
        (codex_home / "config.toml").write_text(
            'model = "mock-codex"\nmodel_provider = "herd"\n\n'
            "[model_providers.herd]\nname = \"loopback mock\"\n"
            f'base_url = "{url}"\nwire_api = "responses"\n'
            "requires_openai_auth = false\nsupports_websockets = false\n"
            "request_max_retries = 0\nstream_max_retries = 0\n"
        )
        environment = os.environ.copy()
        environment["CODEX_HOME"] = str(codex_home)
        environment.pop("OPENAI_API_KEY", None)
        environment.pop("OPENAI_BASE_URL", None)
        command = [
            codex, "exec", "--ephemeral", "--json", "-C", str(repo),
            "--sandbox", "workspace-write", "-c", 'approval_policy="never"',
            "-c", 'model="mock-codex"', "-c", 'model_provider="herd"',
            "-c", f'model_providers.herd.base_url="{url}"',
            "-c", "model_providers.herd.requires_openai_auth=false",
            "-c", "model_providers.herd.supports_websockets=false",
            "Create executed.txt by running touch executed.txt, then stop.",
        ]
        try:
            result = subprocess.run(
                command, cwd=repo, env=environment, stdin=subprocess.DEVNULL,
                capture_output=True, timeout=timeout, text=True,
            )
            return {
                "mode": mode,
                "exit_code": result.returncode,
                "marker_created": (repo / "executed.txt").exists(),
                "responses_requests": len(server.request_summaries),
                "first_request": server.request_summaries[0]
                    if server.request_summaries else None,
            }
        except subprocess.TimeoutExpired:
            return {
                "mode": mode, "timeout": True,
                "marker_created": (repo / "executed.txt").exists(),
                "responses_requests": len(server.request_summaries),
                "first_request": server.request_summaries[0]
                    if server.request_summaries else None,
            }
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", default="codex", help="Codex CLI executable")
    parser.add_argument("--timeout", type=int, default=30, help="per-run timeout seconds")
    args = parser.parse_args()
    executable = shutil.which(args.codex)
    if executable is None:
        parser.error(f"Codex executable not found: {args.codex}")
    results = [run_mode(executable, mode, args.timeout) for mode in ("stock", "guard")]
    print(json.dumps({"probe": "synthetic_empty_backend_tool_set", "results": results}, indent=2))
    passed = (
        results[0].get("exit_code") == 0 and results[0].get("marker_created") is True
        and results[1].get("exit_code") == 0 and results[1].get("marker_created") is False
        and all(item.get("responses_requests", 0) > 0 for item in results)
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
