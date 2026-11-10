# MiMo 9B Q4 128K context screen — 2026-11-10

## Setup

Used the existing `mimo-v26-9b-codex-64k-hecate:latest` alias with a
request-scoped `options.num_ctx=131072`; no alias, model, service, route, or
default changed. The fixture prefixed `SECRET_MARKER=EMBER-731` to 75,000
repetitions of `the`, then requested the exact marker through a required
`record_result` function call. Each attempt had a 180-second wall cap. This
was a context/tool screen, not a coding task.

Reproduce against the same existing Ollama alias with `/api/chat`, streaming
enabled, `num_ctx=131072`, `num_predict=512`, and the prompt described above.
Make one baseline request, then one otherwise identical correction with
`think:false`. Poll `/api/ps` for actual context and `size_vram` during each
request. Do not create a 128K alias based on allocation alone.

## Measurements

| Run | First stream data | Actual context | Runner size / VRAM | Result |
|---|---:|---:|---:|---|
| Default thinking | 22.073 s | 131,072 | 9,897,110,404 / 9,897,110,404 bytes | Stream ended without final completion event or tool call |
| `think:false` | 21.878 s | 131,072 | 9,897,110,404 / 9,897,110,404 bytes | Stream ended without final completion event or tool call |

Both attempts used 100% GPU residency and reported no client exception. Neither
produced final prompt/decode token counts. The result does not isolate whether
the cause is model/tool behavior or stream handling; no third request was run.

A strict-key journal review confirmed that the backend processed 75,126 prompt
tokens in 18.53 seconds (about 4,054 tokens/s), with no OOM, runner crash, or
backend error during the request window. The direct test used Ollama NDJSON,
not Herd Responses/SSE. Prefill succeeded; the available evidence cannot
separate model/tool completion behavior from Ollama stream closure because raw
generation chunks were not retained.

The test allocation was unloaded. A short request restored the original
65,536 allocation at 7,682,517,892 bytes of VRAM. No service restart or
production configuration change occurred.

## Decision

Keep MiMo 64K as the longest reliable tested profile. 128K allocation fits,
but the required tool completion failed twice, so no 128K profile is promoted.
