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
- Investigation of the logged `web_search` drop found it is intentional in
  Herd 0.12.3: hosted search/file/MCP tools have no Ollama implementation and
  are removed with a warning. The default Codex `functions` namespace is
  expanded, and ordinary callable tools and basic call/result history are
  translated. This does not explain the historical `read_file` event; see the
  [tool-filtering evidence](../benchmarks/results/2026-11-07-responses-tool-filtering.md).
- A deterministic loopback check with Codex CLI 0.166.0 completed one valid
  advertised `exec_command` call, returned its matching tool result on the next
  request, and completed the turn. The paired invalid `read_file` case produced
  an unsupported-call result instead. This isolates Codex client behavior, not
  Herd or model behavior; see the
  [round-trip evidence](../benchmarks/results/2026-11-07-codex-tool-roundtrip.md);
  the 15-test local suite and [Python 3.10–3.14 CI](https://github.com/p0rkm4th/hades-herd/actions/runs/42416133189) passed.
- Herd 0.12.3's no-inference translation check retained prior tool-call/result
  continuity and already adds turn-completion guidance when tools are offered.
  Repeated inspection therefore remains unexplained; truncation and model
  behavior still need a real-run trace.
- An un-deployed Herd 0.12.3 patch now validates `reasoning.effort` against the
  selected model's `/api/show` values and maps it to Ollama `think`; it also
  maps Responses `max_output_tokens` to Ollama `options.num_predict`. Full
  upstream tests passed (1,994 passed, 5 skipped), and an isolated live-body
  capture verified both fields. Codex 0.166.0 accepted structured effort
  catalog entries and emitted `low` to a local mock. In one matched coding-task
  pair, stock Herd timed out after a patch without a final turn; the patched
  route completed and its patch passed the full client suite (18/18). This is
  one stochastic task pair, not causal or general reliability proof. The
  adapter patch is not deployed, dynamic client catalogs still advertise no
  efforts, and the interactive `/model` picker is not validated. See the
  [paired task evidence](../benchmarks/results/2026-11-07-adapter-coding-task-pair.md)
  and the
  [patch review artifact](https://github.com/p0rkm4th/hades-herd/blob/codex-herd/show-thinking-controls/patches/ollama-herd-v0.12.3-reasoning-effort.patch).
- The client now rejects non-root paths in `CODEX_HERD_URL`, consistent with
  its documented origin contract. A disposable Codex task produced the fix and
  tests; the stock route timed out, while the patched route completed. Details
  are in the paired task evidence above.
- The earlier sanitized trace-parser commit `d17c55b` passed the Python
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

Keep the deployed default unchanged. Use local profiles experimentally with
independent patch review. Next, investigate the dropped `web_search` tool
metadata and repeat the reasoning-control task only if it will distinguish
adapter behavior from inference variance. Inspection loops and final-turn
stalls remain unresolved; no production router or Codex catalog change is
planned until the adapter patch has independent review.

See [sanitized evidence](../benchmarks/results/2026-11-07-reliability-baseline.md)
and the [roadmap](ROADMAP.md).
