# Sanitized local Codex/Herd reliability baseline — 2026-11-07

This report summarizes isolated disposable-repository runs. It excludes raw
prompts, shell transcripts, private hostnames, addresses, access data, and
unredacted logs. Public issues are linked so an independent reviewer can inspect
the task definition. The profiles ran through Codex CLI 0.166.0 and Herd 0.12.3;
model contexts and digests are recorded below. Ollama was 0.40.15 on the
private fleet at the time of these runs.

| Task | Profile | Result | Observed behavior |
|---|---|---|---|
| [HTTPie #1960](https://github.com/httpie/cli/issues/1960), repeated-header ordering | MiMo-V2.6 9B Q4_K_M, 16K | Complete pass@1; ~126 s | Patch and regression completed; focused and independent module verification passed 122 tests, 3 expected xfails |
| HTTPie #1960, same task | Qwen3.8 27B Q4, 16K | Incomplete, 0/1 | Core edit and smoke output existed, but the 180 s turn ended before tests/final review; 300 s retry still ended before final completion and required a test expectation correction |
| [Rich #4250](https://github.com/Textualize/rich/issues/4250), `FileProxy.write` return count | MiMo-V2.6 9B Q4_K_M, 16K | Incomplete, 0/1 | 180 s timeout; 22 shell calls, repeated reads of the same source/tests, no edits; baseline focused suite 15 passed |
| Rich #4250, matched | Qwen3.8 27B Q4, 16K | Incomplete, 0/1 | 180 s timeout; two shell calls, no edits; generation was observed near 11.1 tokens/s; baseline 15 passed |
| [HTTPie #1958](https://github.com/httpie/cli/issues/1958), mixed-case JSON media type | MiMo-V2.6 9B Q4_K_M, 16K | Incomplete, 0/1 | Corrected run made 27 shell-command items, attempted unsupported `read_file` twice, no source/test edits; baseline 121 passed, 3 xfailed |
| [pytest #15341](https://github.com/pytest-dev/pytest/issues/15341), read-only parent cleanup | MiMo and Qwen3.8, 16K | Incomplete; duplicate fixture retired | A previous MiMo patch misplaced its regression inside another test and timed out without final; the later matched pair made no edits. The later preflight missed already-open [PR #15343](https://github.com/pytest-dev/pytest/pull/15343), so this is not a fresh task-family result. |

The Rich #4250 baseline issue was reproduced before inference; both profile
runs used identical code, task acceptance, test environment, and hard cap.
This straightforward task still produced repeated inspection without
implementation. It is one matched task, not proof that either model lacks
coding ability. The private evidence records direct reproductions, isolated
clones, event counts, and cleanup.

## Current diagnosis

- Tool transport is not the sole explanation: multiple runs successfully
  invoked Codex shell execution, and one MiMo task completed end to end.
- `read_file` failures are observed in some event traces, but we have not yet
  proven whether those were model-selected names outside Codex's advertised
  tools or an adapter/serialization defect. Do not patch the server on this
  evidence alone.
- Repeated reads may reflect model planning, task prompting, or context/state
  handling. Existing evidence does not identify the cause.
- The installed Herd Responses adapter's Codex catalog advertises no reasoning
  levels, and the current integration was observed not to forward Codex
  `reasoning.effort` or Ollama's native `think` field. A prompt-level Qwen
  `/no_think` attempt was not verified as changing the actual request. No
  reasoning default was changed.
- Some prior runs had invalid sandbox paths, missing dependencies, or
  unverified timeouts. Those are harness defects and are excluded from model
  pass rates.

Next: inspect sanitized wire-level tool schemas/results and Herd conversation
reconstruction, then make a deterministic minimal reproducer. No model default,
production routing, or server behavior changed as part of this baseline.
