# Local model behavior profiles

These observations come from local Hermes engineering tasks and inference
runs, not public benchmark scores. Evidence is limited; require supervision.

## Qwen3.5 9B Q4_K_M

- **Best role:** historical bounded coding fixtures with explicit independent
  contracts; 5/5 contracts passed in one five-task suite.
- **Weak role:** long, multi-requirement tool tasks without staged checkpoints.
  A probe task involved repeated edits, three context compactions, and ended
  with an implementation that failed independent offline acceptance.
- **Additional sample:** a bounded interactive-shim task ran for about 50 seconds,
  changed the launcher, and exited 2 before acceptance. It omitted one existing
  local alias and made an unnecessary interpreter change. The supervisor
  corrected the two-file scope; four offline tests and two network-isolated
  manifest checks passed. This is an incomplete worker task, not autonomous
  completion.
- **Effective prompt pattern:** short, single-file tasks with one acceptance
  command and a supplied schema. The old suite supports explicit contracts and
  allowed-tool rules; no prompt ablation proves a Qwen-specific benefit.
- **Ineffective prompt:** the all-at-once probe assignment led to patch loops
  and a temporary Python-to-Markdown replacement. This is one task sample.
- **Task boundary:** one behavior per assignment; keep the script small and
  separate CLI, request protocol, and reporting changes.
- **Operational guidance:** inspect after three minutes without progress;
  checkpoint after two compactions; allow at most two corrections.
- **Tool restrictions:** enforce workspace writes outside the prompt layer;
  inspect logs for broad reads and editing outside the assignment.
- **Supervisor strategy:** confirm artifact changes at checkpoints and run
  mock acceptance independently; do not treat idle as completion.
- **Observed example:** 17m45s, 32 reported edits, 15 reads, 25 script/tool
  runs, one shell command, three context compactions; final probe rejected
  before live use.
- **Additional sample:** an automatically selected quick task added one
  discount helper and tests; all 16 project tests passed in 25.8 seconds with
  no correction. This does not remove the observed long-task failure.
- **Additional failure sample:** a bounded two-file tax-bucket feature ran for
  68 seconds and exited 2. Independent checks found wrong expected totals and
  rejection of valid list rows; the worker's attempted repair did not land.
  Supervisor corrections passed the fixture's 12 tests in the isolated
  acceptance runner. Count this as an incomplete worker task, not autonomous
  completion.
- **Confidence:** low for small supervised coding after mixed current samples;
  low for long, tool-heavy tasks. The evidence does not support a reliability
  percentage.
- **Recovery check:** a fresh mock recheck reproduced prefix disclosure,
  biased control order, and silent append in the probe. Do not use it live.
  This is additional evidence from the same tool assignment, not an independent
  new task sample.
- **Provisional boundary:** one behavior in one small file, one explicit
  acceptance command, and an early artifact checkpoint. Stop repeated parser
  or patch loops; the probe task does not establish a general model limitation.

## MiMo V2.6 9B Q4_K_M

- **Best role:** historical bounded bug fixes, small features, refactors, and
  debugging; 4/5 independent contracts passed.
- **Weak role:** tasks needing unprompted scope control and self-validation.
  The first summarizer had multiple defects and was not tested by the worker.
- **Effective prompt pattern:** provide the record schema, one synthetic
  fixture, output contract, and a small change boundary. No model-specific
  prompt ablation is available.
- **Ineffective prompt:** a long instruction to stay in the assigned directory
  did not prevent reading other lab files; it also did not lead to acceptance
  testing.
- **Task boundary:** one stdlib script plus concise documentation and synthetic
  data.
- **Operational guidance:** review after three minutes without progress; cap
  corrections at two. The implementation session lasted about 14 minutes.
- **Tool restrictions:** use an OS-level workspace boundary and disable
  unapproved persistent skill creation.
- **Supervisor strategy:** keep the initial worker version for comparison,
  inspect every output field, correct only bounded defects, and independently
  test.
- **Observed example:** worker wrote a summarizer and README, then honestly
  reported missing tests. Supervisor corrections passed synthetic and
  three-file aggregation checks. This is retry-assisted, not autonomous
  acceptance.
