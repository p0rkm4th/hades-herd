# Current status — 2026-11-09

## Security-model feasibility — 2026-11-09

Cyber-Ornith 1.5 9B OBLITERATED i1 Q4_K_M was imported from a pinned,
checksum-verified GGUF into an isolated loopback-only Ollama runtime. One
bounded benign tool-call cycle passed at 8K with 100% GPU residency and Q8_0
KV cache. This is not a security-capability benchmark and does not qualify a
`SECURITY-LAB` route; the model remains unregistered and isolated. Flash
Attention was requested in the runtime environment, but explicit backend
confirmation was unavailable. Follow-up synthetic checks exposed incomplete
answers, unsupported SSH claims, and invalid Sigma rules; Cyber-Ornith is not
qualified for security analysis. See the [feasibility report](../benchmarks/results/2026-11-09-security-lab-feasibility.md).

## Agent profile naming and context — 2026-11-09

Generated Codex catalogs now separate friendly HADES display labels from the
canonical Herd model slug and use the effective Codex context in the label.
The LONG role is assigned to Hecate MiMo 64K after a bounded tool-driven Codex
task completed and its independent tests passed. FAST/BALANCED/COMPLEX mappings
and the saved `qwen3.6:35b` default are unchanged.

Hecate's separate MiMo 64K alias is present in live Herd discovery and was
observed at 65,536 actual context, fully GPU resident (8,455 / 12,282 MiB
used). The Codex smoke completed in 41.27 s, first tool action in 3.44 s, with
9 tool calls and 17 independent tests passing. The prior Hermes JSONL fixture
also passed. This is limited evidence from one coding task, not a broad
reliability guarantee. See the [dated profile evaluation](../benchmarks/results/2026-11-09-agent-profile-context.md).

Hermes' active local aliases are `mimo-code` and compatibility
`hades-mimo-long`, both selecting the tested 64K backend. The 16K
`hades-mimo-fast` alias failed Hermes' pre-inference minimum-context check and
was removed. Hermes' saved default model/provider and empty fallback list were
not changed. The private infrastructure report records exact digests, live
fleet inventory, reversible changes, and the request-state discrepancy.

