# Optimization findings

## Tested changes

No runtime optimization has completed a before/after evaluation yet. The 2026-11-15 data in [BENCHMARKS.md](BENCHMARKS.md) is a baseline, not an optimization.

## Candidates and controls

- **Prompt-prefix reuse:** in progress. Compare repeated shared-prefix requests with same-length unique-prefix controls. Capture prompt evaluation counters and duration; do not infer a cache hit from similar text alone.
- **KV-cache quantization and Flash Attention:** pending isolated-runtime compatibility and effective-setting checks. Do not change a shared service to test global settings.
- **Speculative decoding:** pending proof that the exact local model/runtime exposes usable draft or MTP support. Upstream flags alone are not compatibility evidence.

No improvement is claimed until matched repetitions, runtime/model identity, context, correctness, and resource use are independently checked.
