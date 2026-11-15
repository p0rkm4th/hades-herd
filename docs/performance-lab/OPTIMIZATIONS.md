# Optimization findings

## Request-scoped context allocation — mixed result

On generic Node C, the same Qwen3.6 35B Q4_K_M artifact, prompt, runtime, and generation settings were measured at 65,536 and 16,384 context. The 16K configuration produced 51.12 tokens/s median versus 40.80 at 65K; the two warm 16K client times had a 2.608 s median versus 3.268 s at 65K. The 16K runner allocation used 0.529 GB less VRAM after warmup (23.047 versus 23.576 GB). A single aggregate GPU memory sample was 1,084 MiB lower.

Changing the live runner from 65K to 16K incurred 17.3 s of load/reallocation. The runner was restored to 65K after measurement. All outputs reached the 128-token cap without visible answer text, and no correctness or task-duration evaluation was possible. Treat this as a context-allocation candidate, not an accepted optimization or a basis for a production default change. More repetitions and a task-level quality check are required.

## Speculative decoding feasibility

Read-only metadata inspection of the tested Qwen3.6 artifact exposed no draft/MTP metadata. No speculative-decoding run was attempted; backend compatibility remains unproven.

## Other candidates

- **Prompt-prefix reuse:** probe implementation and validation are in progress. Compare repeated shared-prefix requests with same-length unique-prefix controls and capture prompt evaluation counters.
- **KV-cache quantization and Flash Attention:** pending isolated-runtime compatibility and effective-setting checks. Do not change a shared service to test global settings.

No production route, service configuration, or model default was changed. The full baseline is in [BENCHMARKS.md](BENCHMARKS.md).
