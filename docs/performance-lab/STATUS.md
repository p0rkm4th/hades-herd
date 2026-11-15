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
and route-audit artifacts. Status now includes a throttled wrapper heartbeat,
last output time, and output counters. A small redacted CLI distinguishes
heartbeat from worker activity and reports active/terminal exit codes.
Automatic model selection uses task role plus live
node queues, slots, runner residency, and exact model digest. It selects only
warm local models, refuses cold loads, and serializes its own tasks per node.

The interactive Herdr shim now defaults to that automatic local selector and
accepts all configured local aliases; unknown and hosted names are rejected.
Its Qwen3.5 implementation attempt stopped with exit 2 after editing only the
shim, so the worker did not complete its acceptance step. A supervisor
correction passed four offline tests and both manifest checks in a networkless
snapshot. Auto-selection preflight confirmed a warm, digest-verified local
profile without sending inference. Count this as supervisor-assisted work,
not autonomous completion.

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

A separate validation-heavy Qwen3.6 35B task on an already-resident local node
ran for 7.4 minutes and made 13 local completion requests; 12 returned HTTP
200. It produced a large status-viewer draft, but independent validation found
32 failures in 47 worker-authored tests, so the task was interrupted and the
draft was not integrated. This is one supervised failure sample, not a model
reliability estimate. The run had no finalized usage totals. A corresponding
supervisor fix now records SIGINT termination as `interrupted` with shell exit
130. The combined sandbox and status-viewer suite passes 29 offline tests.

The one-shot runner now accepts a bounded JSON acceptance manifest. After a
successful worker exit it runs argv-only checks in a network-isolated copy of
the task workspace, records per-check status, and leaves the worker tree
unchanged. The combined offline suite now passes 40 tests. A direct fixture
run passed 12 tests in the isolated copy. A second bounded Qwen3.5 coding task
was independently rejected: the worker exited 2 after 68 seconds with
incorrect expected totals and list-row handling. Supervisor fixes passed the
same checks, but the worker attempt remains incomplete and is not counted as an
autonomous success.

An additional isolated Actual CSV import task used local Qwen3.6 35B for two
bounded implementation steps: duplicate-header handling and mapping-column
validation. Both completed with independent acceptance; the final focused suite
passed 10 tests plus the existing import contract. A separate MiMo review took
about 9 minutes and produced mixed findings: one reproducible alias ambiguity,
alongside several claims that failed reproduction. Its output was treated as a
review lead, not authority. The resulting patch is prepared separately and was
not applied to the source checkout. These samples improve role evidence but do
not establish a reliability rate.

The one-shot status view now reports a bounded list/count of changed relative
paths and last change time during silent worker activity; it contains no file
contents. Forty-two offline tool tests passed after this change. Completed
worker panes were closed, leaving the supervisor pane only.

## Limits

- TTFT was unavailable in all baseline/context runs because no nonempty answer
  chunks were observed. Token throughput remains measurable, but useful answer
  latency and correctness do not. A single-token post-restore context run
  reported an impossible 1,000,000 tokens/s and is excluded.
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

Run a matched task-level 16K/65K comparison with visible structured answers,
independent correctness, and measured TTFT. The existing warm throughput
difference alone does not establish a useful optimization. Keep the rejected
prefix-cache probe deferred.

This repository is a reviewable research checkpoint, not a live monitoring
feed.
