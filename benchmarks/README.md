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

### Protocol controls

`fixtures/protocol-control/` contains small synthetic tasks used only to check
Codex/Herd request behavior. They are not model-quality benchmarks and their
results must not be added to the coding leaderboard. The first full-tool
control and its limits are recorded in
[`results/2026-11-08-full-tools-protocol-control.md`](results/2026-11-08-full-tools-protocol-control.md).
The historical empty-tool trace shape is compared with that control in
[`results/2026-11-08-empty-tools-request-shape.md`](results/2026-11-08-empty-tools-request-shape.md).
The loopback Codex boundary probe compares a synthetic forwarded tool call with
the proposed visible no-tool response; it is a protocol control, not a live
Herd/model result. See
[`results/2026-11-08-empty-tools-codex-boundary-probe.md`](results/2026-11-08-empty-tools-codex-boundary-probe.md).
The full Herd route was then compared against fake Ollama on stock and guarded
v0.12.3 for both streaming modes. See
[`results/2026-11-08-herd-empty-tools-route-paired.md`](results/2026-11-08-herd-empty-tools-route-paired.md),
the [route probe](fixtures/probe_herd_empty_tools_route.py), and the
[unapplied patch](fixtures/patches/README.md).

A bounded real Codex run then exercised the guarded route on the previously
failing HTTPie #1958 task. It timed out and its independent tests failed, so it
is not a model pass or evidence that the guard improves autonomy. See the
[sanitized live attempt](results/2026-11-08-guarded-httpie-1958-live-task.md).

The [thinking-only route probe](fixtures/probe_herd_thinking_only_route.py)
and [disconnect probe report](results/2026-11-08-thinking-only-and-disconnect-probes.md)
cover the deterministic response-shape checks. Herd v0.12.3 returns a
completed empty Responses output for thinking-only Ollama output, and Codex
0.166.0 completes a blank turn without retrying when given that shape by a
loopback mock. The trace proxy now detects downstream EOF and closes its
upstream stream; this does not verify cancellation in Herd or Ollama.

### Ollama-side metadata capture

`fixtures/trace_ollama_chat.py` is a loopback-only forward proxy for an isolated
Herd test node. Point that test node's `ollama_host` at the printed proxy
address and set `--upstream` to the node's direct Ollama endpoint (or a local
SSH tunnel). It forwards request and response payload bytes without recording
them. It asks Ollama for an uncompressed response so streamed JSONL metadata
can be observed; it does not alter the JSON request body.
For `/api/chat`, the mode-0600 JSONL capture contains only model name, stream
mode, tool-field presence/count/names, message count, response tool-call
count/names, whether `content` and `thinking` fields appeared, their aggregate
character counts, completion reason/token counters, status, and monotonic
timings. It never records prompts, tool schemas, arguments, message content,
or headers.
The proxy binds to `127.0.0.1` only and refuses to overwrite an existing
capture file.

```sh
python3 benchmarks/fixtures/trace_ollama_chat.py \
  --upstream http://127.0.0.1:21434 --port 0 \
  --capture /tmp/ollama-chat-metadata.jsonl
```

The chosen port is printed at startup. Use the proxy only in the disposable
test app, never by changing a production Herd node. Offline tests verify that
streamed bodies are forwarded unchanged, explicit `tools: []` stays distinct
from an omitted `tools` field, and prompt/schema/argument/content sentinels do
not enter the capture.

To reproduce the paired route test, use a disposable checkout of the pinned
upstream Herd source and its dev environment:

```sh
git clone https://github.com/Niko1221/ollama-herd /tmp/ollama-herd-probe
cd /tmp/ollama-herd-probe
git checkout e0dac345515e8423e385ea2d465573a1e8b5a1bf
uv sync --extra dev
HERD_EMPTY_TOOLS_EXPECTED=stock PYTHONPATH=src \
  uv run pytest /path/to/hades-herd/benchmarks/fixtures/probe_herd_empty_tools_route.py -q
git apply /path/to/hades-herd/benchmarks/fixtures/patches/herd-v0.12.3-empty-tools-guard.patch
HERD_EMPTY_TOOLS_EXPECTED=guard PYTHONPATH=src \
  uv run pytest /path/to/hades-herd/benchmarks/fixtures/probe_herd_empty_tools_route.py -q
```

