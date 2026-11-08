#!/usr/bin/env python3
"""Run a real Codex tool cycle through pinned Herd with a fake Ollama backend.

Run this from a disposable checkout of Herd v0.12.3 with its dev dependencies
installed and Codex CLI available. Herd binds to loopback, mDNS is not started,
and the backend is an in-process MockTransport. The command and response are
synthetic. Only request/tool counts and Codex event types are printed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time

import httpx
import uvicorn

from tests.conftest import make_heartbeat
from tests.test_server.test_routes import create_test_app
from fleet_manager.models.node import ModelTagMeta

REPO = Path(__file__).resolve().parents[2]
MODEL = "mock-codex:latest"
TASK = "Run the available shell tool once, then summarize."


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="herd-codex-continuity-") as temp:
        root = Path(temp)
        app = create_test_app(tmp_path=root / "herd-data")
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        sock.listen()
        port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(
            app, log_level="critical", access_log=False, lifespan="on",
        ))
        server_thread = threading.Thread(
            target=server.run, kwargs={"sockets": [sock]}, daemon=True,
        )
        server_thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and time.monotonic() < deadline:
                time.sleep(0.01)
            if not server.started:
                raise RuntimeError("disposable Herd test server did not start")

            base = f"http://127.0.0.1:{port}"
            heartbeat = make_heartbeat(
                node_id="codex-probe",
                loaded_models=[(MODEL, 0.001, 4096)],
                available_models=[MODEL],
                lan_ip="127.0.0.1",
                ollama_host="http://127.0.0.1:11434",
            )
            heartbeat.ollama.models_available_meta = {
                MODEL: ModelTagMeta(
                    digest="mock-digest", family="mock", capabilities=["tools"],
                ),
            }
            registered = httpx.post(
                base + "/heartbeat", json=heartbeat.model_dump(), timeout=5,
            )
            registered.raise_for_status()

            backend_requests: list[dict] = []

            def fake_ollama(request: httpx.Request) -> httpx.Response:
                if request.url.path != "/api/chat":
                    return httpx.Response(404)
                body = json.loads(request.content)
                messages = body.get("messages", [])
                backend_requests.append({
                    "tool_offer_count": len(body.get("tools") or []),
                    "prior_tool_call_count": sum(
                        len(message.get("tool_calls") or [])
                        for message in messages
                        if isinstance(message, dict) and message.get("role") == "assistant"
                    ),
                    "tool_result_count": sum(
                        1 for message in messages
                        if isinstance(message, dict) and message.get("role") == "tool"
                    ),
                })
                if len(backend_requests) == 1:
                    response_chunk = {
                        "model": MODEL,
                        "message": {
                            "role": "assistant",
                            "tool_calls": [{
                                "id": "mock-call-1",
                                "function": {
                                    "name": "exec_command",
                                    "arguments": {"cmd": "printf HADES_TOOL_EXECUTED"},
                                },
                            }],
                        },
                        "done": True,
                        "done_reason": "stop",
                    }
                else:
                    response_chunk = {
                        "model": MODEL,
                        "message": {"role": "assistant", "content": "Diagnostic complete."},
                        "done": True,
                        "done_reason": "stop",
                    }
                return httpx.Response(
                    200,
                    content=(json.dumps(response_chunk) + "\n").encode(),
                    headers={"content-type": "application/x-ndjson"},
                )

            proxy = app.state.streaming_proxy
            node_url = app.state.registry.get_node("codex-probe").ollama_base_url
            proxy._clients["codex-probe"] = httpx.AsyncClient(
                base_url=node_url, transport=httpx.MockTransport(fake_ollama),
            )
            proxy._client_urls["codex-probe"] = node_url

            stdout_path = root / "codex.stdout.jsonl"
            stderr_path = root / "codex.stderr"
            timeline_path = root / "codex.events.jsonl"
            summary_path = root / "codex.summary.json"
            env = os.environ.copy()
            for key in (
                "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_ORG_ID",
                "OPENAI_PROJECT", "CODEX_HOME",
            ):
                env.pop(key, None)
            env.update({"HOME": str(root / "home"), "CODEX_HERD_URL": base})
            command = [
                sys.executable,
                str(REPO / "benchmarks/fixtures/capture_codex_jsonl.py"),
                "--timeout", "45",
                "--stdout", str(stdout_path),
                "--stderr", str(stderr_path),
                "--timeline", str(timeline_path),
                "--summary", str(summary_path),
                "--", sys.executable, str(REPO / "codex_herd.py"), MODEL,
                "exec", "--ephemeral", "--sandbox", "read-only",
                "--skip-git-repo-check", "--json", TASK,
            ]
            capture = subprocess.run(command, cwd=root, env=env, check=False)
            summary = json.loads(summary_path.read_text())
            raw_stdout = stdout_path.read_text()
            raw_stderr = stderr_path.read_text()
            event_types = [
                json.loads(line).get("type")
                for line in timeline_path.read_text().splitlines()
                if line.strip()
            ]
            passed = (
                capture.returncode == 0
                and not summary["timed_out"]
                and len(backend_requests) == 2
                and backend_requests[0]["tool_offer_count"] > 0
                and backend_requests[1]["prior_tool_call_count"] == 1
                and backend_requests[1]["tool_result_count"] == 1
                and "HADES_TOOL_EXECUTED" in raw_stdout
                and "Diagnostic complete." in raw_stdout
                and "turn.completed" in event_types
            )
            print(json.dumps({
                "passed": passed,
                "codex_exit_status": summary["command_exit_status"],
                "timed_out": summary["timed_out"],
                "backend_request_count": len(backend_requests),
                "backend_request_metadata": backend_requests,
                "codex_event_types": event_types,
                "codex_stderr_nonempty": bool(raw_stderr.strip()),
                "raw_output_published": False,
            }, indent=2))
            return 0 if passed else 1
        finally:
            server.should_exit = True
            server_thread.join(timeout=10)
            sock.close()


if __name__ == "__main__":
    raise SystemExit(main())
