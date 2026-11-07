# Benchmark method

## Pass definitions

- **Autonomous pass@1:** Codex's task turn completes; required source changes
  exist; requested tests pass; independent review confirms behavior; no human
  implementation or correction was needed.
- **Patch-only incomplete:** A useful patch exists, but Codex timed out or did
  not produce a final response, or required tests were not completed.
- **Retry-assisted:** A same-thread retry completes after a first failure. Keep
  separate from pass@1.
- **Human-corrected:** An operator fixes implementation or tests. Do not count
  as a model pass.
- **Invalid setup:** The task, test environment, or timeout was inaccessible or
  incorrect. Exclude from model-quality counts and repair the harness first.

## Required controls

Use a fresh disposable clone/worktree and record the exact starting commit.
Put all instructions and test environments inside the permitted workspace.
Verify the reported failure and baseline tests before inference. Use the actual
Codex CLI through the intended local endpoint and an enforced OS timeout.
Preserve event stream, standard error, start/finish timestamps, exit status,
model digest/quantization, context allocation, and runtime versions. Independently
review diff and rerun tests after the agent. Unload model and release the node.

A tool call or passing API smoke is not a task pass. A patch without a final
Codex turn is incomplete. Never combine task results across changed fixtures or
contexts. Public results must be sanitized and contain no raw transcripts,
private network details, prompts with user data, or credentials.

See [`results/2026-11-07-reliability-baseline.md`](results/2026-11-07-reliability-baseline.md)
for a concise baseline.
