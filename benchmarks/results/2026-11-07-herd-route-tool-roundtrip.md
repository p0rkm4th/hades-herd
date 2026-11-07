# Codex tool round trip through an isolated Herd route

Date: 2026-11-07. This check exercised the HADES client, Codex CLI, Herd
v0.12.3's real `/v1/responses` route, and its translator/queue/streaming path.
Ollama was replaced by an in-process `httpx.MockTransport`; no model or
production service was contacted.

## Setup and result

**PASS.** Codex CLI 0.166.0 ran with temporary HOME/CODEX_HOME, a read-only
sandbox, a 45-second process timeout, and only an explicit loopback
`CODEX_HERD_URL`. The synthetic registry exposed one loaded 4K-context mock
model. The mock backend recorded tool names, call/result IDs, and fixed marker
presence.

1. Codex advertised `exec_command`; the Herd Responses route forwarded it to
   the mock Ollama `/api/chat` request.
2. The mock returned two sequential `exec_command` calls, each running a fixed
   `printf` marker.
3. Codex executed both and sent each matching `function_call` and
   `function_call_output` in its next request.
4. Herd reconstructed both assistant tool calls and tool messages for Ollama
   with matching IDs and markers.
5. Codex received a final response and emitted `turn.completed` with exit 0.

The fixture also records whether Herd receives an `exec_command` definition on
each backend request. In this run it was present on all three requests.

The complete test took under one second. In the latest two-step run, all three
backend requests included the `exec_command` definition, and each request
after the first carried the accumulated matching call/result history. The
reproducible fixture is
[`run_herd_route_tool_roundtrip.py`](../fixtures/run_herd_route_tool_roundtrip.py);
setup is documented in the [benchmark guide](../README.md#full-isolated-herd-route-check).
It retains raw Codex stdout/events and stderr only in the operator-selected
local artifact directory; the published result contains no raw transcript.

## Interpretation and limits

For this two-step valid advertised function-call sequence, the Codex → Herd →
Ollama request/result path preserves tool availability, each call ID, and both
returned tool results. This rules out a general failure of that route for
this tested workflow. The empty `tools` arrays seen on some requests in the
separate live HTTPie trace were not reproduced in this deterministic shape, so
their cause remains open. This does not test a real model, arbitrary tool
schemas, other Codex versions, or every streaming/error path.

Together with the separate loopback control, Codex rejects an unadvertised
`read_file` call while accepting an advertised `exec_command`. That makes a
model-selected unsupported tool name plausible for the historical rejection,
but the historical event remains unproven. The later live HTTPie trace did not
contain that event. Inspection loops, long task times, and missing final turns
remain open.

The server emitted its expected warning that hosted `web_search` has no local
Ollama equivalent and is dropped. The executable `exec_command` still passed
through. No tool was downloaded, no inference ran, and no HADES production
configuration was changed.

Validation: HADES client tests **15/15**; upstream Herd Responses translator
and route modules **65/65**; the integrated three-request/two-tool Codex/Herd/
mock-Ollama route **PASS**. The route fixture requires a local Herd v0.12.3
checkout and Codex CLI, so GitHub Actions syntax-checks it and runs the
dependency-free client suite. The published route result was reproduced with:

```sh
python benchmarks/fixtures/run_herd_route_tool_roundtrip.py \
  --herd-source /path/to/ollama-herd-v0.12.3 \
  --artifacts /tmp/herd-route-roundtrip-multistep-try2-20261107
```
