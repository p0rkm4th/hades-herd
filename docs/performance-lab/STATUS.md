# HADES Performance Lab status

Updated: 2026-11-15

## Verified milestones

A fresh three-model local baseline and a request-scoped 65K-versus-16K context
comparison are documented in BENCHMARKS.md and OPTIMIZATIONS.md. Warm 16K
Qwen3.6 runs were faster and used modestly less resident VRAM, but context
reallocation cost 17.3 seconds and the runs produced no visible answer text.
No task-quality or production-default improvement is claimed.

The first Herdr Hermes cohort is independently classified. The Qwen3.5
prefix-cache probe failed offline acceptance and was not run against a live
model. MiMo produced an initial summarizer that required material supervisor
correction; the corrected private tool passed synthetic and live-record checks.
Both worker panes are idle.

The local Hermes launch path now has an OS-enforced workspace and network
boundary. Five offline tests passed, including a denied external connection and
successful use of a local mock inference API. A Qwen3.6 35B no-tools smoke
request returned its exact response through the configured local route; another
returned through a direct, already-resident local node. These short smoke
requests validate routing only, not model quality or performance gains.

The sandbox now supports one-shot task contracts mounted read-only, clean Git
workspace enforcement, a host-enforced runtime limit, and retained output,
usage, status, and route-audit artifacts. A disposable two-file Qwen3.6 35B
task completed in 79 seconds; independent validation passed all 8 project
tests. The task used 8 model API calls, 56.9K input tokens, and 2.2K output
tokens. This is a small supervised sample, not evidence of broad task
reliability. Nine offline sandbox checks now pass, including output/exit-code
capture and rejection of dirty or externally rooted Git workspaces.

## Limits

- TTFT was unavailable in all baseline/context runs because no nonempty answer
  chunks were observed. Token throughput remains measurable, but useful answer
  latency and correctness do not.
- The prefix-cache experiment is rejected until a minimal replacement passes
  offline acceptance.
- Herdr prompt waits and lifecycle states did not consistently reflect worker
  activity. Wrapped Hermes still appears `unknown`; inspect pane output and
  artifacts instead of treating a stalled prompt wait as a failed submission.
- The sandbox boundary passed integration checks but has not been tested
  against a malicious agent. Keep assignments non-sensitive and review outputs.
- No production route, global service setting, or model default was changed.
- Model selection remains explicit; automatic task-aware selection and safe
  local fallback are still unimplemented.

## Next experiment

Implement automatic local model selection using current capacity and observed
task-role evidence, then demonstrate a moderately complex task with saved
checkpoints and independent review. Do not rerun general baselines or the
rejected prefix-cache probe.

This repository is a reviewable research checkpoint, not a live monitoring
feed.
