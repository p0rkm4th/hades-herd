# Qwen3.5 128K long-prompt/tool check — 2026-11-10

One bounded request tested the existing Qwen3.5 9B Q4 Charon profile with a
75,312-token prompt and an exact-retrieval tool call. The backend allocated
131,072 context and returned the exact requested value through the tool. This
is a single long-context capability check, not a coding reliability score.

| Measurement | Result |
|---|---:|
| Actual context | 131,072 |
| Prompt tokens | 75,312 |
| First data / first output | 58.5 s / 88.0 s |
| Prompt processing | 54.7 s |
| Total time | 88.2 s |
| GPU residency | 8.23 / 11.43 GB (about 72%) |
| CPU offload | 3.20 GB (about 28%) |
| Tool result | Exact retrieval succeeded |

An earlier run used too small an output budget and ended before emitting the
tool call; that result was inconclusive. The one corrected run raised the
output cap and fixed backend telemetry, then completed successfully. The
runner was unloaded afterward. No model alias, production setting, or default
changed.

**Decision:** retain 64K as the practical profile. The 128K result confirms
one successful retrieval path but its 28% CPU offload and 88-second first
tool response do not justify a default or a promoted profile. The full
independent five-task coding comparison remains separate in the
[Qwen3.5/MiMo report](2026-11-09-hermes-qwen35-mimo-comparison.md).
