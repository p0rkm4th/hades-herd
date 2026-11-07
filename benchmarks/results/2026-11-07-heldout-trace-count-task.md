# Held-out Codex tool-trace task

Date: 2026-11-07. This is a diagnostic attempt, not a model-quality score.

## Task and setup

The task asked Qwen3.8 27B Q4 to fix trace aggregation that collapsed multiple
same-name function calls, preserve event ordering/counts, avoid retaining IDs or
arguments, and add regression coverage. The public base was
`19396a2ebfa677d6c93a0827e591150a2a24d9eb`. Before inference, the Python 3.10
suite passed 14/14 and a synthetic reproducer confirmed two distinct
`exec_command` calls collapsed to one record.

Codex CLI 0.166.0 used the existing isolated Herd Responses adapter, a fresh
HOME/CODEX_HOME, workspace-write sandbox, `reasoning.effort=low`, and 16,384
context. The Nyx model alias was `qwen38-27b-q4-codex-16k:latest`, digest
`0c315bae2dc37d912ae0ba10b1a2ea053296bce7f5be8f77283613df0d5f974b`.
The router was loopback-only, Nyx-only, with automatic pulls disabled and zero
retries. An external 180-second process timeout bounded the run.

## Result

Codex exited 124 at the 180-second cap after executing four shell commands
(three file-reading commands and one Python command). The event stream had no
source edits or `turn.completed` event, and the held-out worktree's tracked diff
remained empty. No independent implementation tests were applicable because no
patch was produced. The model used its shell tool for limited repository
inspection without progressing to implementation. This is consistent with earlier
traces but does not identify the cause or establish a general model limitation.

Classify this as incomplete/no-progress diagnostic evidence, excluded from
pass-rate scores. Do not rerun this fixture absent a materially changed,
testable hypothesis.

## Cleanup and scope

The model was explicitly unloaded and Ollama `/api/ps` returned no models. The
isolated router stopped and its port closed. Production Herd remained 7/7
online with no active requests. No production route, default, service, or client
configuration changed. Raw Codex events and router logs remain private and are
not included here.
