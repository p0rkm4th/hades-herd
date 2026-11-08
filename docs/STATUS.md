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
- The November 7 source-review fixes and trace-correlator unit tests are covered
  by 31 passing local tests. GitHub Actions passed the Python 3.10–3.14 matrix
  on code head `dc1ed234` in
  [run 42430116409](https://github.com/p0rkm4th/hades-herd/actions/runs/42430116409).
  The subsequent status-only commit `88530bc` also passed in
  [run 42430377369](https://github.com/p0rkm4th/hades-herd/actions/runs/42430377369).
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
  existing queue-manager warnings). No live coding task has tested the patch.
  A brief isolated-router startup showed that v0.12.3 still advertises over
  mDNS when bound to loopback; it was stopped before inference. Live validation
  needs discovery disabled or network isolation.
  Details:
  [guard prototype](../benchmarks/results/2026-11-08-herd-empty-tool-guard-prototype.md).
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

Next: run the same bounded failing coding task through a disposable guarded
adapter and an equivalent stock control, followed by one fresh held-out task.
Keep the adapter isolated and preserve equal model digest, context, task and
timeout. This protocol correction is now verified at the route boundary, but
its effect on real agent completion remains untested. Do not deploy it or
change production behavior based on synthetic output alone. Full sanitized
results and failed attempts are in
[`benchmarks/results/`](../benchmarks/results/).
