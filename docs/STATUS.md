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
- The November 7 source-review fixes are covered by regression tests: 27 tests
  pass locally. GitHub Actions passed the Python 3.10–3.14 matrix on current
  head `dc1ed234` in
  [run 42430116409](https://github.com/p0rkm4th/hades-herd/actions/runs/42430116409).
- A bounded Codex/Herd smoke exercised LF/CRLF trace framing. The initial
  model patch needed human correction; the resulting 27-test suite passed and
  the trace reconciled 10 Responses tool calls with 10 Codex command events.
  It is not a model-quality pass. Details: [trace smoke](../benchmarks/results/2026-11-08-codex-trace-crlf-smoke.md).

## What remains unreliable

- No model has passed the 20 varied-task / 85% first-attempt daily-driver gate.
- In the earlier HTTPie #1958 stall, 14 of 30 `/v1/responses` requests
  explicitly sent `tools: []`; five responses still contained `exec_command`.
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

Next: identify why the stalled HTTPie task produced a different Codex request
shape after tool results. The pattern is not explained by context exhaustion
or prior tool history alone. Do not promote the adapter guard or change
production behavior without a relevant reproduced case. Full sanitized results
and failed attempts are in
[`benchmarks/results/`](../benchmarks/results/).
