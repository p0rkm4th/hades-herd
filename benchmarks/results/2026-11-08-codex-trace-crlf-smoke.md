# Codex trace-capture and CRLF parser smoke — 2026-11-08

This was a bounded integration smoke test for the new Codex event timeline and
a real defect in the sanitized SSE trace parser. It is not a model-quality
trial and is excluded from pass-rate counts.

## Setup

- Codex CLI 0.166.0 through `codex-herd` and the existing Herd Responses route,
  observed through the loopback-only metadata proxy.
- Model: `mimo-v26-9b-codex-16k-hecate:latest`, digest
  `47f141d59fb9ece0a349cf27e8292b8c192ae0082b8a051c2e29c06526feea4b`,
  configured context 16,384; Hecate RTX 4070 Ti.
- Clean disposable repository copy based on public commit
  `6ebb471484b64d85b78a254cf8178d5f428a015d`; 180-second process-group timeout,
  workspace-write sandbox, temporary HOME/CODEX_HOME, no downloads or hosted
  provider.
- The baseline CRLF SSE probe returned no terminal status, while the existing
  LF parser tests passed.

## Result

Codex completed its turn in 152.7 seconds and made edits. The first proposed
parser loop inspected only the first newline and returned before finding the
blank-line delimiter; this regressed existing LF behavior. The generated test
fixtures also contained malformed JSON and an incorrect expectation about
message-item capture. The first independent full-suite check found five
failures. The task therefore required human correction and is not an
autonomous pass.

The corrected implementation searches for the earliest LF or CRLF frame
delimiter in the accumulated buffer, normalizes CRLF inside completed frames,
and retains partial delimiters across chunks. Regression coverage checks pure
CRLF framing, mixed LF/CRLF frames, and split delimiters. After correcting the
implementation and test fixtures, all 27 tests passed independently and
`git diff --check` passed.

## Trace reconciliation

The new capture recorded 10 Responses `function_call` items named
`exec_command` and 10 completed Codex `command_execution` events. The final
request returned a message; Codex emitted `turn.completed`, and the process
did not hit its timeout. All 11 Responses requests carried the nine-item tool
catalog; none had an empty tool list. This shows the new timeline can reconcile
a normal tool-using run exactly. It does not explain the empty-tool requests
from the earlier HTTPie trace.

Hecate was unloaded after the run; Herd reported 7/7 nodes online and idle. No
production configuration changed. Raw events and stderr remain in private
temporary storage and are not published.
