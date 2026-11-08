# Roadmap

## Immediate: diagnose reliability

1. Address source-review findings before collecting more model scores. A
   focused branch now fixes clean-install/default precedence, configured versus
   loaded context metadata, launcher subprocess coverage, repeated call
   counting, and atomic model-isolated profile generation. The 3.10–3.14 CI
   matrix passed. The owner review confirmed these five findings; the
   GitHub integration currently blocks PR creation with 403, so review remains
   available from the pushed compare branch.
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
   route cases, and the full upstream suite (1,992 passed, 5 skipped). Its
   bounded live attempt on HTTPie #1958 timed out and independent tests found
   four failures. The metadata trace saw three empty-tool requests with
   message-only responses but cannot confirm guard activation. Stock and
   guarded task attempts both failed with different request mixes, so no
   autonomy benefit is established. See the [prototype](../benchmarks/results/2026-11-08-herd-empty-tool-guard-prototype.md)
   and [live attempt](../benchmarks/results/2026-11-08-guarded-httpie-1958-live-task.md).
   A fresh stock-adapter protocol control completed a synthetic bug-fix task in
   81.7 seconds: 16 Responses requests all advertised the same 13-name tool
   catalog. This did not reproduce the historical empty-tool request, so the
   guard was not exercised. The report records that the disposable router must
   suppress mDNS, even with a loopback bind. Next, identify the request class in
   the historical stalled trace: all 14 empty-tool requests included prior
   call/results but used at most 5,451 input tokens; the control retained tools
   with 15 prior calls and 13,613 tokens. This argues against context exhaustion
   or tool history alone. The loopback Ollama metadata proxy was used on a
   held-out HTTPie #1965 task. It confirms MiMo selected an unadvertised
   `read` tool after shell inspection; the guarded adapter suppressed it and
   returned a notice, but the agent did not continue or edit files. A controlled
   same-task follow-up with explicit developer instructions made no tool call,
   yet Codex completed without a visible response or edits. That trace also
   showed Herd dropping Codex's untranslatable `web_search` entry; this is a
   separate protocol limitation, not a demonstrated cause. The observer now
   records content/thinking field presence and character counts without
   retaining content, because the earlier 231-token follow-up response could
   not be classified. See the
   [unsupported-tool attempt](../benchmarks/results/2026-11-08-heldout-httpie-1965-live-attempt.md),
   [guided follow-up](../benchmarks/results/2026-11-08-guided-httpie-1965-followup.md),
   and [metadata proxy](../benchmarks/README.md#ollama-side-metadata-capture).
   A same-input response-shape repetition then timed out at 180s: 17 completed
   Codex requests each returned `exec_command`, while all 18 Ollama replies
   had zero content characters and 44,418 thinking characters total. The last
   backend response finished about 25 seconds after Codex was killed. This
   supports an inspection-loop diagnosis but not a causal claim about hidden
   reasoning. The deterministic thinking-only probe shows stock v0.12.3
   returns completed empty Responses output in both stream modes. Codex 0.166.0
   treats that response shape from a loopback mock as a successful blank turn,
   with no follow-up request. This is a plausible blank-turn mechanism, but it
   does not prove the earlier live blank turn had that shape. A content-free
   trace-proxy test verifies downstream EOF detection and closure of its
   upstream stream. A separate v0.12.3 in-process route test confirms that a
   client disconnect cancels the mocked backend stream and frees the queue
   slot. Real Ollama generation cancellation remains unverified. A disposable
   candidate patch turns a completed empty model output into `response.failed`;
   Codex surfaces the error instead of a blank success, but does not retry. It
   is unapplied and unsubmitted. A deterministic Codex mock now verifies
   advertised shell call → tool result in the next request → final message.
   The same sequence passed through a real Codex process, the pinned Herd HTTP
   route, and a fake Ollama transport. This verifies stateless tool-result
   continuity across the adapter for a scripted call, not model autonomy.
   Next, verify whether Ollama stops after request cancellation. See the
   [shape report](../benchmarks/results/2026-11-08-guided-httpie-1965-response-shape.md).
   New evidence: [thinking-only/disconnect report](../benchmarks/results/2026-11-08-thinking-only-and-disconnect-probes.md).
   Do not repeat HTTPie #1958 or #1965 without a new response-shape hypothesis;
   production behavior remains unchanged.
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
   counts so this reconciliation is repeatable. A loopback Codex boundary
   control also confirms that Codex executes a returned `exec_command` even
   though the simulated adapter/backend offer was empty, while the guard-style
   visible message executes no command. Codex's own requests still contained
   nine tools, so the control does not recreate the historical incoming empty
   tool list. A shell-tool-disabled attempt timed out before sending a request.
   The complete in-process Herd route was then compared against a fake Ollama
   backend on stock and guarded v0.12.3 for streaming and non-streaming
   requests. Stock returned a synthetic `function_call` although Ollama
   received no tools; the guard returned visible text and no call. All four
   paired cases returned 200. This confirms the route mismatch, not its effect
   on a real coding task. The patch, notice, and reusable probe are published;
   it remains unapplied. The same bounded failing HTTPie #1958 task has now
   been tried once through the guard: it timed out and its tests failed. Do not
   repeat that fixture. A paired trace enhancement now records bounded schema
   shape at both the Codex and Ollama boundaries, alongside Ollama-side offered
   and returned tool names. One bounded live task completed with non-empty
   offers and matching structure for the seven common functions. Its first
   observer lost response metadata at stream close; a corrected-observer
   repetition recorded five complete call/result continuations using only
   advertised `exec_command`. The first run's later Codex input listed two
   `read` calls/results while Ollama recorded one unadvertised `read`; this
   remains unexplained without ID-level evidence. Do not repeat either task
   without a specific hypothesis. See the [paired live diagnostic](../benchmarks/results/2026-11-08-live-schema-diagnostic.md)
   and [trace report](../benchmarks/results/2026-11-08-tool-schema-trace.md).
3. A live model-generated `read` call was unadvertised at the Ollama boundary;
   Codex rejected the tool name. This distinguishes that event from transport
   loss, but does not explain why the model selected it or prove it caused a
   task failure. The historical `read_file` rejections remain uncorrelated.
4. A deterministic Codex mock and the real Codex→Herd route both verify
   tool-call/result continuation to a final response. The corrected live trace
   also records five continuations. This validates protocol continuity, not
   autonomous coding reliability.
5. Validate each benchmark runner's sandbox-visible task, test environment,
   hard timeout, artifacts, and independent verification before scoring.
6. The content-free reducer now has an optional `--ollama-summary` mode that
   compares ordered tool names only when a backend request is wholly contained
   in one Codex request window; overlaps remain unassigned. Use it before any
   future live trial, and only when a new hypothesis justifies the workload.
   Never record identifiers, arguments, prompts, or tool results.
7. Keep the empty-tool guard and empty-response failure candidates isolated:
   deterministic tests prove their protocol behavior, but live tasks did not
   demonstrate better completion. Real Ollama generation cancellation through
   Herd also remains unverified. Make no production adapter change until a live
   cause and useful recovery behavior are demonstrated.
8. Reasoning-control mapping is verified through a synthetic transport, but the
   real Qwen attempt did not complete and did not capture the exact outgoing
   Ollama request. Preserve defaults; revisit only with exact request capture
   and a bounded task hypothesis.

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
