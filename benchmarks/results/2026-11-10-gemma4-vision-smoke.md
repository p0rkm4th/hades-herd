# Gemma4 12B basic vision smoke — 2026-11-10

An isolated local Ollama check used the synthetic [blue/yellow image fixture](../fixtures/gemma4-vision/blue-top-yellow-bottom.png), SHA-256 `789dd7ed7935df5e251cb0a16941d8c0a72cc1bac3b046f605986049091d6dc7`.

| Request | Result |
|---|---|
| Default thinking, 8-token cap | No visible answer; 8 tokens generated. |
| Same prompt with `think: false` | Correct `BLUE`; 2 tokens generated; 4.34 s end-to-end. |
| Backend | `gemma4:12b`, Q4_K_M; actual 8,192 context. |
| Residency | 9.04 GB entirely in GPU memory across two GPUs during the request; post-unload both returned to 3 MiB. |

The prompt asked for the color in the upper half of a 48×48 image. The only changed request setting in the corrected call was `think: false`. The model was unloaded afterward. No service or model configuration changed.

**Decision:** Basic image input and color recognition work when thinking is disabled. This single synthetic check does not qualify Gemma4 for general vision tasks or agentic vision. Its separate 180-second coding smoke failed without a tool call or edit; do not assign it a coding role.

To reproduce against an already-installed model and a local Ollama endpoint, send `/api/chat` with `stream: false`, `think: false`, `options: {num_ctx: 8192, num_predict: 8, temperature: 0}`, and the fixture encoded in `messages[0].images`. Unload with `/api/generate` and `keep_alive: 0`. Do not add a hosted fallback.
