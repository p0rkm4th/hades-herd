# Roadmap

## Immediate: diagnose reliability

1. Address source-review findings before collecting more model scores. A
   focused branch now fixes clean-install/default precedence, configured versus
   loaded context metadata, launcher subprocess coverage, repeated call
   counting, and atomic model-isolated profile generation. The 3.10–3.14 CI
   matrix passed; independent PR review is pending.
2. Capture sanitized Codex request/response metadata and identify the exact
   advertised tool list, attempted tool name, Herd translation, execution
   result, and tool-result continuation. **Partial evidence:** one live
   HTTPie #1958 trace captured the Codex↔Herd boundary; it did not reproduce a
   `read_file` call, but did show that some requests carried an empty tools
   array while the full stateless input included prior calls/results. This
   narrows the wire behavior but does not explain the prior rejection or task
   stalls. See the [sanitized evidence](../benchmarks/results/2026-11-07-reliability-baseline.md).
   An offline reconciliation found 27 completed Codex command events but only
   21 Responses function-call items. A process-group-bounded Codex event
   capture helper and proxy monotonic timestamps are now tested offline. The
   normal live tool workflow matched 10 Responses calls to 10 Codex command
   events; all 11 Responses requests advertised tools. See the
   [smoke report](../benchmarks/results/2026-11-08-codex-trace-crlf-smoke.md).
   A deterministic import of pinned Herd v0.12.3 reproduces the adapter path:
   an empty Codex tool list omits Ollama's `tools` field, while the response
   converter still emits synthetic Ollama tool calls as Responses
   `function_call` items. This is consistent with five tool-call outputs on
   tool-less requests, but the live Ollama boundary was not captured. Evidence
   and limits: [source-level reproduction](../benchmarks/results/2026-11-08-herd-empty-tools-translator-repro.md).
   A disposable guard prototype passes 61 translator tests, two mocked-Ollama
   route cases, and the full upstream suite (1,992 passed, 5 skipped). No live
   task has exercised it. See the [prototype record](../benchmarks/results/2026-11-08-herd-empty-tool-guard-prototype.md).
   A fresh stock-adapter protocol control completed a synthetic bug-fix task in
   81.7 seconds: 16 Responses requests all advertised the same 13-name tool
   catalog. This did not reproduce the historical empty-tool request, so the
   guard was not exercised. The report records that the disposable router must
   suppress mDNS, even with a loopback bind. Next, identify the request class in
   the historical stalled trace: all 14 empty-tool requests included prior
   call/results but used at most 5,451 input tokens; the control retained tools
   with 15 prior calls and 13,613 tokens. This argues against context exhaustion
   or tool history alone. Keep the guard isolated until a relevant live case
   reproduces the request state. Do not change production behavior.
   A timestamped trace correlator now joins non-overlapping Responses
   completion/request windows to Codex command-event counts while explicitly
   leaving concurrent intervals unassigned. The fresh HTTPie #1978 diagnostic
   exercised it: 27 of 29 command starts and 27 of 29 completions fell in
   assignable windows; two starts and two successful completions remained
   unassigned. Both empty-tool requests were completed final responses with no
   function calls. This does not reproduce the earlier #1958 mismatch, where
   five empty-tool requests returned `exec_command`. See the
   [live trace report](../benchmarks/results/2026-11-08-httpie-1978-trace-correlation.md).
   The correlator now emits total, assigned, and unassigned command-event
   counts so this reconciliation is repeatable. Next, inspect the retained
   #1958 metadata and event ordering for any additional lifecycle signal; do
   not rerun the retired issue fixture or promote the adapter guard without a
   relevant reproduced behavior.
3. Classify unsupported-tool events as model-selected invalid calls versus
   transport/parser loss; add a deterministic reproducer before changing code.
   The two `read_file` rejections came from the 15:50 untraced HTTPie #1958
   attempt. The separate 19:42 wire trace contained empty-tool requests but no
   `read_file` response or Codex rejection; do not correlate these observations.
4. Trace repeated inspection across consecutive messages to test whether prior
   tool results remain in conversation state. Add a fixture for tool-result
   continuity and final-turn completion.
5. Validate each benchmark runner's sandbox-visible task, test environment,
   hard timeout, artifacts, and independent verification before scoring.
6. Isolate reasoning-control handling. Preserve defaults and verify the actual
   Ollama request field before benchmarking any behavior change.
7. Make one minimal reversible change only after a root cause is demonstrated;
   compare before/after on the same task and model.

## Then: daily-driver qualification

Build a held-out set of at least 20 representative tasks and score first-pass
agent completion separately from retry-assisted and human-corrected changes.
Require an independently verified patch and completed Codex turn for a
pass@1. Record end-to-end time, model/digest, context, tool errors, and
intervention count. Keep the existing default until a profile meets the
acceptance gate.

## Deferred

Hermes parity, orchestration, Bitburner agents, model downloads, offloading
engines, hardware purchases, and provider-routing changes remain deferred until
the current client/protocol path is reliable.
