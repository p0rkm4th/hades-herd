# Codex tool round trip through an isolated Herd route

Date: 2026-11-07. This check exercised the HADES client, Codex CLI, Herd
v0.12.3's real `/v1/responses` route, and its translator/queue/streaming path.
Ollama was replaced by an in-process `httpx.MockTransport`; no model or
production service was contacted.

## Setup and result

**PASS.** Codex CLI 0.166.0 ran with temporary HOME/CODEX_HOME, a read-only
sandbox, a 45-second process timeout, and only an explicit loopback
`CODEX_HERD_URL`. The synthetic registry exposed one loaded 4K-context mock
model. The mock backend recorded only tool names and call/result IDs, plus a
boolean for a fixed test marker.

1. Codex advertised `exec_command`; the Herd Responses route forwarded it to
   the mock Ollama `/api/chat` request.
2. The mock returned one `exec_command` call with `printf tool-roundtrip-ok`.
3. Codex executed it and sent the matching `function_call` and
   `function_call_output` on its next request.
4. Herd reconstructed the assistant tool call and tool message for Ollama with
   the same call ID and expected marker.
5. Codex received a final response and emitted `turn.completed` with exit 0.

The complete test took under one second. The reproducible fixture is
[`run_herd_route_tool_roundtrip.py`](../fixtures/run_herd_route_tool_roundtrip.py);
setup is documented in the [benchmark guide](../README.md#full-isolated-herd-route-check).
It retains raw Codex stdout/events and stderr only in the operator-selected
local artifact directory; the published result contains no raw transcript.

## Interpretation and limits

For this valid advertised function-call shape, the Codex → Herd → Ollama
request/result path preserves tool availability, the call ID, and the returned
tool result. This rules out a general failure of that route for this specific
workflow. It does not test a real model, arbitrary tool schemas, other Codex
versions, or every streaming/error path.

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
and route modules **65/65**; this integrated Codex/Herd/mock-Ollama route
**PASS**. The route fixture requires a local Herd v0.12.3 checkout and Codex
CLI, so GitHub Actions tests only the dependency-free client suite. The
published route result was reproduced with:

```sh
python benchmarks/fixtures/run_herd_route_tool_roundtrip.py \
  --herd-source /path/to/ollama-herd-v0.12.3 \
  --artifacts /tmp/herd-route-roundtrip-run-01
```
