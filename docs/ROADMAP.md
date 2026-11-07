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
5. Reasoning-control handling has an isolated review patch and live request
   evidence: the backend-advertised effort is forwarded as Ollama `think`, and
   the Responses output cap becomes `options.num_predict`. Codex's structured
   catalog schema is verified. One matched task pair completed through the
   patch but timed out through stock Herd; one pair is directional evidence,
   not a causal result. The patch is not deployed, dynamic catalogs still
   expose no effort choices, and the interactive `/model` picker is untested.
   See the
   [patch notes](https://github.com/p0rkm4th/hades-herd/blob/codex-herd/show-thinking-controls/patches/README.md) and
   [sanitized task evidence](../benchmarks/results/2026-11-07-adapter-coding-task-pair.md).
6. Classify invalid tool calls and trace repeated inspection/final-turn stalls.
   **Finding:** Herd v0.12.3 intentionally drops hosted `web_search`/`file_search`
   tools with a warning; it expands Codex's default `functions` namespace and
   has explicit tool-result continuity translation. Do not treat the hosted-tool
   drop as accidental loss of shell tools. The historical invalid `read_file`
   source and live inspection/final-turn stalls remain unresolved. Codex 0.166.0
   passes the deterministic valid `exec_command` round trip against a loopback
   mock, while rejecting the separate unadvertised `read_file` call. Compare
   that result against a bounded, isolated Herd route before changing the
   client or server. See the
   [tool-filtering evidence](../benchmarks/results/2026-11-07-responses-tool-filtering.md)
   and [Codex round-trip result](../benchmarks/results/2026-11-07-codex-tool-roundtrip.md).
   Make further changes only against a reproduced cause; do not infer general
   improvement from a single paired task.

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
