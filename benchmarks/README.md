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

## Deterministic Codex tool-router check

`fixtures/mock_codex_tool_router.py` is a loopback-only mock for separating a
Codex tool-router rejection from real model behavior. It advertises one mock
model and returns an undeclared `read_file` function call, followed by a normal
final response. It records only the tool names Codex advertised, whether
Codex sent an unsupported-call output, the scalar `reasoning.effort`, and
whether a `think` field was present. It does not save prompts, full tool
schemas, or other request fields.
It never contacts Herd or an Ollama backend.

Run the mock in one terminal:

```sh
python3 benchmarks/fixtures/mock_codex_tool_router.py --port 8765
```

In a second terminal, use an isolated Codex home and the repository helper:

```sh
tmp_home="$(mktemp -d)"
CODEX_HERD_URL=http://127.0.0.1:8765 \
HOME="$tmp_home" CODEX_HOME="$tmp_home/codex" \
python3 codex_herd.py mock-codex:latest exec --ephemeral --sandbox read-only \
  --skip-git-repo-check --json "Return a short diagnostic."
```

The expected behavior with Codex CLI 0.166.0 is an `unsupported call:
read_file` error, no tool execution, a synthetic unsupported-call result in
the next request, then the mock's `Diagnostic complete.` final response. The
sanitized request summary defaults to
`/tmp/codex-tool-router-capture.json`. This establishes the client's rejection
of a function name that was not advertised. It does not prove what a real model
emitted or whether Herd's output translator caused that name; use an Ollama-side
request/response trace to establish that.
