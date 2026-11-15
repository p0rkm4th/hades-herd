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
The later one-run restore check generated one token and reported 1,000,000
tokens/s; it is an invalid rate and is excluded from the comparison.

## Prefix-cache probe — rejected before live use

The Qwen3.5 Hermes worker's probe passed syntax, help, opt-in, and exact-digest
mock checks. It failed offline checks for prompt redaction, control
counterbalancing, real Ollama timing fields, stream/TTFT handling, control-group
classification, exclusive output creation, and error/partial-evidence
semantics. No live prefix-cache request was made.

## Speculative decoding feasibility

Ollama 0.40.15 source includes `draft_num_predict` handling, and the tested
Qwen3.6 model-derived options expose value 2. This does not establish usable
draft weights or embedded MTP tensors, nor an effective performance change.
No speculative-decoding run was attempted; qualify the exact local artifact
and runner before a request-scoped comparison.

## Visible-answer context follow-up — inconclusive

At 16K, two warm samples had median TTFT 3.653 s and generation 53.94 tok/s;
at 65K, two warm samples measured 3.938 s and 49.96 tok/s. The 16K warm
result was about 7% faster to first text and 8% faster in generation. All six
runs contained the expected marker, but recorded output was only 11 characters.
The `/api/ps` metadata reported the preceding context setting, so effective
allocation and memory for this follow-up are unverified. The earlier capped
microbenchmark separately reported lower 16K runner allocation; it had no
visible answer and does not establish a quality or task-time benefit.

**Decision: KEEP EXPERIMENTAL.** The warm gains are below the 15% target, the
comparison is not counterbalanced, and full answer correctness is unknown. Do
not change the default. Validate effective allocation and full response capture
before a matched engineering task comparison.

## Other candidates

- **Prompt-prefix reuse:** blocked on a new minimal probe passing offline
  acceptance.
- **KV-cache quantization and Flash Attention:** pending proof of an isolated
  reversible runtime and effective-setting logs. Do not change a shared
  service to test global settings.
- **Context quality follow-up:** next candidate; require an accepted
  engineering task, correctness, and TTFT at both context sizes.

## Worker tool acceptance checkpoint

The prefix-cache probe remains rejected after a fresh loopback mock reproduced
prefix disclosure, prefix-first ordering, and silent output append. The
supervisor-corrected MiMo summarizer independently passed synthetic median,
null-TTFT, cold/warm, empty-response, duplicate-run, and no-overwrite checks.
These are tool reliability results, not inference optimization gains.

## Status observability — accepted in the isolated lab harness

The supervisor added content-free aggregate local inference activity to worker
status after independent inspection of two incomplete Herdr runs exposed a gap
between queue counters and actual serving requests. The view reports call and
successful-response counts plus latest-request age; it preserves output age as
the separate progress signal. The 55-test offline tool suite passes. This
improves diagnosis only; it is not a model speedup and has not been deployed to
production infrastructure.

## Context measurement interpretation

The first 128-token context microbenchmark produced zero visible response
characters. Its server token counters still permit a capped-decode comparison,
but it cannot support TTFT or useful-answer latency claims. In the separate
short synthetic sentinel follow-up, all six runs emitted the expected answer;
there were two warm samples per context, in non-counterbalanced order. Warm
TTFT was 3.653 s at 16K and 3.938 s at 65K; generation was 53.94 and 49.96
tok/s. Each context transition cost about 17.3 s. Keep the result experimental:
it does not establish accepted engineering-task quality or a worthwhile
reallocation policy.
