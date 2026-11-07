# Real Codex model-specific profile smoke test — 2026-11-07

This test validates the generated profile against Codex CLI itself. It uses the
loopback-only deterministic Responses fixture, not Herd or an inference model.

- Codex CLI: 0.166.0.
- Fresh temporary `HOME`; `codex-herd.py` generated the model-specific profile
  and catalog from a mock live model named `mock-codex:latest`.
- The launch completed with exit 0 and a `turn.completed` event after two
  Responses requests.
- Both requests exposed the expected local Codex tool catalog. The second
  request included Codex's synthetic unsupported-call result for the fixture's
  intentionally unadvertised `read_file` function.
- The fixture reported no API reasoning-effort field, as expected for this
  diagnostic, and contacted only its loopback server. No Ollama model or hosted
  inference provider was involved.

This verifies Codex accepts the generated named profile/catalog and the
launcher reaches it. The expected `read_file` rejection is a control case; the
test does not make claims about real-model coding quality or the cause of live
inspection loops. Raw CLI event output and temporary paths remain local.

## Valid tool follow-up control — 2026-11-08

A separate bounded loopback run used the same installed Codex CLI 0.166.0 with a
mock Responses server and no model backend. The first request advertised
`exec_command`; the server returned a harmless `printf` call. Codex executed it
successfully. The second request included one prior function call and one tool
result, and again advertised the complete 13-name local tool set. Codex then
accepted the final message and emitted `turn.completed` (exit 0). The requests
and call arguments are not published.

This confirms the ordinary single-agent call/result/final turn. It did not
reproduce a request with an empty tool list, so it does not explain the empty
`tools` entries observed in the separate live trace. That behavior appears to
belong to another Codex request path or condition; no cause is established.