The project is public at [p0rkm4th/hades-herd](https://github.com/p0rkm4th/hades-herd).
The initial source, tests, and sanitized evidence are on `main`; the HADES
workstation launcher now uses this checkout as its canonical source. The live
endpoint and digest evidence remain in local user configuration. Verification
of the migration is recorded below.

The November 7 launcher review findings are fixed on the pushed branch
[`codex-herd/launcher-review-fixes`](https://github.com/p0rkm4th/hades-herd/compare/main...codex-herd/launcher-review-fixes?expand=1)
at `b774696`: fresh-install and explicit-model selection, configured context
metadata, atomic per-model profiles, clean-launch integration coverage, and
distinct trace-call counting. The 20-test Python 3.10–3.14 CI matrix passed.
A synchronized two-model profile-generation test now passes locally as well;
the full local suite is 21 tests, and GitHub Actions passed the Python
3.10–3.14 matrix in
[run 42452190590](https://github.com/p0rkm4th/hades-herd/actions/runs/42452190590).
The latest test and sanitized result are in the [concurrency check](../benchmarks/results/2026-11-08-concurrent-profile-generation.md).
These changes are not yet in `main`; the available GitHub integration returned
403 when asked to create a PR.

On 2026-11-08, `config show` was aligned with the generated Codex catalog when
duplicate model installations have different configured contexts. It now
reports the context source and warns when a saved Codex budget exceeds the
lowest known backend configuration, without presenting the model's advertised
maximum as allocated context. The tests also restore all module-global paths
after each temporary-home test. Commit `aceeef8` contains this fix; the full
local suite passes 22 tests and the Python 3.10–3.14 CI matrix passed.

A real Codex CLI 0.166.0 matched smoke then exercised both the fast and advanced
model profiles through Herd on the same disposable coding task. Both turns
completed, edited the requested source, passed five independent tests, and
returned a final response; approximate elapsed times were 8 seconds for MiMo
9B Q4 and 97 seconds for Qwen3.8 27B Q4. This verifies the launch paths, not
the Level A five-varied-task gate. See the [sanitized smoke result](../benchmarks/results/2026-11-08-supervised-codex-launch-smoke.md).
The installed Fish command also passed this repeated path check from a
disposable project directory; it preserved the saved default and is not a new
distinct task result.

The short Level A fast-profile campaign then attempted three distinct,
baseline-reproduced launcher bugs. MiMo produced no verified fix on the
first-run default or trace-count tasks; its context task timed out at 180s and
the independent regression still failed. Since 0/3 makes the 4/5 smoke target
unreachable, that campaign stopped. See the [Level A scorecard](../benchmarks/results/2026-11-08-level-a-fast-smoke.md).

A single controlled repeat of the first-run task added a supported Codex
developer-instructions value to the isolated model profile. It still timed out
at 180s after 35 shell calls; the partial patch violated stale-default and
explicit-selection invariants, and its new tests were not discovered. This
prompt intervention did not qualify as a pass or demonstrate a reliable gain.
The scorecard update passed Python 3.10–3.14 CI in
[run 42455432087](https://github.com/p0rkm4th/hades-herd/actions/runs/42455432087).

## Qwen3.8 64K timeout follow-up — 2026-11-09

A multi-step `codex-herd doctor` task stalled for five minutes on 64K and
returned Codex's SSE idle-timeout error. A same-task 32K comparison reduced
CPU offload but also failed to return a final response before its harness cap.
No crash or OOM was observed; available logs do not distinguish silent model
generation from Herd withholding SSE events. No timeout, routing, or default
change is justified. See the [sanitized investigation](../benchmarks/results/2026-11-09-qwen38-codex-idle-timeout.md).

## Local model coding reliability — 2026-11-09

The reproducible local-only fixture runner exercised MiMo 9B Q4 at a verified
16,384 context on four of five distinct task categories. Bug fix, feature,
multi-file, and log-driven debugging tasks completed with passing pytest and
independent checks; a behavior-preserving refactor passed pytest but missed the
required helper extraction contract. MiMo had 100% GPU residency, 2.3–4.7s to
first tool action, and 29–107s task time. This meets the scoped 4/5 target, not
the separate daily-driver gate. Qwen3.8 27B Q4 at 65,536 changed the smoke file
and passed its test but failed to complete a Codex turn by 180s; its measured
residency was 66.7% GPU / 33.3% CPU. The run did not distinguish slow offloaded
inference from model progress failure. See the [full scorecard](../benchmarks/results/local-model-reliability.md).

The CLI now supports local role mappings (`fast`, `balanced`, `complex`),
stored in deployment-local preferences. Each is mapped to the tested MiMo 16K
profile for bounded coding tasks. Role assignment does not change the saved
default; an unconfigured role errors without hosted fallback. The installed
Fish launcher passed real task runs and a role-selection integration test.
Existing Python tests pass 27/27. No Ollama/Herd configuration, route, alias,
or default changed.

## Works

- The dependency-free Python helper discovers a live Herd catalog and
  generates a dedicated Codex profile.
- Fish `codex-herd` supports exact model selection, per-model preferences,
  catalog refresh, and explicit errors for stale or unknown model names.
- The private HADES deployment was last observed with all seven backends online;
  this is point-in-time evidence, not a public service-health guarantee.
- On 2026-11-07, after migration to this checkout, `codex-herd list` discovered
  the live fleet with 7/7 nodes online, and `codex-herd qwen3.6:35b --help`
  forwarded to Codex without starting inference. The saved `qwen3.6:35b`
  default remained unchanged. These checks do not qualify it as a coding agent.
- MiMo-V2.6 9B Q4 completed HTTPie #1960's header-order fix and test through
  Codex/Herd in about 126 seconds. Independent verification passed 122 tests
  with 3 expected xfails. This is one successful task, not daily-driver proof.

## Not yet dependable

- MiMo and Qwen3.8 each timed out on the same bounded Rich #4250 task without
  edits; the Qwen run made two shell calls and generated near 11 tokens/s.
  These results point to an execution/progress problem on this task, not a
  general intelligence ranking.
- A one-variable MiMo retry added a two-command inspection cap and required an
  edit within those calls. It also timed out at 180 seconds, making 22 shell
  calls (21 unique; one repeated twice), with no edits. The focused baseline
  passed 15 tests. This prompt-only intervention did not resolve the issue;
  the fixture is retired from further retries. It is diagnostic evidence, not
  a model-quality score.
- Qwen3.8 has successful task-specific 8K registry and multi-file results, but
  many distinct 16K Codex attempts did not complete a full agent turn.
- Earlier traces include unsupported `read_file` attempts, repeated source
  inspection, patches without a final response, and test-fixture errors.
- A deterministic loopback test confirms Codex 0.166.0 rejects an unadvertised
  `read_file` call locally and reports the rejection on the next request. A
  corrected live Responses trace on HTTPie #1958 saw no `read_file` result or
  unsupported-call error, so the historical event's origin is still unproven.
  Herd's translator preserves unknown Ollama tool names unchanged. See the
  [sanitized evidence](../benchmarks/results/2026-11-07-reliability-baseline.md).
- Herd 0.12.3's no-inference translation check retained prior tool-call/result
  continuity and already adds turn-completion guidance when tools are offered.
  Repeated inspection therefore remains unexplained; truncation and model
  behavior still need a real-run trace.
- Codex reasoning controls are not yet demonstrated end-to-end through Herd's
  adapter. A controlled mock confirms Codex emits `reasoning.effort` only when
  the catalog advertises it and the profile selects it. A no-inference call to
  the installed Herd 0.12.3 Responses translator omitted both `reasoning` and
  `think` while retaining messages and tools. The actual downstream HTTP body
  was not intercepted; no client control is enabled. See the [sanitized
  evidence](../benchmarks/results/2026-11-07-reliability-baseline.md).
- Latest published diagnostic commit is `d17c55b`; CI passed the Python
  3.10–3.14 matrix and fixture syntax in
  [run 42408427998](https://github.com/p0rkm4th/hades-herd/actions/runs/42408427998).
- The loopback trace proxy passed a real bounded Codex/Herd run. It observed 30
  successful Responses calls before the 180-second timeout and 27 unique shell
  calls, with no code edits. Sixteen requests carried nine tool entries; 14
  carried an empty list, and five of those still returned `exec_command`. Full
  stateless input had 26 prior tool calls and 26 results; no `previous_response_id`
  appeared. This is an observed wire pattern, not a proven cause of the stall.
  The proxy's tests verify unchanged SSE forwarding and omit prompts, schemas,
  arguments, results, response text, IDs, and headers from the capture.
- The owner-provided model study is summarized in the [model matrix](MODEL_MATRIX.md).
  Published scores remain directional only; no offload experiment, model pull,
  hardware change, or production route/default change is planned during this
  reliability phase.
- No profile meets the 20 varied-task / 85% pass@1 daily-driver gate; the new
  MiMo 4/5 result is limited to five small deterministic fixtures.
- The first GitHub Actions matrix run passed on Python 3.11–3.14 but failed on
  3.10 because the tests imported `tomllib`. The tests now decode the generated
  string field with the standard library; the follow-up
  [matrix run passed Python 3.10–3.14](https://github.com/p0rkm4th/hades-herd/actions/runs/42402317435).

## Current decision

Keep the deployed default unchanged. MiMo 9B Q4 at 16K is the best tested local
profile for bounded, supervised coding; Qwen3.8 27B Q4 at 64K did not complete
the matched smoke within its limit. Earlier MiMo maintenance failures remain
valid limits outside the new fixture scope. Stop stalled or repetitive
sessions, verify the diff and tests, and use a hosted model only by an explicit
separate operator command.

See [sanitized evidence](../benchmarks/results/2026-11-07-reliability-baseline.md)
and the [roadmap](ROADMAP.md).


## Long-run harness reliability follow-up — 2026-11-09

Preserved Hermes and Codex-Herd JSONL implementations/tests separately outside
`/tmp`, and added an independent CLI acceptance fixture. Both self-authored
suites and the shared base CLI check pass. The separate valid timezone-offset
check passes Hermes but fails Codex (`+00:00` is counted as skipped), despite
Codex's 19/19 self-authored tests. Operator-observed long runs also recorded
approval timeouts/compaction for Hermes, and at least three compactions, many
failed corrections, budget overruns, and false no-compaction/no-error claims
for Codex. The 6.17M token checkpoint is cumulative consumption, not context
occupancy. The independent 41.27s Codex smoke remains a separate bounded result.
Neither harness is promoted as an unattended daily driver. See the
[scorecard](../benchmarks/results/2026-11-09-harness-longrun-scorecard.md).

An opt-in `scripts/codex_herd_supervisor.py` now enforces wall time, tool-call,
repetition, and consecutive tool-failure limits and stores a private recovery
checkpoint plus JSONL/stderr logs. A regression test confirms silent child
processes are terminated at the wall limit. Token enforcement depends on
usage events being reported by Codex; no production profile/default changed.

## MiMo 64K retrieval follow-up — 2026-11-09

An explicit Hermes `localherd` request using `hades-mimo-long` retrieved a
marker placed before 27,000 filler words and wrote it through the terminal
tool. It completed in 16.38 seconds and the output matched independently.
The backend allocated 65,536 context. The prompt's token count and tool-call
count were unavailable, so this validates a long-prompt/tool path, not full
64K saturation or a coding-role reliability claim. The first harness attempt
was rejected by the OS argument-size limit before inference; the bounded
27,000-word retry succeeded. See the [probe report](../benchmarks/results/2026-11-09-mimo-64k-long-context.md).

## Model naming cleanup — 2026-11-09

Generated Codex catalog labels no longer prepend `HADES` to every model; the
canonical model slug stays unchanged. Hermes now has the short `mimo-code`
alias pointing to the verified 64K MiMo profile. A smoke first confirmed
Hermes rejects the 16K model because v0.23.0 requires 64K, so the unsupported
`hades-mimo-fast` shortcut was removed. The prior `hades-mimo-long` alias is
retained. The corrected alias completed a local one-shot in 7.2 s. No saved
default or provider changed. See the private Hermes alias acceptance record.

## Matched Hermes coding profile comparison — 2026-11-09

A five-task local-only comparison completed through Hermes `localherd`: MiMo 9B 64K passed 4/5 (mean 36.7 s; one multi-file contract failure); Qwen3.5 9B 64K passed 5/5 independent checks (mean 105.9 s), although its debugging task used `execute_code` rather than the requested terminal tool, making strict terminal-only compliance 4/5. First-tool averages were 37.4 s and 106.6 s respectively. Usage token counts were unavailable. Neither qualifies for unsupervised daily use. MiMo is the faster candidate; Qwen3.5 is a slower opt-in candidate with better external fixture results. The saved default remains unchanged. See [sanitized evidence](../benchmarks/results/2026-11-09-hermes-qwen35-mimo-comparison.md).
