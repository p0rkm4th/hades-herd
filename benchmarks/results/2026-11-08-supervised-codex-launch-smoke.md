# Supervised Codex launch smoke — 2026-11-08

## Purpose

Verify the pushed model-specific launcher profiles with the installed Codex CLI
and real Ollama inference through Herd. This is a matched integration smoke,
not the five-task supervised daily-driver acceptance suite.

## Method

- Codex CLI 0.166.0; isolated temporary HOME/CODEX_HOME for each run.
- Fresh disposable Git repository with the same task, task instructions, and
  five standard-library tests for both models.
- `workspace-write` sandbox, approval policy `never`, and a 180-second process
  timeout. No hosted credentials, provider fallback, model downloads, or
  production configuration changes.
- Task: implement integer duration formatting as unbounded `H:MM:SS`, with
  negative values and type validation. The model was instructed not to change
  tests.
- Independent verification checked the final diff, ran all five tests, and
  checked the generated per-model catalog context.

## Results

| Profile | Codex turn | Tool calls | Independent tests | Approximate elapsed time | Result |
|---|---:|---:|---:|---:|---|
| MiMo-V2.6 9B Q4, configured 16K | Completed with final response | 4 successful shell commands | 5/5 passed | 8 seconds | Pass |
| Qwen3.8 27B Q4, configured 16K | Completed with final response | 5 successful shell commands | 5/5 passed | 97 seconds | Pass |

The exact elapsed durations were not instrumented; these are approximate
process timings. Both generated Codex catalogs advertised 16,384 tokens, and
both isolated profiles used the Herd Responses API. Diffs changed only the
requested implementation file. No human correction was needed.

The first MiMo invocation used an obsolete approval flag and exited before
inference. It is excluded; the successful invocation used Codex's supported
`--config approval_policy="never"` override. The fixture suite is small and
synthetic. These two matched runs establish that both launch paths can execute
tools, edit code, pass tests, and complete a turn; they do not establish broad
coding reliability or count toward the five varied-task acceptance suite.

## Installed Fish command check

A separate path check then used the actual installed Fish `codex-herd`
function from a disposable project directory. The fast model again edited the
fixture, made five successful shell calls, completed the turn in about 15
seconds, and passed all five independent tests. The generated profile selected
the explicit model through Herd's Responses API at the saved 16K context. The
saved default remained unchanged. This repeats the same small task and confirms
the workstation command path; it is not another distinct acceptance task.

After each run, the model was unloaded and the host GPU returned to idle. Herd
reported 7/7 nodes online with no queued or in-flight requests.