- **Additional sample:** automatic documentation routing selected MiMo for a
  bounded README task. Independent review corrected one inaccurate rounding
  statement; all 16 project tests and runnable examples then passed. The run's
  usage report omitted token counts despite successful chat responses.
- **Confidence:** moderate for the historical five fixtures; low to moderate
  for this single supervised task.
- **Recovery check:** the corrected summarizer passed a fresh synthetic check
  for median/null TTFT, cold/warm loads, empty responses, duplicate rejection,
  and no-clobber behavior. The worker's original was untested and needed
  material correction, so acceptance is retry-assisted.
- **Provisional boundary:** one schema-bound offline utility and a concise
  README, with an OS-enforced workspace limit. Require independent tests and
  count workspace excursions as a supervision risk.
- **Additional review sample:** MiMo spent about 9 minutes on a read-only code
  review and found a real ambiguity between multiple recognized aliases for
  one field. Several other findings were false or incomplete when reproduced.
  Assign MiMo review tasks as lead generation only; require direct source and
  test verification. Confidence remains low for code review.

In a later bounded task, MiMo on Node B drafted JSON progress output, then
reached
its iteration limit after 2m55s. Independent acceptance found nine failures;
supervisor corrections led to 34 passing tests. This is supervisor-assisted,
not autonomous completion. Primary token totals were unavailable.

## Gemma4 12B

A single bounded smoke task timed out without useful tool activity. This is not
enough evidence to characterize roles, prompting, or task boundaries.

## Qwen3.6 35B

- **Best role:** tightly bounded Python implementation with an exact task
  contract and independent acceptance command. Two small disposable tasks
  passed their independent test suites without correction.
- **Observed task:** a two-file batch API change completed in 79 seconds. The
  diff stayed within the allowed files and all 8 project tests passed.
- **Prompt pattern:** specify accepted input forms, reuse of existing
  validation, allowed files, required tests, and the final evidence to report.
- **Operational evidence:** one run made 8 inference API calls and used
  56.9K input and 2.2K output tokens. This high input-to-output ratio suggests
  reducing reusable prompt/context overhead before expanding task complexity.
- **Negative sample:** a validation-heavy status CLI task used 13 local requests
  (12 successful HTTP responses) over 7.4 minutes and produced an overlarge
  implementation/test draft. Independent checks found 32/47 tests failed; the
  draft was rejected. No usage totals were finalized. This is one task-boundary
  failure, not a reliability rate or backend failure.
- **Current boundary:** no evidence yet for debugging large systems,
  repositories, long-lived sessions, or multi-worker tasks. Keep assignments
  in clean, disposable workspaces, keep validation cases bounded, and
  independently review all results.
- **Confidence:** low; two accepted small tasks and one failed larger task do
  not establish a reliability rate.
- **Additional sample:** two isolated Actual CSV import tasks completed in
  97 seconds and 328 seconds. One added duplicate-header guards; one added
  mapping-column reuse and mode validation. Both passed independent acceptance
  in the final snapshot. The worker's second suite had redundant cases, which
  the supervisor reduced to focused tests. This supports tightly bounded
  implementation, not unsupervised integration.
- **Suggested limits:** one behavior per task, up to two named source/test
  files, explicit acceptance commands, and a three-minute no-progress review.
  Check artifact changes because terminal output may remain silent while work
  proceeds.


## Qwen3.8 27B Q4_K_M

- **Best role:** bounded multi-file coding with an exact test contract.
  Historical HADES tasks include a two-module change passing 7 tests in about
  117 seconds and a separate context-sensitive task passing 57 tests in about
  138 seconds.
- **Weak role:** an identical registry task once made no edit within its
  150-second cap. Longer local Hermes work is not yet characterized.
- **Effective prompt pattern:** name affected modules, tests, and syntax
  invariants. No prompt ablation is available.
- **Operational limit:** the model is large and currently excluded from
  automatic selection while unresident; automatic cold loading is disabled.
- **Confidence:** low to moderate for bounded coding in the historical HADES
  route; no independent local Hermes sample yet.

## Additional Qwen3.6 and Qwen3.5 evidence — 2026-11-15

Qwen3.6 completed a focused classifier change in 185 seconds. Its six worker
tests passed, but independent review found a “patch” noun regression. A narrow
supervisor correction and regression test passed the focused suite 7/7 and
combined 49-test lab suite. Count this as supervisor-assisted acceptance.

