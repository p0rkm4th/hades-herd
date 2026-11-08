# Held-out HTTPie #1965 live attempt

**Date:** 2026-11-08 02:23 UTC  
**Model:** MiMo-V2.6 9B Q4_K_M, digest `47f141d59fb9ece0a349cf27e8292b8c192ae0087b2a051c2e29c06526feea4b`  
**Context:** 16K configured  
**Codex CLI:** 0.166.0  
**Task base:** `5b604c37c6c67e18e7c3e9aee6c88a8c22b98345`

This was one bounded held-out task after the guarded HTTPie #1958 attempt. The
fresh detached worktree reproduced issue #1965: malformed brace-prefixed JSON
`{{"a": 1}` was misidentified as an in-body prefix. Before inference,
`tests/test_output.py` passed **121 tests with 3 expected xfails**. The task
asked Codex to fix the prefix detection, add focused regression tests, and run
that suite.

## Result

The process exited 0 after 7.0 seconds, but this was **not a task pass**. Codex
issued two ordinary repository-inspection shell commands, then the model tried
to call a `read` tool that was not offered by Codex. The guarded Herd adapter
suppressed that call and returned the visible notice “No tool was run because
the model requested a tool not advertised for this turn.” Codex ended the turn
without continuing the task. The worktree contains no source or test changes;
only the pre-run task instructions are untracked. No requested test was run by
the agent.

The content-free Codex trace confirms the offered tools included `exec_command`
and `write_stdin`, but not `read`. Its corresponding Ollama metadata capture
shows the first backend response requested `exec_command`; the next requested
`read`. The payloads and arguments were not recorded in the published traces.
This directly confirms an unsupported-tool selection in this run. The Codex
request contained the tool catalog; the Ollama request contained a translated
seven-tool subset, including `exec_command`. Herd did not remove `read` from a
tool list Codex had offered; `read` was not offered. The run does not establish
why the model selected it. The disposable adapter also logged that it dropped
the untranslatable `web_search` entry from Codex's catalog. This separate
translation limitation and the later guided attempt are described in the
[follow-up report](2026-11-08-guided-httpie-1965-followup.md).

The operator independently reran the unchanged focused suite after the agent:
**121 passed, 3 xfailed** in 15.75 seconds. The source bug therefore remains
unfixed. Classify this as a valid live agent attempt with an unsupported-tool
failure, not an invalid setup, patch-only result, or autonomous pass. Do not
combine it with the earlier #1958 task score: the issue, task, and trial
conditions differ.

## Runtime and cleanup

The run used a fresh temporary HOME, workspace-write sandbox, approval policy
`never`, a 180-second process-group timeout, and only loopback proxies to a
disposable Herd v0.12.3 test app and the existing Hecate Ollama server over a
strict-key SSH tunnel. No hosted credentials, downloads, production routing,
or HADES provider settings were used. Raw Codex logs remain private.

Afterward, the model was stopped; Hecate reported 5 MiB GPU memory use. The
test app, both metadata proxies, and SSH tunnel were stopped. Production Herd
remained unchanged. The source patch is not available because no edits were
made.

## Next diagnostic

Keep the current tool catalog and task definition. In a deterministic isolated
fixture, test whether an unsupported tool name is selected when the model sees
the complete task instructions and the actual advertised tool list. Compare
the model's requested tool name with the offered names at both the Codex and
Ollama boundaries. Change one supported input at a time; do not add an alias
or custom harness tool merely to hide the mismatch. Revisit task performance
only after the unsupported-tool behavior has a reproducible cause or a
validated, minimal mitigation.
