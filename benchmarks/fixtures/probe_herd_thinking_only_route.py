"""Reproduce thinking-only Ollama chunks through the pinned Herd Responses route.

Run in a disposable checkout of the documented Herd commit. The fake Ollama
backend returns no assistant content and no tool call, only a private thinking
sentinel. Assertions deliberately check that the sentinel never reaches the
OpenAI-compatible response.
"""

from __future__ import annotations

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_heartbeat
from tests.test_server.test_routes import create_test_app

MODEL = "qwen3-coder:30b"
PRIVATE_THINKING = "PRIVATE THINKING SENTINEL"


@pytest.mark.parametrize("stream", [False, True])
def test_thinking_only_completion_becomes_empty_responses_output(tmp_path, stream):
    observed_backend_requests = []

    def fake_ollama(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        observed_backend_requests.append(body)
        chunk = {
            "model": MODEL,
            "message": {"role": "assistant", "content": "", "thinking": PRIVATE_THINKING},
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 7,
            "eval_count": 0,
        }
        return httpx.Response(
            200,
            content=(json.dumps(chunk) + "\n").encode(),
            headers={"content-type": "application/x-ndjson"},
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
            json={
                "model": MODEL,
                "input": "continue",
                "tools": [{
                    "type": "function",
                    "name": "exec_command",
                    "parameters": {"type": "object", "properties": {}},
                }],
                "stream": stream,
            },
        )

    assert response.status_code == 200, response.text
    assert len(observed_backend_requests) == 1
    assert len(observed_backend_requests[0].get("tools", [])) == 1
    if stream:
        events = [
            json.loads(line[6:])
            for line in response.text.splitlines()
            if line.startswith("data: ")
        ]
        completed = next(event["response"] for event in events if event.get("type") == "response.completed")
        assert completed["status"] == "completed"
        assert completed["output"] == []
    else:
        completed = response.json()
        assert completed["status"] == "completed"
        assert completed["output"] == []

    assert PRIVATE_THINKING not in response.text
