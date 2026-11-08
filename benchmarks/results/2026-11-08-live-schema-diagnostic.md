# Live Codex/Herd/Ollama schema diagnostic — 2026-11-08

## Scope

One bounded protocol diagnostic used a fresh synthetic repository with a small
discount-calculation bug. It was not a model-quality benchmark. The disposable
Herd 0.12.3 test app routed only to one installed model on an RTX 4070 Ti host;
production Herd configuration was not changed.

- Codex CLI 0.166.0; Ollama 0.40.15; Herd 0.12.3 at
  `e0dac345515e8423e385ea2d465573a1e8b5a1bf`.
- MiMo-V2.6 9B Q4_K_M, configured 16K context, model digest
  `47f141d59fb9ece0a349cf27e8292b8c192ae0082b8a051c2e29c06526feea4b`.
- One successful Codex turn took 29.8 seconds. Codex emitted `turn.completed`;
  independent standard-library tests passed 5/5. No retry or human patch
  correction was needed.
- A prior setup attempt returned 503 from the disposable router because its
  synthetic heartbeat omitted model-size eligibility metadata. It made no
  Ollama request and is excluded from the result.

## Schema observations

- All 10 Codex `/v1/responses` requests carried a non-empty tool offer. Each
  had nine top-level entries representing 12 function names plus `web_search`.
- All 10 Ollama `/api/chat` requests carried seven function schemas. The seven
  shared function names had identical captured parameter structure at both
  boundaries. The five Codex-only functions were nested multi-agent controls
  not offered by the Herd/Ollama adapter.
- Ollama returned eight `exec_command` calls, one `read` call, then a final
  response. `read` was not in the tool schemas offered to Ollama. Codex still
  completed this task, but the Codex-side response observer did not preserve
  response-event metadata, so this run cannot establish how Codex handled that
  particular call.
- No empty tool offer occurred in this task. That does not explain the separate
  historical traces that did contain empty offers.

## Observer correction and limits

The first live run revealed that the Codex trace proxy recorded an
`AttributeError` while Codex closed each completed SSE connection. The proxy
still forwarded enough data for Codex to finish, but its response metadata from
that run is not evidence. A regression test now delays SSE parsing and closes
the client immediately after the terminal event; the proxy parses and marks a
completed event before forwarding it, then avoids cancelling that completed
upstream response. The offline proxy tests and full 43-test client suite pass.

The corrected observer has not yet been revalidated against another live
Codex/model session. The tool-schema result above relies on request-side
metadata from Codex and request/response metadata from Ollama only. This single
task is diagnostic evidence, not a daily-driver score.
