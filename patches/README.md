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

On 2026-11-07, an isolated in-process router using this patch sent explicit
`reasoning.effort: "low"` and `max_output_tokens: 64` to Nyx. The metadata-only
transport observed `/api/show`, then `/api/chat` with `think: "low"` and
`options.num_predict: 64`; the Responses stream returned HTTP 200 and
`response.completed` in 9.18 seconds. The same route's pre-fix capture had
`max_tokens` at top level and no `options.num_predict`; it is retained as the
before result. The patched route maps the cap, preserves other Ollama options,
and avoids Herd's thinking-overhead inflation for an explicit Responses
ceiling. The change is covered by unit tests, including a thinking-model case,
and the full suite passed. Ollama's [Chat API](https://github.com/ollama/ollama/blob/main/docs/api.md)
documents generation options inside `options`, including `num_predict`. The
model was unloaded afterward; the backend reported no resident models and both
GPUs returned to idle. No production Herd router or client configuration was
involved. This verifies the selected control fields on the live outbound body,
not coding quality, unsupported-value handling, or general daily-driver
reliability.

Codex's HADES model catalog still advertises no reasoning levels in the
production profile. In particular, this patch alone does not enable the
interactive `/model` control or prove a coding-task improvement. Before use,
verify unsupported values against the isolated route, integrate catalog
metadata, and repeat a controlled coding-task comparison. Do not apply it to the
production router as-is.
