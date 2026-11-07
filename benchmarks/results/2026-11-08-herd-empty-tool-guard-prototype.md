# Empty-tool response guard prototype — 2026-11-08

Follow-up to the [translator reproduction](2026-11-08-herd-empty-tools-translator-repro.md).
This is a focused prototype in a disposable clone of upstream Herd v0.12.3,
not a deployed change or a modification to the HADES server.

## Prototype behavior

The experiment preserved the difference between an explicit empty offered-tool
set and an unknown offered-tool set. For an explicit empty set, it suppressed
the Ollama `exec_command` response and returned a visible assistant message in
both streamed and non-streamed translation. When the offered set was unknown
(`None`), the existing pass-through behavior remained. The direct streamed
check confirmed there was no `function_call` event and the response completed
with the visible message.

## Verification limits

- The complete upstream translator test file passed: 61 tests.
- The complete upstream suite passed: 1,990 passed, 5 skipped, with 3 existing
  `RuntimeWarning`s in unrelated `queue_manager` tests. The suite ran against
  the patched disposable clone.
- Tests ran in a `.venv` created inside that clone with `uv sync --extra dev`;
  no system Python or production service was changed. Python compilation and
  `git diff --check` passed.
- The first focused run found one stale expectation: malformed `apply_patch`
  calls were expected to pass through despite not being advertised. The
  expectation and misleading log wording were corrected, then all 61 tests
  passed.
- No isolated Herd HTTP route with a mocked Ollama backend, live inference,
  held-out coding task, or production deployment was run.

This establishes that the proposed distinction is implementable at the
translator-function level and passes both the focused translator tests and
the full upstream suite. It does not prove the guard improves Codex task
completion or that the historical live calls followed this exact path. Keep
the prototype isolated until a mocked-route test and an end-to-end task
establish the behavior.
