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

## Local model coding reliability

`run_local_reliability.py` creates a fresh temporary Git repository per task,
checks baseline tests, launches the installed Fish `codex-herd` command with a
fresh HOME and explicit local model, then runs pytest and independent contract
checks. It removes hosted API credentials, caps each run at 180 seconds, kills
the process group on timeout, and emits only sanitized event counts and test
results. Raw Codex output and task workspaces are not retained. The fixtures
are in `fixtures/local_coding_reliability.py`.

Example:

```sh
python3 benchmarks/run_local_reliability.py \
  --model mimo-v26-9b-codex-16k-hecate:latest --context 16384 --phase full
```

The runner uses an installed pytest or an isolated `uv run --with pytest`
environment; it does not install packages globally. A pass requires a completed
Codex turn, allowed source edits, passing pytest, and a separate contract check.
The human-readable scorecard records exact tested model IDs and the limits of
the small fixtures. Do not treat it as a substitute for a user's project tests.

## Deterministic Codex tool-router check

`fixtures/mock_codex_tool_router.py` is a loopback-only mock for separating a
Codex tool-router rejection from real model behavior. It advertises one mock
model and returns an undeclared `read_file` function call, followed by a normal
final response. It records only the sanitized top-level and nested tool names
and types, whether Codex sent an unsupported-call output, the scalar
`reasoning.effort`, and whether a `think` field was present. It does not save
prompts, full tool schemas, or other request fields.
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

For reasoning experiments, the fixture records only the scalar
`reasoning.effort` and whether a `think` field is present. The committed client
catalog intentionally advertises no effort levels until the server mapping is
verified. The mock cannot establish what Herd sends to Ollama; the result report
records a separate no-inference translator check.

## Sanitized live Responses trace

`fixtures/trace_codex_herd.py` is an optional loopback-only forwarding proxy for
one bounded Codex/Herd diagnosis. It forwards request and streamed response
bytes unchanged. The summary records only HTTP status/path, advertised tool
names and nesting, reasoning-effort enum, input item counts, prior tool-call
names/result counts, response item types/function names, terminal status, and
token counts. It never writes message text, tool schemas, arguments, tool
results, response text, IDs, or request headers. Raw request/response bodies
exist only in process memory while being forwarded. `read_file` names are
captured on both sides so a Codex-local rejection can be compared with what
Herd returned to Codex.

Run it with the private upstream URL supplied only in the local environment:

```sh
HERD_TRACE_UPSTREAM="http://<private-herd-host>:11435" \
  python3 benchmarks/fixtures/trace_codex_herd.py --port 8766 \
  --capture /tmp/codex-herd-trace-summary.json
```

In the isolated Codex process, set `CODEX_HERD_URL=http://127.0.0.1:8766`.
The helper's discovery calls and Responses API are transparently forwarded;
the Codex-generated provider profile points back through the proxy. The proxy
rejects upstream URLs with embedded credentials and binds only to `127.0.0.1`.
Do not publish raw Codex logs from a trial. Verify the summary has no task text
before sharing it. The fixture requires no model download and does not change
Herd or Ollama configuration.
