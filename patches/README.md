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
installed on the HADES router or exercised against a live inference request.
The full upstream suite passed (1,993 passed, 5 skipped); targeted translator,
Responses-route, and streaming tests passed (99 passed); Ruff check and format
passed for the modified source files. Three existing queue-test coroutine
warnings remain in the upstream suite output.

Codex's HADES model catalog still advertises no reasoning levels in the
production profile. In particular, this patch alone does not enable the
interactive `/model` control or prove a coding-task improvement. Before use,
apply it only to an isolated router, verify the exact outbound Ollama
`/api/chat` body for a supported and unsupported effort, then integrate catalog
metadata and repeat a controlled task comparison. Do not apply it to the
production router as-is.
