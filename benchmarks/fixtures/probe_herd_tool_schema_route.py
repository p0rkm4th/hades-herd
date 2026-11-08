"""Probe Herd v0.12.3 Responses→Ollama tool-schema translation with fake Ollama.

Run this file as a pytest test inside a disposable Ollama Herd checkout. It
opens no socket and never starts the router or its mDNS advertiser.
"""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from tests.conftest import make_heartbeat
from tests.test_server.test_routes import create_test_app

_FIXTURE_DIR = Path(__file__).resolve().parent
_SCHEMA_SPEC = importlib.util.spec_from_file_location(
    "hades_herd_tool_schema_metadata", _FIXTURE_DIR / "tool_schema_metadata.py"
)
assert _SCHEMA_SPEC is not None and _SCHEMA_SPEC.loader is not None
_SCHEMA_MODULE = importlib.util.module_from_spec(_SCHEMA_SPEC)
_SCHEMA_SPEC.loader.exec_module(_SCHEMA_MODULE)
tool_schema_metadata = _SCHEMA_MODULE.tool_schema_metadata


MODEL = "schema-probe:latest"


def test_responses_function_schema_reaches_ollama_unchanged(tmp_path):
    observed = []
    schema = {
        "type": "object",
        "properties": {
            "cmd": {"type": "string", "description": "synthetic description"},
            "timeout": {"type": "integer", "default": 15},
        },
        "required": ["cmd"],
        "additionalProperties": False,
    }

    def fake_ollama(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        observed.append(body)
        if request.url.path != "/api/chat":
            return httpx.Response(404)
        final = {
            "model": MODEL,
            "message": {"role": "assistant", "content": "schema probe complete"},
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 1,
            "eval_count": 1,
        }
        return httpx.Response(
            200,
            content=(json.dumps(final) + "\n").encode(),
            headers={"content-type": "application/x-ndjson"},
        )

    app = create_test_app(tmp_path=tmp_path)
    with TestClient(app) as client:
        heartbeat = make_heartbeat(
            node_id="schema-probe",
            loaded_models=[(MODEL, 1.0)],
            available_models=[MODEL],
            ollama_host="http://127.0.0.1:11434",
        )
        assert client.post("/heartbeat", json=heartbeat.model_dump()).status_code == 200

        proxy = app.state.streaming_proxy
        node_url = app.state.registry.get_node("schema-probe").ollama_base_url
        proxy._clients["schema-probe"] = httpx.AsyncClient(
            base_url=node_url, transport=httpx.MockTransport(fake_ollama)
        )
        proxy._client_urls["schema-probe"] = node_url

        response = client.post("/v1/responses", json={
            "model": MODEL,
            "input": "Use the supplied tool schema.",
            "tools": [{
                "type": "function",
                "name": "exec_command",
                "description": "synthetic tool description",
                "parameters": schema,
            }],
            "stream": False,
        })

    assert response.status_code == 200, response.text
    assert len(observed) == 1
    ollama_tools = observed[0].get("tools")
    assert isinstance(ollama_tools, list) and len(ollama_tools) == 1
    assert tool_schema_metadata([{
        "type": "function", "name": "exec_command", "parameters": schema,
    }]) == tool_schema_metadata(ollama_tools)
