# Current status — 2026-11-07

The project is public at [p0rkm4th/hades-herd](https://github.com/p0rkm4th/hades-herd).
The initial source, tests, and sanitized evidence are on `main`; the HADES
workstation launcher now uses this checkout as its canonical source. The live
endpoint and digest evidence remain in local user configuration. Verification
of the migration is recorded below.

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
- On 2026-11-07, read-only live `/api/show` checks on the MiMo 9B Hecate alias
  returned `think` values `[false, true]` (default `true`); Qwen3.8 27B on Nyx
  returned `[false, low, medium, xhigh]` (default `medium`). `codex-herd
  config show` now displays these backend-advertised values per node while
  keeping Codex's selectable reasoning levels empty: Herd still drops
  `reasoning.effort`, so exposing a selector would imply a control that does
  not work. Ollama documents that values are model-specific and unsupported
  names silently resolve to the model default, so forwarding must be validated
  against the chosen backend. See the [Ollama thinking API](https://github.com/ollama/ollama/blob/main/docs/capabilities/thinking.mdx).
- An isolated, un-deployed Herd 0.12.3 patch carries explicit Codex effort
  through translation, checks the selected backend's `/api/show`, and forwards
  only an exact advertised string as Ollama `think`; unsupported requests fail
  visibly. The upstream full suite passed 1,994 tests (5 skipped), with 99
  focused tests passing. Source Ruff/format checks passed. A bounded live check
  through the patched in-process router verified `reasoning.effort: "low"`
  became `think: "low"` on Nyx `/api/chat`; the Responses stream completed in
  9.92 seconds. The model was unloaded and the fleet returned idle. This is
  control-path evidence, not a coding-quality result. The patch is not deployed
  and the client catalog still advertises no effort levels. The same check
  exposed an output-cap gap: Responses `max_output_tokens` becomes top-level
  `max_tokens`, not Ollama `options.num_predict`. The isolated patch now maps
  that field and has a regression test; the full upstream suite passes 1,994
  tests (5 skipped). A follow-up live body capture verified the patched route
  sent `options.num_predict: 64` with `think: "low"`; it completed in 9.18
  seconds and the node returned to idle. The earlier pre-fix request did not
  carry the cap. This confirms request serialization, not coding quality or
  daily-driver behavior. See the [patch review notes](../patches/README.md).
- `main` remains at `19396a2`. The review branch
  `codex-herd/show-thinking-controls` contains the capability display, tested
  upstream adapter patch, and MIT notice. The adapter-artifact commit `c4aca60`
  passed Python 3.10–3.14 CI in [run 42410262261](https://github.com/p0rkm4th/hades-herd/actions/runs/42410262261).
  The output-cap patch commit `b11fbb6` passed CI in
  [run 42411900091](https://github.com/p0rkm4th/hades-herd/actions/runs/42411900091);
  live-check documentation commit `981c81b` passed in
  [run 42412085746](https://github.com/p0rkm4th/hades-herd/actions/runs/42412085746).
  A pull request has not been opened: the connected GitHub integration returned
  HTTP 403 when asked to create it. The [branch comparison](https://github.com/p0rkm4th/hades-herd/compare/main...codex-herd/show-thinking-controls?expand=1)
  is public for review.
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
- A no-inference preflight with Codex CLI 0.166.0 loaded a temporary custom
  Responses provider and model catalog with structured
  `supported_reasoning_levels` entries (`effort` plus `description`).
  `codex debug models` exposed the entries, and two requests to the local
  synthetic mock carried `reasoning.effort: low` and completed the mock turn.
  This validates catalog parsing and request serialization only; the
  interactive `/model` picker and backend inference remain unverified. No
  production profile or catalog was changed. The earlier plain-string catalog
  attempt was invalid and is not evidence against the supported schema.
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
