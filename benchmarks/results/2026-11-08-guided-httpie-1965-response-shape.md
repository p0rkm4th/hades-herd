# Guided HTTPie #1965 response-shape diagnostic

**Date:** 2026-11-08 02:38 UTC  
**Model:** MiMo-V2.6 9B Q4_K_M, digest `47f141d59fb9ece0a349cf27e8292b8c192ae0087b2a051c2e29c06526feea4b`  
**Context:** 16K configured  
**Codex CLI:** 0.166.0  
**Task base:** `5b604c37c6c67e18e7c3e9aee6c88a8c22b98345`

This was one same-input diagnostic repetition of the prior per-model
developer-instruction follow-up. The task, instruction, model, context,
guarded disposable Herd route, and Codex sandbox were unchanged. The only
difference was use of the updated metadata-only Ollama proxy, which now records
content/thinking field presence and character counts without retaining text.
The task was bounded by a 180-second process-group timeout.

## Result

Codex timed out (exit status 1) at 180.1 seconds without a final turn or
source/test edits. Its content-free event index recorded 17 shell command
starts: 16 completed and one failed. The task worktree contains only the
untracked task instructions.

The Codex boundary trace recorded **17 completed Responses requests**, each
returning one `function_call` for `exec_command`. The Ollama observer recorded
**18 `/api/chat` requests**, all with `content` present but zero characters,
and all returning one `exec_command` call. Thirteen responses included a
`thinking` field. Across all 18 backend responses, Ollama reported 151,250
prompt tokens, 14,769 generated tokens, and 44,418 thinking characters, with
zero visible content characters. The 18th backend request began before Codex's
hard timeout and finished about 25 seconds after Codex was killed; it has no
corresponding completed Responses request. The router/test app and model were
stopped after cleanup.

This run demonstrates an inspection loop and no user-visible completion in
this trial. It does not prove that hidden thinking alone caused the loop, nor
that model-specific instructions caused the behavior. It does show why the
earlier single-request follow-up could not be interpreted from token counts
alone: that run had no content-shape capture. The two follow-ups with the same
instruction produced different request histories, so they are evidence of
instability rather than a controlled success.

## Verification and cleanup

Before inference, issue #1965 reproduced as `prefix='a'`; the focused baseline
suite passed **121 tests with 3 expected xfails**. No implementation was
produced, so there was no patch or post-run code to verify. MiMo was unloaded;
Hecate returned to 5 MiB GPU memory. The disposable app, both loopback
proxies, and strict-key SSH tunnel were stopped. Production Herd remained 7/7
online with zero active requests and no configuration changes.

## Next action

Do not repeat this task or lengthen its timeout. First test the Codex/Herd
response handling with a deterministic Ollama fixture that returns a
thinking-only response, then a valid tool call, and verify whether Codex
continues, receives empty output, or stalls. Separately test client disconnect
cancellation: the last backend generation outlived Codex's process timeout by
roughly 25 seconds in this run. Keep both as isolated protocol diagnostics;
do not deploy a production adapter change until one reproduces a fixable
failure with a regression test.
