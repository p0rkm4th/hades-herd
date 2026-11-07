#!/usr/bin/env python3
"""Run Codex through Herd 0.12.3 with a mock Ollama backend.

This checks the real Responses route and tool-result continuation without
loading a model or contacting a production Herd/Ollama service. See the
benchmark README for prerequisites and invocation.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from pathlib import Path
from typing import Any

MODEL = "mock-codex:latest"
MARKER = "tool-roundtrip-ok"
TOOL_CALL_ID = "codex-herd-roundtrip-1"


def _mock_ollama_handler(calls: list[dict[str, Any]]):
    import httpx

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/show":
            return httpx.Response(
                200,
                json={"model_info": {"mock.context_length": 4096}, "parameters": ""},
            )
        if request.url.path != "/api/chat":
            return httpx.Response(404, json={"error": "unexpected mock path"})

        body = json.loads(request.content)
        messages = body.get("messages", [])
        assistant_calls = []
        tool_results = []
        for message in messages:
            for call in message.get("tool_calls", []):
                assistant_calls.append(
                    {
                        "id": call.get("id"),
                        "name": call.get("function", {}).get("name"),
                    }
                )
            if message.get("role") == "tool":
                tool_results.append(
                    {
                        "call_id": message.get("tool_call_id"),
                        "marker_present": MARKER in str(message.get("content", "")),
                    }
                )
        tool_names = sorted(
            tool.get("function", {}).get("name", "")
            for tool in body.get("tools", [])
            if isinstance(tool, dict)
        )
        calls.append(
            {
                "tool_names": tool_names,
                "assistant_calls": assistant_calls,
                "tool_results": tool_results,
            }
        )

        if len(calls) == 1:
            chunks = [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": TOOL_CALL_ID,
                                "function": {
                                    "name": "exec_command",
                                    "arguments": {"cmd": f"printf {MARKER}"},
                                },
                            }
                        ]
                    }
                },
                {
                    "done": True,
                    "done_reason": "stop",
                    "prompt_eval_count": 10,
                    "eval_count": 2,
                },
            ]
        else:
            chunks = [
                {"message": {"content": "Tool round trip complete."}},
                {
                    "done": True,
                    "done_reason": "stop",
                    "prompt_eval_count": 18,
                    "eval_count": 6,
                },
            ]
        ndjson = "".join(
            json.dumps(chunk, separators=(",", ":")) + "\n" for chunk in chunks
        )
        return httpx.Response(
            200,
            content=ndjson,
            headers={"content-type": "application/x-ndjson"},
        )

    return handle


def run(herd_source: Path, client_source: Path, artifacts: Path, timeout: int) -> None:
    herd_source = herd_source.resolve()
    client_source = client_source.resolve()
    if (
        tomllib.loads((herd_source / "pyproject.toml").read_text())["project"][
            "version"
        ]
        != "0.12.3"
    ):
        raise SystemExit("This fixture is pinned to Ollama Herd 0.12.3.")
    if not (herd_source / "tests/test_server/test_routes.py").is_file():
        raise SystemExit("Herd source must include its tests/test_server helpers.")
    if not shutil.which("codex"):
        raise SystemExit("Codex CLI is required on PATH.")

    # Keep deployment-specific router settings from influencing the synthetic app.
    for key in list(os.environ):
        if key.startswith("FLEET_"):
            os.environ.pop(key, None)

    sys.path.insert(0, str(herd_source))
    sys.path.insert(0, str(herd_source / "tests"))
    import httpx
    import uvicorn
    from fleet_manager.models.node import ModelTagMeta
    from tests.conftest import make_heartbeat
    from tests.test_server.test_routes import create_test_app

    artifacts = artifacts.resolve()
    artifacts.mkdir(parents=True, exist_ok=False)
    temp = Path(tempfile.mkdtemp(prefix="herd-route-codex-"))
    ollama_calls: list[dict[str, Any]] = []
    app = create_test_app(tmp_path=temp)
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    server = uvicorn.Server(
        uvicorn.Config(
            app, host="127.0.0.1", port=port, log_level="error", access_log=False
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    codex: subprocess.Popen[str] | None = None
    try:
        thread.start()
        deadline = time.monotonic() + 10
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.05)
        if not server.started:
            raise RuntimeError("Isolated Herd test app did not start.")

        base_url = f"http://127.0.0.1:{port}"
        heartbeat = make_heartbeat(
            node_id="mock-node",
            loaded_models=[(MODEL, 0.01, 4096)],
            available_models=[MODEL],
            lan_ip="127.0.0.1",
            ollama_host="http://mock-ollama:11434",
        )
        heartbeat.ollama.models_available_meta = {
            MODEL: ModelTagMeta(capabilities=["completion", "tools"])
        }
        response = httpx.post(
            f"{base_url}/heartbeat", json=heartbeat.model_dump(), timeout=5
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Synthetic heartbeat rejected: HTTP {response.status_code}."
            )

        proxy = app.state.streaming_proxy
        node = app.state.registry.get_node("mock-node")
        proxy._clients["mock-node"] = httpx.AsyncClient(
            base_url=node.ollama_base_url,
            transport=httpx.MockTransport(_mock_ollama_handler(ollama_calls)),
        )
        proxy._client_urls["mock-node"] = node.ollama_base_url

        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(temp),
            "CODEX_HOME": str(temp / "codex"),
            "XDG_CONFIG_HOME": str(temp / ".config"),
            "XDG_CACHE_HOME": str(temp / ".cache"),
            "CODEX_HERD_URL": base_url,
        }
        codex_version = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
        codex = subprocess.Popen(
            [
                sys.executable,
                str(client_source / "codex_herd.py"),
                MODEL,
                "exec",
                "--ephemeral",
                "--sandbox",
                "read-only",
                "--skip-git-repo-check",
                "--json",
                "Use exec_command once; then confirm it completed.",
            ],
            cwd=temp,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            output, error_output = codex.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(codex.pid, signal.SIGKILL)
            output, error_output = codex.communicate()
            (artifacts / "codex.stdout.jsonl").write_text(output)
            (artifacts / "codex.stderr.log").write_text(error_output)
            (artifacts / "mock-ollama-summary.json").write_text(
                json.dumps(ollama_calls, indent=2) + "\n"
            )
            (artifacts / "exit-status.txt").write_text("timeout\n")
            raise RuntimeError(
                f"Codex exceeded the {timeout}s process timeout."
            ) from None

        (artifacts / "codex.stdout.jsonl").write_text(output)
        (artifacts / "codex.stderr.log").write_text(error_output)
        (artifacts / "mock-ollama-summary.json").write_text(
            json.dumps(ollama_calls, indent=2) + "\n"
        )
        (artifacts / "exit-status.txt").write_text(f"{codex.returncode}\n")

        passed = (
            codex.returncode == 0
            and '"type":"turn.completed"' in output
            and len(ollama_calls) == 2
            and "exec_command" in ollama_calls[0]["tool_names"]
            and ollama_calls[1]["assistant_calls"]
            == [{"id": TOOL_CALL_ID, "name": "exec_command"}]
            and ollama_calls[1]["tool_results"]
            == [{"call_id": TOOL_CALL_ID, "marker_present": True}]
        )
        print(
            f"Codex exit 0 and turn.completed: {'PASS' if codex.returncode == 0 and 'turn.completed' in output else 'FAIL'}"
        )
        print(f"Herd calls to mock Ollama: {len(ollama_calls)} (expected 2)")
        print(
            f"Advertised exec_command reached Ollama: {'PASS' if ollama_calls and 'exec_command' in ollama_calls[0]['tool_names'] else 'FAIL'}"
        )
        print(
            f"Matching tool call/result ID and output returned: {'PASS' if len(ollama_calls) == 2 and ollama_calls[1]['assistant_calls'] == [{'id': TOOL_CALL_ID, 'name': 'exec_command'}] and ollama_calls[1]['tool_results'] == [{'call_id': TOOL_CALL_ID, 'marker_present': True}] else 'FAIL'}"
        )
        print(f"Codex version: {codex_version}")
        print(f"Run artifacts: {artifacts}")
        if not passed:
            raise SystemExit(1)
        print("ISOLATED_HERD_ROUTE_ROUNDTRIP=PASS")
    finally:
        if codex is not None and codex.poll() is None:
            os.killpg(codex.pid, signal.SIGKILL)
            codex.wait()
        server.should_exit = True
        thread.join(timeout=8)
        if thread.is_alive():
            server.force_exit = True
            thread.join(timeout=2)
        shutil.rmtree(temp)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--herd-source", type=Path, required=True)
    parser.add_argument(
        "--client-source", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error("--timeout must be positive")
    run(args.herd_source, args.client_source, args.artifacts, args.timeout)


if __name__ == "__main__":
    main()
