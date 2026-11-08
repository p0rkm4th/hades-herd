"""Run against a disposable checkout of Herd v0.12.3 with fake Ollama.

This test exercises Herd's Responses route, scorer, queue, streaming proxy, and
translator. It opens no socket and never starts Herd's mDNS advertiser.
"""

from __future__ import annotations

import json
import os

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_heartbeat
from tests.test_server.test_routes import create_test_app

MODEL = "qwen3-coder:30b"
EXPECTED = os.environ.get("HERD_EMPTY_TOOLS_EXPECTED", "stock")


@pytest.mark.parametrize("stream", [False, True])
def test_empty_tool_call_route(tmp_path, stream):
    observed_backend_requests = []

    def fake_ollama(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        observed_backend_requests.append({
            "path": request.url.path,
            "tools_present": "tools" in body,
            "tool_count": len(body.get("tools") or []),
        })
        if request.url.path != "/api/chat":
            return httpx.Response(404)
        chunks = [
            {
                "model": MODEL,
                "message": {
                    "role": "assistant",
                    "tool_calls": [{
                        "id": "synthetic",
                        "function": {"name": "exec_command", "arguments": {"cmd": "true"}},
                    }],
                },
                "done": False,
            },
            {
                "model": MODEL,
                "message": {"role": "assistant", "content": ""},
                "done": True,
                "done_reason": "stop",
                "prompt_eval_count": 1,
                "eval_count": 1,
            },
        ]
        content = "\n".join(json.dumps(chunk) for chunk in chunks) + "\n"
        return httpx.Response(
            200, content=content.encode(), headers={"content-type": "application/x-ndjson"}
        )

    app = create_test_app(tmp_path=tmp_path)
    with TestClient(app) as client:
        heartbeat = make_heartbeat(
            node_id="probe",
            loaded_models=[(MODEL, 1.0)],
            available_models=[MODEL],
            ollama_host="http://127.0.0.1:11434",
        )
        registered = client.post("/heartbeat", json=heartbeat.model_dump())
        assert registered.status_code == 200, registered.text

        proxy = app.state.streaming_proxy
        node_url = app.state.registry.get_node("probe").ollama_base_url
        proxy._clients["probe"] = httpx.AsyncClient(
            base_url=node_url, transport=httpx.MockTransport(fake_ollama)
        )
        proxy._client_urls["probe"] = node_url

        response = client.post(
            "/v1/responses",
            json={"model": MODEL, "input": "continue", "tools": [], "stream": stream},
        )

    assert response.status_code == 200, response.text
    assert observed_backend_requests == [{
        "path": "/api/chat", "tools_present": False, "tool_count": 0,
    }]

    if stream:
        items = []
        response_text = response.text
        for line in response_text.splitlines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                if event.get("type") == "response.output_item.done":
                    items.append(event.get("item", {}).get("type"))
    else:
        body = response.json()
        items = [item.get("type") for item in body.get("output", [])]
        response_text = response.text

    if EXPECTED == "stock":
        assert "function_call" in items
        assert "No tool was run" not in response_text
    elif EXPECTED == "guard":
        assert "function_call" not in items
        assert "No tool was run" in response_text
    else:
        raise AssertionError("HERD_EMPTY_TOOLS_EXPECTED must be 'stock' or 'guard'")
