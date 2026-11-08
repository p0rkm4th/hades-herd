# Current status — 2026-11-08

`p0rkm4th/hades-herd` is the public source of truth for the `codex-herd`
client. Its launcher, tests, sanitized diagnostics, and review history are
published here; private HADES infrastructure and endpoint details remain
outside this repository. See the [operator guide](OPERATOR_GUIDE.md) and
[roadmap](ROADMAP.md).

## What works

- The dependency-free Python client discovers live Herd models, creates
  model-isolated Codex profiles, and does not pull models or fall back to
  hosted inference.
- The review branch fixes fresh-install default selection, explicit-model
  precedence, unloaded context reporting, atomic profile generation, and
  repeated same-name trace counts. It adds a fake-Herd/fake-Codex launch test.
- The November 7 source-review fixes, trace-correlator unit tests, and current
  sanitized-report changes were covered by 35 passing tests. GitHub Actions
  passed the Python 3.10–3.14 matrix on code head `41853c3` in
  [run 42438683194](https://github.com/p0rkm4th/hades-herd/actions/runs/42438683194).
- The content/thinking-shape observer update and sanitized follow-up reports
  are covered by **36 passing local tests**, including streamed and
  non-streamed privacy checks. GitHub Actions passed the Python 3.10–3.14
  matrix on `6c723cd` in
  [run 42440081315](https://github.com/p0rkm4th/hades-herd/actions/runs/42440081315).
- A bounded Codex/Herd smoke exercised LF/CRLF trace framing. The initial
  model patch needed human correction; the resulting 27-test suite passed and
  the trace reconciled 10 Responses tool calls with 10 Codex command events.
  It is not a model-quality pass. Details: [trace smoke](../benchmarks/results/2026-11-08-codex-trace-crlf-smoke.md).

## What remains unreliable

- No model has passed the 20 varied-task / 85% first-attempt daily-driver gate.
- In the 19:42 HTTPie #1958 wire-trace run, 14 of 30 `/v1/responses` requests
  explicitly sent `tools: []`; five responses still contained `exec_command`.
  A separate 15:50 no-proxy attempt on the same task logged two unsupported
  `read_file` calls. The trace run did not contain `read_file`, so the two
  observations are not correlated.
  A separate run reconciled 10 tool calls exactly, and every `/v1/responses`
  request carried its tool catalog. That run does not explain the earlier
  empty-tool behavior or six-event discrepancy. See the
  [sanitized baseline](../benchmarks/results/2026-11-07-reliability-baseline.md).
- Repeated inspection, long completion times, and patch-without-final-turn
  failures remain unresolved. Codex reasoning-effort mapping through the live
  Herd adapter is not verified end to end.
- A separate stock-adapter protocol control completed a synthetic bug-fix task
  in 81.7 seconds: 16 Responses requests all carried the same 13-name tool
  catalog, and all 12 final tests passed. It did not reproduce empty-tool
  requests, so it is excluded from model scores and does not validate the guard.
  See the
  [control report](../benchmarks/results/2026-11-08-full-tools-protocol-control.md).
- The 14 historical empty-tool requests all included prior tool call/results
  and used 2.5K–5.5K input tokens. The control retained tools with 15 prior
  calls and 13.6K tokens. This argues against context exhaustion or tool history
  alone; the request-state cause and six-event count mismatch remain unknown.
  See the
  [request-shape analysis](../benchmarks/results/2026-11-08-empty-tools-request-shape.md).
- A deterministic import of the pinned Herd v0.12.3 translator reproduces a
  protocol mismatch: `tools: []` becomes an Ollama body with no `tools` field,
  but a synthetic Ollama `exec_command` call still becomes a Responses
  `function_call`. This is consistent with five tool-call outputs on tool-less
  requests in the HTTPie trace, but the live Ollama request/response body was
  not captured. No adapter patch or deployment was made. See the
  [source-level reproduction](../benchmarks/results/2026-11-08-herd-empty-tools-translator-repro.md).
- A sanitized trace correlator now joins Responses request metadata to
  timestamped Codex command-event windows. It rejects historical unstamped
  traces and marks overlapping requests unassigned instead of inferring a
  correlation. A live HTTPie #1978 diagnostic exercised it: two requests had
  empty tool lists, neither returned a function call, and two of 29 command
  starts were outside assignable response windows. The Codex run timed out
  without edits; this is not a model score. See the
  [live correlation report](../benchmarks/results/2026-11-08-httpie-1978-trace-correlation.md).
- A disposable guard prototype distinguishes explicit-empty from unknown
  offered-tool metadata and suppresses unadvertised calls in streamed and
  non-streamed results. Its translator tests pass 61/61; two mocked-Ollama
  route cases and the full upstream suite pass (1,992 passed, 5 skipped, 3
  existing queue-manager warnings). A live guarded attempt on HTTPie #1958
  timed out at 180 seconds without a final Codex turn; its independent tests
  had 4 failures. Three empty-tool requests returned message-only Responses,
  but the metadata trace cannot prove whether the guard synthesized them.
  The stock and guarded runs both failed and had different request mixes, so
  no autonomy improvement is established. Keep the patch unapplied.
  See the [prototype](../benchmarks/results/2026-11-08-herd-empty-tool-guard-prototype.md)
  and [live attempt](../benchmarks/results/2026-11-08-guarded-httpie-1958-live-task.md).
- A new loopback-only Ollama metadata proxy forwards payload bytes unchanged
  and records only model/tool names and counts, token counters, response status,
  content/thinking presence and character counts, completion reason, and
  timing. Its offline tests verify streamed forwarding, missing-versus-empty
  tool metadata, and exclusion of prompt/schema/argument/content/thinking
  sentinels. In held-out HTTPie #1965, the
  content-free Codex and Ollama traces both show the model requested an
  unadvertised `read` tool after two shell inspections; guarded Herd suppressed
  it and returned a notice, after which Codex ended without edits. The valid
  live attempt is a failure, not a model pass; no loss of a Codex-offered tool
  was observed. The route separately logged a dropped `web_search` entry that
  Ollama's chat format cannot represent. See the
  [held-out report](../benchmarks/results/2026-11-08-heldout-httpie-1965-live-attempt.md)
  and [benchmark instructions](../benchmarks/README.md#ollama-side-metadata-capture).
- A same-task follow-up added only per-model developer instructions telling
  Codex to use the listed shell tools. The model made no tool call, but Codex
  completed with no visible response and no repository change. The task did not
  improve; because the previous observer omitted text/thinking shape, its
  cause remains unknown. A metadata-only observer enhancement now records
  presence and character counts for those fields without retaining content.
  See the
  [follow-up report](../benchmarks/results/2026-11-08-guided-httpie-1965-followup.md).
- One same-input diagnostic with that enhanced observer then timed out at 180s
  after 17 completed Codex Responses turns, all issuing `exec_command`, with no
  source edits. Ollama returned 18 tool calls; all 18 responses had zero
  content characters, 13 carried a `thinking` field, and total thinking text
  length was 44,418 characters. The 18th backend request completed about 25s
  after Codex was killed, so its result had no client turn. This is evidence
  of an inspection loop, not proof that thinking caused it. Next, test
  thinking-only continuation and client-disconnect cancellation with
  deterministic fixtures. See the
  [response-shape report](../benchmarks/results/2026-11-08-guided-httpie-1965-response-shape.md).
- A loopback Codex boundary probe ran the installed CLI 0.166.0 against a
  synthetic endpoint. When the mock returned `exec_command` despite a simulated
  zero-tool backend offer, Codex executed it; when the mock returned visible
  no-tool text, Codex ran no command. Both sessions exited 0. Codex's own
  requests still advertised nine tools, so this does not reproduce the
  historical incoming `tools: []` request or validate a live Herd guard.
  Details and reproduction:
  [boundary probe](../benchmarks/results/2026-11-08-empty-tools-codex-boundary-probe.md).
- The explicit-empty mismatch was then reproduced through the complete
  in-process Herd `/v1/responses` route, queue, streaming proxy, and fake Ollama
  `/api/chat` transport on unmodified v0.12.3. In both streaming modes, stock
  Herd passed through a synthetic `exec_command` despite sending no tools to
  Ollama; the guard patch returned a visible message and no function call.
  All four paired route cases returned HTTP 200. This confirms the adapter
  mismatch and guard behavior, but does not show that it caused the historical
  agent task failure. The patch is public for review and remains unapplied.
  See the [paired report](../benchmarks/results/2026-11-08-herd-empty-tools-route-paired.md)
  and [patch notes](../benchmarks/fixtures/patches/README.md).
- A deterministic route probe shows that pinned Herd v0.12.3 turns an Ollama
  completion with empty content/tool calls and non-empty `thinking` into HTTP
  200 with a completed Responses object and `output: []` in both stream modes;
  the thinking text is not exposed. A local trace-proxy test also confirms
  downstream EOF now closes its upstream stream and records a content-free
  disconnect summary. A separate in-process v0.12.3 route test confirms client
  disconnect cancels the mocked backend stream and releases its queue slot;
  actual Ollama generation stop remains unverified. Codex CLI 0.166.0 treats that completed empty output as
  a successful blank turn (zero usage and no follow-up request) against a
  deterministic loopback mock. This makes the response shape a plausible blank
  turn mechanism; the earlier live 231-token response was not captured well
  enough to connect it. A disposable v0.12.3 candidate patch turns empty
  completions into explicit failures; Codex surfaces the error and exits 1
  instead of silently finishing. It does not retry, remains unsubmitted and
  unapplied ([candidate patch notes](../benchmarks/fixtures/patches/README.md)),
  and does not demonstrate improved task success. Herd route
  cancellation is verified against a mock transport; actual Ollama generation
  stop remains unverified.
  Details: [thinking-only and disconnect probes](../benchmarks/results/2026-11-08-thinking-only-and-disconnect-probes.md).
- The expanded offline public-repository test suite now passes **37 tests**;
  the pinned upstream Herd route probe separately passes **3/3**.

## Decision and review handoff

Keep the deployed default and production routes unchanged. The tested changes
are on `codex-herd/review-launcher-context`, pushed but not merged or deployed.
Creating a draft PR through the connected GitHub integration returned 403
(`Resource not accessible by integration`); use the
[compare page](https://github.com/p0rkm4th/hades-herd/compare/main...codex-herd/review-launcher-context?expand=1).

The November 7 independent review's five code findings are addressed on this
branch: clean-install/explicit model precedence, configured-versus-live context
metadata, full fake-endpoint launcher integration coverage, repeated same-name
tool-call counts, and atomic model-specific generated profiles. The branch has
passing CI, but a draft PR could not be created because the GitHub integration
returns 403 for PR creation; no open PR exists as of 2026-11-08.

Next: test tool-result continuity and final-turn handling. Separately verify
cancellation in Herd's actual route; the trace-proxy result is not evidence of
backend cancellation. Do not repeat HTTPie #1958, rerun #1965 without a new
hypothesis, or deploy the guard based on these incomplete tasks. Full sanitized results and failed attempts are in
[`benchmarks/results/`](../benchmarks/results/).
