# Local model behavior profiles

These observations come from local Hermes engineering tasks and inference
runs, not public benchmark scores. Evidence is limited; require supervision.

## Qwen3.5 9B Q4_K_M

- **Best role:** historical bounded coding fixtures with explicit independent
  contracts; 5/5 contracts passed in one five-task suite.
- **Weak role:** long, multi-requirement tool tasks without staged checkpoints.
  A probe task involved repeated edits, three context compactions, and ended
  with an implementation that failed independent offline acceptance.
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
- **Confidence:** moderate for old fixture suite, low for long tool-heavy work.

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
- **Confidence:** moderate for the historical five fixtures; low to moderate
  for this single supervised task.

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
- **Current boundary:** no evidence yet for debugging large systems,
  repositories, long-lived sessions, or multi-worker tasks. Keep assignments
  in clean, disposable workspaces and independently review all results.
- **Confidence:** low; two accepted small tasks establish feasibility, not a
  reliability rate.
