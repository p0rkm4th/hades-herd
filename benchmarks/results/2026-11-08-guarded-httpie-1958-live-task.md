# Guarded Herd adapter: live HTTPie #1958 attempt

Date: 2026-11-08  
Purpose: bounded diagnostic of the explicit-empty tool guard; not a model score.

## Configuration

- Task: HTTPie #1958, mixed-case JSON media type formatting, starting commit
  `5b604c37c6c67e18e7c3e9aee6c88a8c22b98345`.
- Model: MiMo-V2.6 9B Q4_K_M, digest prefix `47f141d5`, configured context
  16,384 tokens, on one RTX 4070 Ti host.
- Client: Codex CLI 0.166.0 through the public `codex-herd` launcher, fresh
  temporary home, workspace-write sandbox, no hosted credentials, 180-second
  process-group timeout.
- Router: pinned Ollama Herd v0.12.3 in a disposable worktree, with the
  experimental explicit-empty tool guard patch. The test app and metadata
  proxy listened only on loopback; a strict-key SSH tunnel reached the existing
  Ollama service. No production Herd route or service was used.

An initial launcher attempt was invalid: the disposable test-app factory had
not initialized its required trace store, and the request failed before model
inference. The app was restarted with its own temporary data directory. The
invalid attempt is excluded below.

## Result

The corrected run reached inference and timed out at 180 seconds (exit 124),
without a Codex `turn.completed` event. It made a source edit and test edits,
but remained an incomplete agent run. The sanitized Codex event index recorded
40 command starts, 36 successful completions, and 4 failed commands. There
were 38 distinct command strings (two exact repeats); the task instructions
were read four times, and two test commands were issued.

The Responses trace contained 40 POST requests. Three explicitly had an empty
tool list; their returned Responses contained message items and no function
calls. The metadata-only trace does not include message text or Ollama's raw
tool-call output, so it cannot prove whether the guard synthesized those
messages. The deterministic route tests separately demonstrate the guard's
filtering behavior.

Independent execution of the task's requested `tests/test_output.py` suite
found **4 failures, 127 passes, and 3 expected xfails**. The failures were in
lexer-selection assertions added or changed during the attempt; they did not
validate the requested body-formatting behavior. The source edit changes
JSON MIME detection in `JSONFormatter.format_body`, but the uncompleted run did
not leave a passing focused suite. `git diff --check` passed.

## Comparison and limits

The historical stock-adapter run on the same task, model digest, context, and
timeout recorded 30 Responses requests, 14 empty tool lists, and 5 function
call outputs on those empty-list requests; it also timed out without a patch.
The guarded run had a different request mix and likewise did not complete.
These two runs do **not** show that the guard improved autonomous coding:
neither completed the task, and the differing request traces prevent a
controlled causal comparison.

The attempt is excluded from coding pass-rate scores. The guard remains
experimental and unapplied to production. MiMo was unloaded after the run;
the temporary app, proxy, and tunnel were stopped. Hecate returned to idle and
the production Herd was verified 7/7 online with no active requests.

Private raw Codex logs remain outside this repository. This report contains
only sanitized event counts and task outcomes.
