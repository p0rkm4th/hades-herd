# Experimental adapter patches

## Ollama Herd 0.12.3: Codex reasoning effort

[`ollama-herd-v0.12.3-reasoning-effort.patch`](ollama-herd-v0.12.3-reasoning-effort.patch)
is a review artifact against the upstream Ollama Herd `v0.12.3` source commit
[`e0dac345515e8423e385ea2d465573a1e8b5a1bf`](https://github.com/geeks-accelerator/ollama-herd/commit/e0dac345515e8423e385ea2d465573a1e8b5a1bf).
The upstream source is MIT-licensed; its license is included at
[`licenses/ollama-herd-MIT-LICENSE.txt`](licenses/ollama-herd-MIT-LICENSE.txt).

The patch carries an explicit Codex `reasoning.effort` through the Responses
translator, queries `/api/show` on the selected node/model, and adds Ollama's
`think` field only when the exact requested string appears in that model's
advertised values. Missing or unsupported values return an explicit 400.
Default requests remain unchanged. Metadata is cached per node/model for 60
seconds and cleared when the node's Ollama connection is invalidated.

The patch was tested in a disposable source clone only. It has **not** been
installed on the HADES router. The full upstream suite passed (1,994 passed,
5 skipped); three targeted translator/route/streaming regression tests passed;
Ruff check and format passed for the modified production source. Three existing
queue-test coroutine warnings remain in the upstream suite output. A
thinking-model output-cap regression also verifies the Responses limit is not
inflated by Herd's reasoning-overhead heuristic. The expanded patch applies
cleanly to a fresh worktree at the pinned v0.12.3 commit.

On 2026-11-07, an isolated in-process router using this patch sent one explicit
`reasoning.effort: "low"` Responses request to the Nyx Ollama backend. A
metadata-only test transport observed the `/api/show` capability lookup and the
subsequent `/api/chat` request with `think: "low"`; the Responses stream
returned HTTP 200 and `response.completed` in 9.92 seconds. The request was
sent with a requested `max_output_tokens: 64`, but inspection of the serialized
Ollama body showed `max_tokens: 64` at top level and no `options.num_predict`.
Ollama's [Chat API](https://github.com/ollama/ollama/blob/main/docs/api.md)
documents generation options inside `options`, including `num_predict`, so this
was **not a verified 64-token generation cap**. The model was unloaded
afterward; the backend reported no resident models and both GPUs returned to
idle. No production Herd router or client configuration was involved. This
verifies field pass-through for one supported reasoning value only; it does not
demonstrate a coding-task improvement or validate unsupported-value handling
against a live backend. Correct output-limit translation is a separate
The review patch now maps a present `max_tokens` into
`options.num_predict`, preserves other Ollama options, and includes a regression
test. That mapping passed unit tests but was not in place during the live check;
verify it on the isolated live route before using output limits as benchmark
controls.

Codex's HADES model catalog still advertises no reasoning levels in the
production profile. In particular, this patch alone does not enable the
interactive `/model` control or prove a coding-task improvement. Before use,
verify unsupported values against the isolated route, integrate catalog
metadata, and repeat a controlled task comparison. Do not apply it to the
production router as-is.
