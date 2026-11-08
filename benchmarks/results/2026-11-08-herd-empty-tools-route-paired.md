# Herd empty-tool Responses route comparison — 2026-11-08

This compares unmodified Ollama Herd v0.12.3 with a small experimental
translator guard. It exercises the full in-process `/v1/responses` route,
scoring, queue, streaming proxy, and Responses conversion, with fake Ollama at
the `/api/chat` transport boundary. It is not a model-quality result.

## Setup

- Both worktrees used upstream Herd commit
  `e0dac345515e8423e385ea2d465573a1e8b5a1bf`.
- Stock ran unmodified. The comparison worktree applied the change-only
  [guard patch](../fixtures/patches/herd-v0.12.3-empty-tools-guard.patch).
- Python 3.13.14 and pytest 9.2.0 were used in an isolated venv.
- The existing Herd test app was exercised in-process with `TestClient`. Its
  helper does not start mDNS. Ollama calls used `httpx.MockTransport`; no
  listener, LAN connection, model, or production service was involved.
- The public test fixture
  [`probe_herd_empty_tools_route.py`](../fixtures/probe_herd_empty_tools_route.py)
  sends an explicit `tools: []`. The fake Ollama backend verifies Herd omitted
  the `tools` field, then returns a synthetic `exec_command` call. Both
  streaming and non-streaming requests were tested.

## Results

| Herd translator | Streaming | Ollama received tools | Responses result | HTTP |
|---|---|---|---|---:|
| Stock v0.12.3 | No | No; field absent | `function_call: exec_command` | 200 |
| Stock v0.12.3 | Yes | No; field absent | `function_call: exec_command` | 200 |
| Guard prototype | No | No; field absent | Visible message; no function call | 200 |
| Guard prototype | Yes | No; field absent | Visible message; no function call | 200 |

The comparison reproduces the source-level mismatch at the complete route
boundary and confirms the guard's behavior in both response modes. The
`exec_command` is synthetic and was not executed by Codex or a shell in this
route test.

An initial harness attempt failed because its cached mock-client URL differed
from the registry URL; the proxy replaced it and attempted a DNS connection.
The harness was corrected to use the registry's exact URL, then all four
paired cases passed. The failed setup is excluded from the result.

## Interpretation and limits

The original source explanation is now supported by both full-route evidence
and the separate Codex boundary probe: stock Herd can return a tool call after
Ollama received no tool catalog, while the guard returns a user-visible message
instead. This is consistent with the historical trace, where five empty-tool
Responses requests returned `exec_command`.

It still does not prove that this adapter behavior caused the HTTPie task's
inspection loop or timeout. No historical Ollama request/response body was
captured, the synthetic backend does not run a model, and these route tests do
not run Codex through Herd. The guard remains an unapplied prototype; the
production router is unchanged. The focused translator suite and complete
upstream suite passed previously on the same patch (61 translator tests;
1,992 passed, 5 skipped in the full suite). Reproduction instructions and the
change-only patch are in
[`fixtures/patches/`](../fixtures/patches/README.md).
