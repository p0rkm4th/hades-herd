# Roadmap

## Immediate: diagnose reliability

1. Capture sanitized Codex request/response metadata and identify the exact
   advertised tool list, attempted tool name, Herd translation, execution
   result, and tool-result continuation. **Partial evidence:** one live
   HTTPie #1958 trace captured the Codex↔Herd boundary; it did not reproduce a
   `read_file` call, but did show that some requests carried an empty tools
   array while the full stateless input included prior calls/results. This
   narrows the wire behavior but does not explain the prior rejection or task
   stalls. See the [sanitized evidence](../benchmarks/results/2026-11-07-reliability-baseline.md).
2. Classify unsupported-tool events as model-selected invalid calls versus
   transport/parser loss; add a deterministic reproducer before changing code.
3. Trace repeated inspection across consecutive messages to test whether prior
   tool results remain in conversation state. Add a fixture for tool-result
   continuity and final-turn completion.
4. Validate each benchmark runner's sandbox-visible task, test environment,
   hard timeout, artifacts, and independent verification before scoring.
5. Isolate reasoning-control handling. Preserve defaults and verify the actual
   Ollama request field before benchmarking any behavior change.
6. Make one minimal reversible change only after a root cause is demonstrated;
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
