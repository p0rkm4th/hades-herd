# HADES Performance Lab status

Updated: 2026-11-15

## Verified milestone

A fresh serial baseline is recorded for three local Ollama model/node configurations. Each used three matched runs with a fixed synthetic troubleshooting prompt, 65,536 context, and a 128-token generation cap. All runs completed; generation throughput medians ranged from 40.8 to 99.1 tokens/s. The full comparison and important measurement limits are in [BENCHMARKS.md](BENCHMARKS.md).

A request-scoped 65K-versus-16K context comparison is complete. Warm 16K runs were faster and used modestly less resident VRAM, but changing context incurred a 17.3 s runner reallocation and no answer-quality check was possible. It is a mixed candidate result, not an accepted production optimization. Details are in [OPTIMIZATIONS.md](OPTIMIZATIONS.md).

Two local Hermes workers have been launched through Herdr on separate compute nodes. Their implementation tasks remain in progress; no worker result is accepted yet.

## Limits and blockers

- The streaming harness observed no nonempty answer chunks in the nine live baseline runs, so TTFT is unavailable. These measurements do not establish answer latency, correctness, or task quality.
- One cataloged candidate was excluded pending direct host preflight; no benchmark request was sent to it.

## Next experiments

1. Independently validate the worker-built shared-prefix probe, then measure warm-prefix reuse against matched unique-prefix controls.
2. Validate the worker-built benchmark summarizer with synthetic input.
3. Continue with isolated KV-cache/Flash Attention or speculative-decoding feasibility only after verifying the installed runtime supports a reversible test configuration.

This repository provides reviewable checkpoints; it is not a live monitoring feed.
