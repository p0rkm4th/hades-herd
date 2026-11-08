# Empty-tool Codex boundary probe — 2026-11-08

This deterministic protocol probe checks what Codex CLI does with a Responses
`exec_command` item when the simulated adapter/backend tool catalog is empty.
It is not an Ollama model test, a Herd integration test, or a coding benchmark.

## Method

- Codex CLI 0.166.0 ran twice against an ephemeral loopback-only Responses
  server, each time from a fresh temporary Codex home and Git repository.
- Requests used a custom local provider, `requires_openai_auth = false`, a
  workspace-write sandbox, `approval_policy = never`, and a 30-second process
  timeout. No OpenAI endpoint, Herd router, or inference node was used.
- The fixture records only the number of tools in the Codex request, a
  hard-coded simulated backend offer count of zero, request count, exit code,
  and whether a disposable marker file appeared. It retains no prompt, tool
  arguments, or event transcript.
- In `stock` mode, the mock adapter returned a synthetic `exec_command`
  function call despite the simulated zero-tool backend offer. In `guard`
  mode, it returned visible assistant text and no function call.

## Result

| Mode | Codex request tools | Simulated backend tools | Codex command ran | Exit | Requests |
|---|---:|---:|---|---:|---:|
| stock | 9 | 0 | Yes; marker created | 0 | 2 |
| guard | 9 | 0 | No; marker absent | 0 | 1 |

Codex executed the function call supplied by the endpoint in stock mode. It did
not execute a command in guard mode. The result confirms the client-side
behavior for this synthetic response sequence and validates that the proposed
guard response is visible without running a tool.

## Limits and next step

Codex itself advertised nine tools in both runs. The mock's backend offer of
zero was injected after that request; therefore this does **not** reproduce a
real Codex request whose `tools` field is `[]`, nor prove that the historical
HTTPie calls followed this path. An additional attempt with Codex's shell-tool
feature disabled timed out before sending any Responses request and is not a
valid empty-tools comparison. The pinned Herd translator/route tests remain
the direct evidence that an explicit incoming `tools: []` can be preserved
and guarded.

Reproduce on a machine with Codex CLI:

```sh
python3 benchmarks/fixtures/run_empty_tools_guard_probe.py
```

The source is [`../fixtures/run_empty_tools_guard_probe.py`](../fixtures/run_empty_tools_guard_probe.py).
