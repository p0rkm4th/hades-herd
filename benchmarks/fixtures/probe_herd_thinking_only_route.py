"""Probe response shape and client cancellation in pinned Herd v0.12.3.

Run in a disposable checkout of the documented Herd commit. The fake Ollama
backend returns no assistant content and no tool call, only a private thinking
sentinel. Assertions check that the sentinel is not exposed. A second probe
closes the client mid-stream and checks cancellation reaches the mocked
backend stream and releases the queue slot; real Ollama generation cancellation
is outside this test.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_heartbeat
from tests.test_server.test_routes import create_test_app

MODEL = "qwen3-coder:30b"
PRIVATE_THINKING = "PRIVATE THINKING SENTINEL"
EXPECTED_EMPTY_RESPONSE = os.environ.get("HERD_EMPTY_RESPONSE_EXPECTED", "stock")


def test_client_disconnect_cancels_backend_stream(tmp_path):
    backend_cancelled = threading.Event()

    class SlowBackendStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            first_chunk = {
                "model": MODEL,
                "message": {"role": "assistant", "content": "working"},
                "done": False,
            }
            yield (json.dumps(first_chunk) + "\n").encode()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                backend_cancelled.set()
                raise

        async def aclose(self):
            backend_cancelled.set()

    def fake_ollama(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        return httpx.Response(200, stream=SlowBackendStream(), headers={
            "content-type": "application/x-ndjson",
        })

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

        with client.stream(
            "POST",
            "/v1/responses",
            json={"model": MODEL, "input": "continue", "stream": True},
        ) as response:
            assert response.status_code == 200
            first_event = next(response.iter_bytes())
            assert b"response.created" in first_event

    assert backend_cancelled.wait(1), "Herd did not close the backend stream after client disconnect"
    deadline = time.monotonic() + 1
    while any(info["in_flight"] for info in app.state.queue_mgr.get_queue_info().values()):
        assert time.monotonic() < deadline, "Herd kept the cancelled request in flight"
        time.sleep(0.01)


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
        terminal = next(event for event in events if event.get("type") in {"response.completed", "response.failed"})
        completed = terminal["response"]
    else:
        completed = response.json()

    assert completed["output"] == []
    if EXPECTED_EMPTY_RESPONSE == "stock":
        assert completed["status"] == "completed"
        assert terminal["type"] == "response.completed" if stream else True
    elif EXPECTED_EMPTY_RESPONSE == "failure":
        assert completed["status"] == "failed"
        assert "no visible content" in completed["error"]["message"]
        assert terminal["type"] == "response.failed" if stream else True
    else:
        raise AssertionError("HERD_EMPTY_RESPONSE_EXPECTED must be 'stock' or 'failure'")

    assert PRIVATE_THINKING not in response.text
