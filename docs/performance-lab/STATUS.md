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
workspace enforcement, Hermes filesystem checkpoints, a host-enforced runtime
limit, and a live `starting`/`running` status file with retained output, usage,
and route-audit artifacts. Automatic model selection uses task role plus live
node queues, slots, runner residency, and exact model digest. It selects only
warm local models, refuses cold loads, and serializes its own tasks per node.

Four bounded tasks across Qwen3.5, Qwen3.6, and MiMo passed independent checks.
The Qwen3.5 quick coding task took 25.8 seconds and passed all 16 project tests.
The Qwen3.6 batch API task took 79.2 seconds and passed all 8 project tests.
The MiMo documentation task completed in 42.1 seconds and passed all 16 tests;
the supervisor corrected one misleading rounding statement in its README
draft. This small sample supports bounded use only. The Qwen3.6 task used 56.9K
input and 2.2K output tokens; the Qwen3.5 task used 38.0K input and 1.5K
output tokens. The MiMo usage file omitted token counts despite successful
chat responses, so that run's token cost is unverified. Fourteen offline
sandbox checks now pass, including queue and model selection behavior.

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
- Task type comes from a short keyword heuristic. The selector may fall back
  to another ready local model before a task starts, but it does not rerun
  failed work. Per-node locks and queue checks support separate idle nodes;
  concurrent multi-worker execution has not been demonstrated.

## Next experiment

Demonstrate a moderately complex local task with saved checkpoints and
independent review, then distinct Herdr subtasks on separate local workers.
Do not rerun general baselines or the rejected prefix-cache probe.

This repository is a reviewable research checkpoint, not a live monitoring
feed.
