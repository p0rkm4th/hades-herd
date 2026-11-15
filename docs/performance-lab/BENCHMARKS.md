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
