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
The first cohort panes were closed after their evidence was preserved.

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

## Recovery checkpoint — 2026-11-15

A bounded Qwen3.6 local CLI-report task completed in 185.6 seconds and passed
independent acceptance, with one small supervisor hardening change. A MiMo
context-documentation task ran 358.6 seconds but exited 2 with acceptance
pending; review found semantic errors despite its completion claim. The
supervisor corrected the private matrix and its independent fixture passed.
These are task-specific observations, not a model ranking. The remaining
worker pane was confirmed to be an idle shell and closed after its status and
artifacts were preserved.

The context comparison remains inconclusive: warm 16K medians showed 7.2%
lower TTFT and 8.0% higher decode than 65K, but the response capture was only
11 characters and resident-context metadata contradicted request options.
The next experiment is a full structured answer with verified effective
allocation and correctness checks. Keep 16K experimental; change no defaults.

## Limits

- TTFT was unavailable in the three-model baseline and original capped context
  comparison because those runs produced no nonempty answer chunks. A later
  short synthetic context follow-up did produce a visible sentinel; it still
  does not measure engineering-task quality. Token throughput remains
  measurable in the capped runs. A single-token post-restore context run
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

The visible-answer follow-up measured 7.2% lower warm TTFT and 8.0% higher
decode at requested 16K, but the runtime's resident-context report showed the
opposite setting. Memory and effective allocation for that follow-up are
therefore unverified. The earlier capped decode/allocation comparison remains
a separate microbenchmark. Run a matched task-level 16K/65K comparison only
after effective context and full response capture can be independently
verified. Keep the rejected prefix-cache probe deferred.

The private lab independently passed its operator CLI suite (40 tests) and
complete tool suite (74 tests) after narrow supervisor fixes for latest-task
status and sandbox reader-thread cancellation. These are lab-harness changes,
not delegated worker successes or production changes. Three additional local
worker attempts did not pass acceptance: Qwen3.5 produced malformed parser
code, MiMo left the CLI option unwired, and Qwen3.6 made no change before
interruption. A workspace-copy oversight also deprived the MiMo attempt of its
baseline tests. No worker remains active; all child panes were closed after
evidence and process state were checked.

Cancellation testing reproduced a reader-thread closed-pipe exception. The
lab fix passed the offline tool suite, including a cancellation-race case.
Herdr Ctrl+C and a signal to the sandbox parent did not stop a nested worker
process group in one run; after verifying exact task-owned processes, the
supervisor stopped that group and confirmed exit. Treat this as a lifecycle
gap to monitor, not a production incident.

This repository is a reviewable research checkpoint, not a live monitoring
feed.

## Bounded CLI dogfood checkpoint

The private lab's local operator CLI completed one synthetic Qwen3.5 task in
about 29 seconds. Its acceptance manifest passed, and an independent review
passed all five project tests. This is one narrow, supervised validation of
the operator path, not a general worker reliability estimate. No production
settings changed. Automatic continuation and end-to-end cancellation remain
unverified.

## 2026-11-15 supervised engineering checkpoint

A focused task-classifier update scanned the full bounded task contract rather
than only its first sentence. A local Qwen3.6 worker completed in 185 seconds;
independent review found and corrected a regression around “review this patch.”
The corrected focused suite passed 7/7, and the combined local tool suite now
passes 49 offline tests. A separate Qwen3.5 CLI assignment stopped at its
12-turn limit after 163 seconds; its acceptance did not run and review rejected
the partial implementation. Its workspace was preserved and no replacement
worker was launched.

Classifier intent remains heuristic; the new full-contract scan has a small
synthetic acceptance set and is not a general language-understanding result.

## 2026-11-15 worker recovery

Independent loopback-mock checks reconfirmed that the Qwen3.5 prefix probe
fails live-use acceptance: it leaks prefix text, uses biased control ordering,
and appends to an existing output file. It remains unused against a live model.
The corrected MiMo benchmark summarizer passed a fresh synthetic report check
and is accepted for offline JSONL summaries only; credit is supervisor-assisted.
A separate Qwen3.6 CLI follow-up made three successful local completion calls
but produced no output or project edits and was safely interrupted. Its cause
is unresolved, so it is recorded as incomplete rather than a model-quality
failure. See HERDR_FINDINGS.md and MODEL_PROFILES.md.

Ollama 0.40.15 source supports `draft_num_predict` handling, and the selected
Qwen3.6 model-derived options expose value 2. Draft/MTP artifact support and
effective behavior are still unverified; speculative decoding remains deferred.

## 2026-11-15 activity-observability recovery

Two additional local Hermes tasks were inspected rather than duplicated. A
MiMo CLI task timed out after five local completion responses and produced no
accepted edit. A Qwen3.6 status-activity task reached its iteration limit after
partial instrumentation; its viewer integration and acceptance remained
incomplete. Neither outcome establishes a general model-quality failure.

The supervisor completed the aggregate-only activity view in the isolated lab
harness. It reports local request counts and last-request age separately from
productive output age, so inference activity cannot mask a stalled task. The
updated offline suite passes 55 tests. This is a private orchestration-tool
improvement; it does not change production inference routing or settings.

The earlier Qwen3.6 16K/65K comparison emitted no visible answer text. A later
synthetic sentinel comparison measured visible TTFT and exact output at both
contexts but did not test engineering-task quality. Colibri is a documented
upstream Qwen3.6 candidate, but no HADES runtime or artifact compatibility
test has been performed.

## Verified visible-answer and operator CLI checkpoint

