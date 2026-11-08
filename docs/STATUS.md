# Current status — 2026-11-08

The project is public at [p0rkm4th/hades-herd](https://github.com/p0rkm4th/hades-herd).
The initial source, tests, and sanitized evidence are on `main`; the HADES
workstation launcher now uses this checkout as its canonical source. The live
endpoint and digest evidence remain in local user configuration. Verification
of the migration is recorded below.

The 2026-11-07 independent review's launcher and trace findings are implemented
on `codex-herd/review-fix-only`; that branch has its own passing CI run but is
not yet merged to `main`. A follow-up branch adds content-free schema-shape
capture to both the Codex-facing and Ollama-facing trace fixtures, so a paired
diagnosis can compare tool definitions across the adapter boundary. Its
offline tests pass; no live model run has used this instrumentation yet.

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
- Addressed the 2026-11-07 source review: first-run `codex-herd` now selects and
  saves the initial default only when launching implicitly; explicit model
  selection overrides stale defaults without changing the saved preference.
  Unloaded catalog entries use Ollama model `num_ctx` when available, distinguish
  that configured value from observed loaded allocation, and validate saved
  context overrides. Generated profiles use atomic replacement, and per-model
  developer instructions are sent as launch-specific Codex overrides.
- Added a clean-home subprocess test using a mock Herd API and fake Codex binary.
  It checks implicit/explicit selection, 16K context metadata, argument
  forwarding, and Codex exit status. Trace collection now preserves same-name
  tool-call counts/order while omitting IDs and arguments. The 23-test suite
  passed locally and across Python 3.10–3.14 in
  [GitHub Actions run 42443450209](https://github.com/p0rkm4th/hades-herd/actions/runs/42443450209).
  See the [review-fix evidence](../benchmarks/results/2026-11-08-code-review-fixes.md).
- The paired trace fixtures summarize bounded tool schema structure on both
  sides of the Herd adapter: property names/types, required keys, and
  structural limits only. Descriptions, defaults, enum/example values, prompts,
  arguments, and full schemas are omitted. This provides a way to test whether
  tool definitions differ across the boundary; it does not yet prove that
  schema translation caused the empty-tool-list observations. The updated
  offline suite passes 32 tests, including loopback forwarding, privacy, and
  recursion/size limits.
- A separate installed-Codex 0.166.0 smoke used an isolated home and loopback
  mock Herd, with hosted API-key/base-URL variables removed. The mock observed
  a synthetic model-specific developer-instruction marker in the actual
  Responses request; Codex completed against the mock. This validates config
  delivery, not model behavior or inference.
- A bounded direct Ollama streaming check returned to an unloaded baseline
  within 0.09 seconds after the client closed its stream; the fleet stayed idle.
  This supports prompt disconnect cleanup but does not prove server-side
  cancellation mechanics or agent recovery. No response text was retained. See
  [cancellation evidence](../benchmarks/results/2026-11-08-ollama-stream-cancellation.md).

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
- No profile meets the 20 varied-task / 85% pass@1 daily-driver gate.
- The first GitHub Actions matrix run passed on Python 3.11–3.14 but failed on
  3.10 because the tests imported `tomllib`. The tests now decode the generated
  string field with the standard library; the follow-up
  [matrix run passed Python 3.10–3.14](https://github.com/p0rkm4th/hades-herd/actions/runs/42402317435).

## Current decision

Keep the deployed default unchanged. Launcher and trace-parser review findings
are fixed in a focused branch; local tests pass. These client fixes do not
resolve model inspection loops, final-turn stalls, or the unexplained empty-tool
list trace. Continue protocol investigation against that evidence before
changing agent behavior or starting another broad model campaign.

See [sanitized evidence](../benchmarks/results/2026-11-07-reliability-baseline.md)
and the [roadmap](ROADMAP.md).
