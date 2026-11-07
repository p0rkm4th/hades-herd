# Qwen3.8 reasoning effort `none` diagnostic

Date: 2026-11-08. This is a single paired diagnostic, not a model-quality score.

## Hypothesis and setup

The previous Qwen3.8 Q4/Nyx attempt with Codex `reasoning.effort=low` spent
roughly two minutes generating Ollama tokens but delivered no client-visible
text/tool chunks before the 180-second Codex cap. This trial changed only the
requested effort. Ollama `/api/show` reported native thinking values
`false`, `low`, `medium`, and `xhigh`; a disposable adapter copy mapped Codex
`none` to native boolean `think: false` when `false` was advertised. The
Codex CLI model catalog listed `none`, and `codex debug models` accepted it.
This mapping was not deployed.

- Base/task: public commit `19396a2ebfa677d6c93a0827e591150a2a24d9eb`, same
  trace call-count task, fresh detached worktree.
- Model: Qwen3.8 27B Q4, `qwen38-27b-q4-codex-16k:latest`, digest
  `0c315bae2dc37d912ae0ba10b1a2ea053296bce7f5be8f77283613df0d5f974b`.
- Runtime: Codex CLI 0.166.0, 16,384 configured context, isolated loopback
  Herd v0.12.3 app, Nyx only, `auto_pull=false`, zero retry, fresh HOME and
  CODEX_HOME, workspace-write sandbox, 180-second OS timeout.
- No hosted credentials or production endpoint; no production default, route,
  model, service, or provider changes.

## Result

Codex exited 124 at 180 seconds after seven completed shell-command executions.
There was no tracked source change and no `turn.completed` event. Ollama's
journal recorded about 734 generated tokens at approximately 9.4 tokens/s;
the context reached 14,214 tokens of 16,384. The adapter logged an incomplete
stream after 81 seconds with zero client-visible text/tool chunks. Ollama then
logged HTTP 500 after the Codex process disconnected.

The exact outbound `/api/chat` JSON was not captured, so this run does not
independently prove that `think: false` reached Ollama. Do not conclude that
`none` improves or fails to improve model reasoning from this one attempt. The
near-16K context use and the unverified control application are confounders.

## Cleanup

Qwen was explicitly unloaded; `/api/ps` was empty and both Nyx GPUs returned to
0% utilization (5 MiB / 1 MiB). The loopback router stopped and port 18779
closed. Production Herd was 7/7 online with zero active requests and no loaded
models. Raw logs and CLI events remain private.

Codex reasoning effort names are model-dependent in the [official reasoning
API guide](https://developers.openai.com/api/docs/guides/reasoning); this local
model-specific mapping is experimental and is not implied by that API guidance.

## Follow-up no-inference transport control — 2026-11-08

A separate fresh-HOME Codex CLI 0.166.0 request used the same isolated route
mapping but replaced Ollama with a synthetic streaming client. The capture
stored only scalar metadata. It confirmed Codex sent `reasoning.effort=none`,
the adapter mapped it to boolean `think: false`, and the outgoing request was a
`POST /api/chat` for the expected model. The request had seven tool definitions
and no explicit `num_ctx`; the profile/catalog carried the configured context.
Codex received the mock completion and emitted `turn.completed` (exit 0). No
model was loaded, no prompt/tool arguments were recorded, and no production
service was contacted.

This verifies the profile-to-adapter mapping path for `none`. It does not
capture the exact Ollama request from the earlier real-inference attempt and
does not demonstrate improved coding-task completion.