A synthetic fixed-answer follow-up produced the expected output at both 16K
and 65K. Warm 16K TTFT and client time were about 7% lower, generation was 8%
faster, and runner allocation was 2.2% lower. Context reallocation cost about
17.3 seconds, and the comparison used only two warm samples per setting in a
non-counterbalanced order. Keep this experimental; task-level correctness and
engineering benefit remain unmeasured.

The private operator tooling now exposes sanitized JSON history and progress
views. Independent isolated suites passed after supervisor corrections: 25
history tests and 34 status-viewer tests. Both workers reached iteration
limits before acceptance, so these are supervisor-assisted results. The
combined private tool and CLI suites now pass 69 and 33 tests. Next: compare
the same independently accepted engineering task at 16K/65K.

## 2026-11-15 recovery checkpoint

The worker-tool verdicts are now independently reconciled: the Qwen3.5 prefix
probe fails live-use acceptance and remains unused; the corrected MiMo JSONL
summarizer passes its offline reporting scope with supervisor assistance. A
later Qwen3.5 artifact-locator draft also failed independent CLI tests; Luna
implemented and validated a separate private-lab version (69 tool tests, 33
CLI tests). A Qwen3.6 cancellation assignment produced no output or edits and
was safely interrupted; its cause remains unresolved. No child pane remains
open.

The original capped context microbenchmark had no visible output and cannot
support TTFT claims. A separate short synthetic answer passed 3/3 at both 16K
and 65K; warm TTFT/decode gains were 7.2%/8.0%, with two warm samples per tier
and about 17.3 seconds to switch contexts. This is not engineering-task quality
evidence. Keep 16K experimental and the next optimization is a matched,
independently checked engineering task at both sizes. No production setting
changed.


## Recovery checkpoint update — 2026-11-15

Independent offline acceptance classified the Qwen3.5 prefix-cache probe as
failed for live use and the MiMo JSONL summarizer as accepted for offline
reporting after supervisor correction. A later Qwen3.5 CLI draft failed its
independent suite. A Qwen3.6 cancellation task produced no output or edits;
its nested process tree required process-group inspection and interruption. No
worker remained running after cleanup.

A follow-up short-answer comparison emitted an expected marker in all three
runs at each context setting. Warm 16K medians were 3.653 s TTFT and 53.94
tok/s; warm 65K medians were 3.938 s and 49.96 tok/s. The response capture was
only 11 characters, and resident-context metadata reflected the prior setting.
Treat the result as inconclusive; full answer correctness and effective
allocation remain unverified. No production settings changed.

## 2026-11-15 context-quality follow-up

A matched synthetic aggregation returned valid JSON at both 16K and 65K, but
both outputs failed the same checksum and four category totals. This gives no
evidence that larger context improves correctness, and the runs were not a
valid latency comparison. The earlier small-sentinel throughput result remains
experimental and does not establish useful-task performance. No production
settings changed. Next: qualify isolated-runtime support for KV-cache and
Flash Attention experiments, and revisit prefix reuse only after its probe
passes offline acceptance.

## Prefix-reuse assay checkpoint — 2026-11-15

A new offline-accepted probe completed eight requests on Qwen3.6 35B at
65,536 context. Its whole-run gate rejected one control with a one-token
prompt-count mismatch. A post-hoc matched subset (three warm shared-prefix
requests versus three controls) showed 42.4% lower median prefill, 41.0% lower
TTFT, and 39.5% lower client elapsed. This is a single-run indirect reuse
signal, not an accepted optimization: there is no explicit cache-hit counter
and the short marker does not establish task correctness. Exact digest and
65K allocation were checked before and after; no service setting changed.

The existing structured context workload failed the same five aggregate
checks at both requested context sizes, so it provides no evidence of a
context-quality benefit. Next: read-only Colibri artifact/toolchain
qualification; no build, import, download, or launch until compatibility and
an isolated reversible plan are established. If that gate fails, prepare a
replicated, token-matched prefix-reuse experiment with an independent
correctness check. No worker remains active.

## Operator wait command — 2026-11-15

The local lab CLI now provides `hades-agent wait TASK_ID` (or `--latest`) for
bounded waiting on a task record. It prints a redacted terminal summary,
returns a distinct timeout code, and never cancels work on timeout. Independent
networkless acceptance passed 78 CLI tests plus syntax and help checks. The
Qwen3.6 worker drafted the feature but reached its turn cap before acceptance;
Luna corrected test fixtures, added timeout/state guards, and independently
validated it. Count this as supervisor-assisted usability work, not autonomous
worker completion. A separate Qwen3.5 report enhancement did not pass
acceptance and was not integrated.

## Redacted acceptance summaries — 2026-11-15

The local operator report now shows passed/total independent acceptance checks
when its status artifact is valid and belongs to the task workspace. Missing,
malformed, symlinked, or out-of-scope artifacts are reported as unavailable;
paths and logs are never printed. A networkless acceptance snapshot passed 84
CLI tests plus syntax and help checks. The worker drafts were incomplete, so
this is supervisor-completed usability work, not autonomous worker completion.

## Prefix-reuse rerun disposition — 2026-11-15

A second eight-request run reused the first run's exact controls. All visible
markers passed and the exact model/context remained resident, but one control
again differed by one prompt token and the run exited 2. The matched subset
showed controls at about 80 ms prefill versus about 1.75 s for shared-prefix
requests. This is not a valid A/B result: the controls had already been
submitted and were not fresh. The initial cache signal remains experimental
and unconfirmed. Any follow-up needs novel per-run synthetic content and exact
token-matched samples. No production setting changed.
