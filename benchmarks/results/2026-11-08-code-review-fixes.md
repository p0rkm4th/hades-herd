# Public code-review fixes — 2026-11-08

Review baseline: public `main` commit `19396a2`, reviewed on 2026-11-07. Changes
are prepared on a focused branch from that baseline. This report records offline
unit/subprocess tests only; no private Herd request or model inference was used.

| Finding | Change | Verification |
|---|---|---|
| Fresh install had no selected model; explicit selection could be shadowed by the first catalog model | Implicit launch selects the first eligible model and persists it as the initial default. Explicit model selection takes precedence and does not replace the saved default. | Isolated-home launcher tests for implicit and explicit selection. |
| Unloaded catalog entries claimed only a 4K context even when the model alias configured `num_ctx` | Prefer a validated saved Codex override, then observed loaded allocation, then parsed model `num_ctx`; retain a visibly labeled 4K fallback only when configuration is unknown. Model-declared maximum remains separate metadata. | Mock `/api/show` reports `num_ctx 16384`; generated Codex catalog advertises 16K without claiming live allocation. |
| No end-to-end launcher smoke test | Added subprocess coverage using a local mock Herd API and fake Codex executable under an isolated `HOME`. | Verifies generated profile/catalog, model selection, argument forwarding, and exit code propagation. |
| Trace parser collapsed distinct same-name tool calls | De-duplicate lifecycle events by response item ID (or call ID), not by tool name; preserve call order and omit IDs/arguments. | Two same-name calls remain two metadata records; added/done/complete events for one ID count once. |
| Generated profile was written in place and contained per-model developer instructions | Replace generated TOML atomically; pass selected model's instructions as that Codex invocation's explicit config override, avoiding shared-profile cross-talk between launches. | Simulated replace failure preserves the previous profile; two model configs resolve to their own instructions. |

Local verification on Python 3.14: `python3 -m unittest discover -s tests -v`
passed all 23 tests; `git diff --check` passed. The focused `main`-based branch
passed the Python 3.10–3.14 matrix in
[GitHub Actions run 42443450209](https://github.com/p0rkm4th/hades-herd/actions/runs/42443450209).

These fixes address launcher and measurement defects only. They do not
demonstrate real model autonomy, resolve the observed empty-tool-list trace,
or qualify a daily-driver model. The HADES production default is unchanged.
