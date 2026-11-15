# Local inference benchmarks

## Fresh short-prompt baseline — 2026-11-15

Three local configurations were measured serially on Ollama 0.40.15. Each had three runs, no overlapping benchmark requests, context 65,536, `num_predict=128`, temperature 0, and seed 7. Models were cold on the first run for Nodes A and B and warm throughout on Node C. Values below are medians.

| Generic node | Hardware class | Model | Client time | First cold load | Prompt processing | Prompt tok/s | Generation tok/s | TTFT |
|---|---|---|---:|---:|---:|---:|---:|---|
| Node A | 10 GB consumer GPU | Qwen3.5 9B Q4_K_M | 1.376 s | 2.335 s | 0.041 s | 1,139.6 | 99.1 | unavailable |
| Node B | 12 GB consumer GPU | MiMo V2.6 9B Q4_K_M | 1.649 s | 2.265 s | 0.039 s | 1,171.3 | 80.9 | unavailable |
| Node C | 4 × 8 GB workstation GPUs | Qwen3.6 35B Q4_K_M | 3.268 s | warm | 0.089 s | 530.0 | 40.8 | unavailable |

Each run reached the 128-token cap, but the harness saw zero nonempty `response` chunks. TTFT therefore remained null; do not interpret client time or token throughput as time to a useful answer. The first two rows include one first-run cold load, while the client-time median is warm-dominated. No matched peak-memory sample or task-correctness check was taken.

The exact public synthetic workload and capture controls are in [METHODOLOGY.md](METHODOLOGY.md). Model digests and raw telemetry are deliberately kept private.

## Visible-answer context follow-up — 2026-11-15

The earlier context comparison emitted no visible text. A later synthetic
fixed-answer check at 16,384 and 65,536 context verified the same 11-character
expected answer on all three runs per setting. Warm medians exclude the first
request after context reallocation; only two warm samples remain per setting.

| Generic node | Context | Warm client time | Warm TTFT | Warm generation | Warm prompt processing | Runner VRAM allocation |
|---|---:|---:|---:|---:|---:|---:|
| Node C | 16,384 | 3.756 s | 3.653 s | 53.94 tok/s | 497.0 tok/s | 23.047 GB |
| Node C | 65,536 | 4.046 s | 3.938 s | 49.96 tok/s | 481.8 tok/s | 23.576 GB |

The first request after changing context incurred 17.27–17.29 s of runner
reallocation. The comparison used the same model, 38-token prompt, seed,
temperature, and output budget. The order was 16K then 65K, not
counterbalanced. This validates only a short synthetic answer; it does not
show engineering-task quality or long-context retention. Runner allocation
is not peak memory.

## Context allocation comparison

Node C ran the same model and workload at 16,384 context in three additional serial runs, then returned to 65,536 context. The median of the two warm 16K runs was 2.608 s client time and 51.12 tokens/s; the 65K baseline medians were 3.268 s and 40.80 tokens/s. The first context transition required a 17.304 s runner reallocation. Runner VRAM allocation after warm runs was 23.576 GB at 65K and 23.047 GB at 16K. A single aggregate GPU memory sample fell 4.4%; this is not a peak-memory measurement. Output remained unavailable and correctness was not tested. See [OPTIMIZATIONS.md](OPTIMIZATIONS.md) for interpretation.


### TTFT interpretation

The missing visible-token TTFT does not invalidate the API-reported generated
token counts, prompt/generation durations, or resident allocation samples.
It does invalidate conclusions about time to a useful answer, task duration,
and correctness. These measurements are inference microbenchmarks only.