The fixture uses Herd's in-process test app and an `httpx.MockTransport`, so it
does not open a port or start mDNS. Run only in the disposable checkout; the
patch is a candidate for review, not a production deployment instruction.

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

`fixtures/run_empty_tools_guard_probe.py` runs two bounded Codex CLI sessions
against a loopback Responses mock. It checks whether Codex executes a returned
`exec_command` function call or stops on a visible assistant message. The mock
labels the simulated backend tool offer as empty; Codex's own request in this
control still contains tool definitions. See the linked result report for
limits and exact outcomes. This probe makes no model requests.

For reasoning experiments, the fixture records only the scalar
`reasoning.effort` and whether a `think` field is present. The committed client
catalog intentionally advertises no effort levels until the server mapping is
verified. The mock cannot establish what Herd sends to Ollama; the result report
records a separate no-inference translator check.

### Timestamped Codex event capture

`fixtures/capture_codex_jsonl.py` runs one bounded child process, preserves raw
Codex JSONL stdout and stderr in mode-0600 files, enforces a process-group
timeout, and writes a separate metadata-only event timeline. The timeline
contains only monotonic timestamps plus event/item type and item status; it
omits IDs, commands, arguments, outputs, and message text. Output paths must
not already exist. The proxy's `request_sequence` and
`response_finished_monotonic_ns` fields use the same host monotonic clock, so
the timeline can be compared to Responses completion events when both run on
the same workstation.

Example from a disposable task worktree, with the trace proxy already running:

```sh
python3 /path/to/hades-herd/benchmarks/fixtures/capture_codex_jsonl.py \
  --timeout 180 --input AGENT_TASK.md \
  --stdout run/codex-events.jsonl --stderr run/codex-stderr.txt \
  --timeline run/codex-event-index.jsonl --summary run/capture-summary.json \
  -- env CODEX_HERD_URL=http://127.0.0.1:8766 \
  python3 /path/to/hades-herd/codex_herd.py MODEL exec --json \
  --sandbox workspace-write --config 'approval_policy="never"' -- -
```

Keep `codex-events.jsonl` and `codex-stderr.txt` private: they can contain
commands, model output, or task text. Publish only reviewed aggregate results
and the content-free event index.

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

The first live use was a held-out HTTPie #1965 task. Codex exposed
`exec_command` and `write_stdin`; the model requested `exec_command` and then
an unadvertised `read` tool. The guarded adapter suppressed it and returned a
notice; Codex ended without a patch. This identifies a concrete
unsupported-tool selection but does not explain its cause. See the
[sanitized result](results/2026-11-08-heldout-httpie-1965-live-attempt.md).

The follow-up with explicit per-model developer instructions avoided a model
tool call, but Codex completed with no visible message or repository change.
The observer had recorded token counts but not content/thinking presence or
lengths, so that attempt cannot distinguish an empty response from hidden
reasoning or an adapter issue. The observer now records those shape metrics
without text; see the
[follow-up report](results/2026-11-08-guided-httpie-1965-followup.md).
An instrumented same-input repetition then timed out after 17 Codex tool turns.
All 18 observed Ollama responses had empty content; 13 included thinking, with
44,418 thinking characters total. The last backend response completed after
Codex's hard timeout. This is a failed diagnostic, not a pass; see the
[response-shape report](results/2026-11-08-guided-httpie-1965-response-shape.md).

### Correlating tool calls with Codex events

After one captured run, combine the proxy summary with the content-free Codex
event index:

```sh
python3 benchmarks/fixtures/correlate_codex_trace.py \
  /path/to/codex-herd-trace-summary.json \
  /path/to/codex-event-index.jsonl > /path/to/correlation.json
```

The reducer matches Responses requests and events using same-workstation
monotonic timestamps. It reports command starts/completions in the interval
after a response finishes and before the next Responses request begins. If
those requests overlap, it leaves the interval unassigned. The output contains
request sequence numbers, tool counts/names, event counts, and response status;
it never includes IDs, commands, prompts, arguments, or tool results. Timing
proximity is not an ID-level match, so parallel commands or overlapping model
requests still require cautious interpretation. Historical captures without
timestamps are rejected rather than guessed.
The result also reports total command starts/completions, counts assigned to
non-overlapping response windows, and counts left unassigned. Events before
the first response window and events in overlapping windows therefore remain
visible in aggregate counts without unsupported call-level attribution.
