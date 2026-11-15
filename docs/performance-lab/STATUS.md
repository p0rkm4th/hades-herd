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

## Limits

- TTFT was unavailable in all baseline/context runs because no nonempty answer
  chunks were observed. Token throughput remains measurable, but useful answer
  latency and correctness do not.
- The prefix-cache experiment is pending a new minimal probe that passes
  offline acceptance.
- Herdr prompt waits and lifecycle states did not consistently reflect worker
  activity. Workspace cwd did not prevent workers from reading outside their
  assignments.
- No production route, global service setting, or model default was changed.

## Next experiment

Evaluate the 16K context candidate using a visible structured answer and an
independent correctness contract, with TTFT and context-transition load
reported separately. See METHODOLOGY.md before running it.

This repository is a reviewable research checkpoint, not a live monitoring
feed.