Qwen3.5's natural-language CLI attempt stopped after 163 seconds at the
12-turn cap with its acceptance pending. Review found incorrect subprocess
arguments and status/history handling in the partial implementation; it was
rejected and preserved without a rewrite. Token totals were unavailable.
Continue limiting assignments to one behavior with explicit fixtures and
early inspection.

In a later bounded task, Qwen3.6 on Node C drafted `history --json` for the
operator CLI, then reached its iteration limit after 6m28s before testing.
The supervisor repaired validation and fixture defects; 25 offline tests
passed. This is a supervisor-assisted result, not an autonomous success.
Primary token totals were unavailable.

The lab operator CLI later completed one small synthetic Qwen3.5 task in
about 29 seconds. Its acceptance manifest and an independent five-test project
run passed. Treat this as one bounded success; the model's broader tool-heavy
reliability remains low-confidence. Prefer one behavior in one source file,
explicit acceptance commands, changed-path inspection, and independent review.

## 2026-11-15 stalled CLI follow-up

A bounded Qwen3.6 CLI attempt produced three successful local completion
responses but no output or project change; it was interrupted after
281.9 seconds with acceptance pending. The cause is uncertain and does not
establish a reasoning failure. Keep the scope to one behavior with an early
artifact checkpoint and independent acceptance.

## Recovery sample updates — 2026-11-15

### Qwen3.5 9B

A bounded artifact-locator change on Node A failed independent acceptance after
an exit-2 run: 36 CLI tests produced 9 failures and 2 errors. The draft replaced
existing command behavior and used unsafe path containment. Luna implemented a
separate private-lab version and independently passed 69 tool tests and 33 CLI
tests; this is not worker credit. For now, assign one small behavior in one
file, state exact allowed paths and stdout/stderr/exit behavior, and inspect the
diff and focused test early. Confidence is low for filesystem-sensitive work
and multi-requirement autonomous changes.

### MiMo V2.6 9B

The worker produced an initial JSONL summarizer and README but explicitly left
testing unfinished. Supervisor-led synthetic acceptance passed after
correction, so classify this as retry-assisted. Delayed/truncated reporting and
reads beyond the assigned workspace were observed. Prefer schema-bound offline
utilities with a supplied fixture and command, and enforce workspace limits at
the OS layer. Confidence remains low to moderate for supervised, bounded data
work; workspace discipline and autonomous validation remain low-confidence.


## Additional bounded-task evidence — 2026-11-15

**Qwen3.6 35B:** a narrowly scoped local CLI-report feature completed in
185.6 seconds. Focused acceptance and the then-current CLI suite passed; the
supervisor added malformed-metadata guards, after which integrated CLI and
tool suites passed. Treat this as accepted with a small supervisor hardening
correction, with low-to-moderate confidence for this task size.

**MiMo V2.6 9B:** a context-evidence documentation task ran for 358.6 seconds
and made a single-file draft, but authoritative task status was exit 2 with
acceptance pending. Its final response claimed success, while review found
conflated preference/allocation evidence and treated missing measurements as
unsupported configurations. Keep this as a failed worker sample. Luna
corrected the private matrix and independently passed its fixture; that
correction is not worker completion. Prefer short, source-bound documentation
tasks with acceptance executed by the supervisor.

## Recovery observations

- **Qwen3.5 9B:** a bounded artifacts-JSON implementation failed independent
  CLI acceptance after 116 s. Syntax passed, but the focused suite had 7
  errors and 1 failure; the draft contained undefined status handling and a
  null-path helper defect. Keep near-term work to one small behavior, one
  file, and explicit acceptance; inspect early and avoid repeated rewrite
  prompts. Confidence remains low.
- **MiMo V2.6 9B:** its summarizer draft was not tested by the worker. The
  supervisor-corrected version passed synthetic offline reporting checks and
  is accepted for that scope only. This is retry-assisted evidence. Enforce
  filesystem boundaries and independently execute acceptance.
- **Qwen3.6 35B:** a nested process tree required process-group inspection for
  safe interruption. A short context comparison showed a small warm TTFT and
  decode improvement at requested 16K, but answer capture was only 11
  characters and resident context metadata lagged the request. No broad
  reliability or context-quality claim follows.
