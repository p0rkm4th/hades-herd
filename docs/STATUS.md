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
- The test suite passes locally: 27 tests. GitHub Actions passed the Python
  3.10–3.14 matrix for code commit `5a90083` in
  [run 42425964504](https://github.com/p0rkm4th/hades-herd/actions/runs/42425964504).
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
- A deterministic import of the pinned Herd v0.12.3 translator reproduces a
  protocol mismatch: `tools: []` becomes an Ollama body with no `tools` field,
  but a synthetic Ollama `exec_command` call still becomes a Responses
  `function_call`. This is consistent with five tool-call outputs on tool-less
  requests in the HTTPie trace, but the live Ollama request/response body was
  not captured. No adapter patch or deployment was made. See the
  [source-level reproduction](../benchmarks/results/2026-11-08-herd-empty-tools-translator-repro.md).

## Decision and review handoff

Keep the deployed default and production routes unchanged. The tested changes
are on `codex-herd/review-launcher-context`, pushed but not merged or deployed.
Creating a draft PR through the connected GitHub integration returned 403
(`Resource not accessible by integration`); use the
[compare page](https://github.com/p0rkm4th/hades-herd/compare/main...codex-herd/review-launcher-context?expand=1).

Next: prepare and test a minimal explicit-empty-allowlist fix in a disposable
upstream checkout, including streaming and non-streaming cases. Only then use
timestamp-correlated live evidence on a distinct bounded task. Do not change
production behavior without that evidence. Full sanitized results and failed
attempts are in [`benchmarks/results/`](../benchmarks/results/).
