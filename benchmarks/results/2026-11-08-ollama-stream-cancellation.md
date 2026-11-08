# Ollama stream disconnect check — 2026-11-08

This was one direct, bounded Ollama API check on an existing local node. It
bypassed Herd and did not test Codex task completion. No prompt or generated
content was retained.

| Item | Observation |
|---|---|
| Runtime | Ollama 0.40.15 |
| Model | `qwen3.5:9b-q4_K_M`, already installed |
| Request | Streaming `/api/chat`, `num_predict=512`, request-scoped `keep_alive=0` |
| Response | HTTP 200; first nonempty delta at 2.40 seconds |
| Disconnect | Client closed stream after that delta |
| Return to baseline | `/api/ps` empty 0.09 seconds after close; 2.49 seconds after request start |
| Fleet telemetry | 7/7 online, zero active requests, zero queued or in-flight Herd requests |

This supports that client EOF promptly returned the model to the unloaded idle
baseline in this request. No Ollama journal or server-side cancellation event
was captured, so the check does not prove which internal cancellation path
stopped generation. It is cancellation evidence, not a coding benchmark.

Afterward, a fresh read-only check again found the model unloaded and the fleet
idle. No model was downloaded and no server settings were changed.
