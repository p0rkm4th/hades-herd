# Current status — 2026-11-07

The project is public at [p0rkm4th/hades-herd](https://github.com/p0rkm4th/hades-herd).
The initial source, tests, and sanitized evidence are on `main`; the HADES
workstation launcher now uses this checkout as its canonical source. The live
endpoint and digest evidence remain in local user configuration. Verification
of the migration is recorded below.

## Code-review fixes on review branch

On branch `codex-herd/review-launcher-context` based on reviewed `main` at
`19396a2`: clean-install launches now resolve and save an online default;
explicit model selection takes precedence over a saved default; Codex context
uses complete online-host `num_ctx` configuration when unloaded and otherwise
labels the safe fallback; profile/catalog files are atomic and isolated by
model; the launcher has a subprocess smoke test; and trace metadata counts
distinct same-name tool calls without persisting call IDs. The review-only
suite passed 19 tests; after adding trace-capture and CRLF regressions, the
current suite passes 27 tests, including a clean-home fake-Herd/fake-Codex
launch. GitHub Actions passed the full configured matrix on commit `5a90083`
in [run 42425964504](https://github.com/p0rkm4th/hades-herd/actions/runs/42425964504).
This branch is not yet merged or deployed, and no live Herd profile behavior
was changed. The installed Codex CLI 0.166.0 also accepted the hashed
model-specific profile against the deterministic loopback fixture and completed
the mock turn; see the [sanitized profile smoke result](../benchmarks/results/2026-11-07-real-codex-profile-smoke.md).

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
- An offline reconciliation of this run found 27 completed Codex
  `command_execution` events versus 21 Responses `function_call` items. The
  streams lack a shared correlation key, so six events remain unexplained;
  a timestamped metadata-only Codex event capture and proxy request/response
  timestamps are now implemented and tested. They have not yet been exercised
  in a live model run.
- The owner-provided model study is summarized in the [model matrix](MODEL_MATRIX.md).
  Published scores remain directional only; no offload experiment, model pull,
  hardware change, or production route/default change is planned during this
  reliability phase.
- No profile meets the 20 varied-task / 85% pass@1 daily-driver gate.
- The first GitHub Actions matrix run passed on Python 3.11–3.14 but failed on
  3.10 because the tests imported `tomllib`. The tests now decode the generated
  string field with the standard library; the follow-up
  [matrix run passed Python 3.10–3.14](https://github.com/p0rkm4th/hades-herd/actions/runs/42402317435).

## Current decision

Keep the deployed default unchanged. Use local profiles experimentally with
independent patch review. The immediate engineering work is protocol tracing,
inspection-loop diagnosis, runner validation, and a minimal controlled fix—not
adding models or changing production routes.

See [sanitized evidence](../benchmarks/results/2026-11-07-reliability-baseline.md)
and the [roadmap](ROADMAP.md).

## Latest held-out diagnostic — 2026-11-07

A fresh Qwen3.8 Q4/Nyx attempt on the trace call-count bug timed out at 180s
(exit 124) after four completed shell commands (three reads and one Python
command), but without a patch or completed Codex turn. This is incomplete
diagnostic evidence, excluded from model pass rates. It does not identify whether
the cause is model behavior, context/protocol handling, or agent workflow. Nyx was
unloaded and released; production Herd remained idle. See the [sanitized held-out
result](../benchmarks/results/2026-11-07-heldout-trace-count-task.md).
- A 2026-11-08 synthetic control verified the normal Codex Responses sequence:
  advertised `exec_command`, execution, tool result, then final turn. Both
  requests included the complete local tool catalog; the live trace's empty
  tool-list pattern was not reproduced. See the [control result]
  (../benchmarks/results/2026-11-07-real-codex-profile-smoke.md).

## Reasoning control diagnostic — 2026-11-08

A single same-task Qwen3.8 Q4/Nyx comparison with Codex `none` exited 124 after
seven shell-command executions, without a patch or completed turn. Ollama
reported about 734 generated tokens at ~9.4 tokens/s and 14,214/16,384 context
tokens; the Responses route saw no client-visible text/tool chunks before the
Codex process disconnected. The isolated adapter was configured to map
`none` to Ollama `think:false` when advertised, but the exact outbound JSON
during the real inference run was not captured. This does not establish whether that mapping helped. See the
[sanitized result](../benchmarks/results/2026-11-08-reasoning-none-diagnostic.md).
- A follow-up fresh-HOME, no-inference Codex transport control confirmed
  `reasoning.effort=none` becomes boolean `think:false` in the synthetic
  `/api/chat` request; Codex completed that mock turn. This verifies the mapping
  path, not the earlier model run or coding quality. Details are in the
  [reasoning diagnostic](../benchmarks/results/2026-11-08-reasoning-none-diagnostic.md).
- The November 7 source-review findings are covered on branch
  `codex-herd/review-launcher-context`: clean-install default selection,
  explicit-model precedence, unloaded configured-context reporting,
  end-to-end launcher smoke coverage, distinct same-name trace call counts,
  and atomic model-specific profiles. Latest local run on 2026-11-08:
  `python3 -m unittest discover -s tests -v` passed all 19 tests. GitHub Actions
  passed on commit `3802aee` in [run 42423933976](https://github.com/p0rkm4th/hades-herd/actions/runs/42423933976).
  PR creation was denied by the connected GitHub integration (403
  `Resource not accessible by integration`); use the
  [compare-and-create-PR page](https://github.com/p0rkm4th/hades-herd/compare/main...codex-herd/review-launcher-context?expand=1).
- The trace parser now accepts LF and CRLF SSE frames, including delimiters
  split across chunks. A bounded Codex/Herd smoke run completed but the agent's
  first patch regressed LF parsing and added invalid test expectations; human
  corrections were required, so this is not a model pass. The new timeline
  exactly reconciled 10 Responses `exec_command` calls with 10 Codex shell
  events in that run; all requests advertised tools, so the earlier empty-tool
  behavior remains unexplained. The corrected 27-test suite passes locally.
  See the [smoke report](../benchmarks/results/2026-11-08-codex-trace-crlf-smoke.md).
