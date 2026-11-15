# Optimization findings

## Request-scoped context allocation — mixed result

On generic Node C, the same Qwen3.6 35B Q4_K_M artifact, prompt, runtime, and
generation settings were measured at 65,536 and 16,384 context. Warm 16K runs
produced 51.12 tokens/s median versus 40.80 at 65K. The two warm 16K client
times had a 2.608 s median versus 3.268 s at 65K. The 16K runner allocation
used 0.529 GB less VRAM after warmup (23.047 versus 23.576 GB); a single
aggregate GPU memory sample was 1,084 MiB lower.

Changing the live runner from 65K to 16K incurred 17.3 s of load/reallocation.
The runner was restored to 65K after measurement. All runs reached the
128-token cap with no visible answer text. Missing TTFT does not invalidate
token throughput or allocation observations, but no useful-answer latency,
correctness, or task-time gain is established. This is a candidate result, not
an accepted optimization or a basis for a production default change.

## Prefix-cache probe — rejected before live use

The Qwen3.5 Hermes worker's probe passed syntax, help, opt-in, and exact-digest
mock checks. It failed offline checks for prompt redaction, control
counterbalancing, real Ollama timing fields, stream/TTFT handling, control-group
classification, exclusive output creation, and error/partial-evidence
semantics. No live prefix-cache request was made.

## Speculative decoding feasibility

Read-only metadata inspection of the tested Qwen3.6 artifact exposed no
draft/MTP metadata. No speculative-decoding run was attempted; compatibility
remains unproven.

## Other candidates

- **Prompt-prefix reuse:** blocked on a new minimal probe passing offline
  acceptance.
- **KV-cache quantization and Flash Attention:** pending proof of an isolated
  reversible runtime and effective-setting logs. Do not change a shared
  service to test global settings.
- **Context quality follow-up:** next candidate; require visible structured
  output, correctness, and TTFT at both context sizes.
