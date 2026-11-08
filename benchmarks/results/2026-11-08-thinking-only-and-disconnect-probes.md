# Thinking-only Responses and trace-proxy disconnect probes

**Date:** 2026-11-08 03:11 UTC
**Scope:** Deterministic offline protocol fixtures; no live inference or
production service changes.

## Herd thinking-only response

Added `probe_herd_thinking_only_route.py` for a disposable checkout of the
documented Herd v0.12.3 commit. The fake Ollama backend receives one advertised
`exec_command` tool, then returns a completed assistant message containing no
content or tool call and a private `thinking` sentinel.

Both streaming and non-streaming `/v1/responses` tests pass. Stock Herd returns
HTTP 200 and a completed Responses object with `output: []`; the `thinking`
field is ignored and its sentinel is not exposed. This confirms the adapter
shape Codex may see, but does not establish how Codex handles an empty completed
response or whether that shape caused a live inspection loop.

Reproduction from the pinned upstream checkout:

```sh
PYTHONPATH=src:. uv run pytest \
  /path/to/hades-herd/benchmarks/fixtures/probe_herd_thinking_only_route.py -q
```

Result: **2 passed**.

## Herd route disconnect

A second route test closes a streaming client after the first Responses event.
The pinned Herd v0.12.3 route cancels the `httpx.MockTransport` async backend
stream and releases the request's queue slot. Result: **3/3 route cases pass**
(two thinking-only modes plus the disconnect case). This verifies cancellation
propagation through Herd's in-process streaming route and queue using a mocked
backend. It does not establish whether a real Ollama server stops GPU
generation immediately after its HTTP stream is cancelled.

## Codex behavior on completed empty output

Extended the loopback mock Responses endpoint with an `empty_then_final`
scenario. Codex CLI **0.166.0** was launched through `codex-herd` in a fresh
temporary HOME/CODEX_HOME against that endpoint, with no hosted endpoint in the
profile. The first and only Responses request returned `response.completed`
with `output: []`.

Codex exited **0** and emitted `thread.started`, `turn.started`, and
`turn.completed` with zero input/output/reasoning tokens. It made no second
request and produced no assistant message. The mock's sanitized capture
contains one request and tool names only. This demonstrates that a completed
empty result is treated as a successful but blank Codex turn. In combination
with Herd's thinking-only route behavior, this is a plausible path to a blank
turn. It does not prove that the earlier live 231-token response had this
shape; that attempt's content/thinking shape was not captured.

Reproduction: start the mock with `--scenario empty_then_final`, set
`CODEX_HERD_URL` to its loopback URL, then run:

```sh
codex-herd mock-codex:latest exec --ephemeral --sandbox read-only \
  --skip-git-repo-check --json 'Return a short diagnostic.'
```

Use a fresh temporary HOME/CODEX_HOME as in the local trial, and inspect only
the sanitized mock summary plus Codex JSONL events.

## Codex trace proxy disconnect

The trace proxy previously continued draining an upstream SSE response after
its downstream Codex client disappeared. It now monitors downstream EOF, closes
the in-flight upstream response/connection, and records a sanitized summary
with `client_disconnected: true`. The new test uses a slow fake SSE upstream
and a raw loopback client that closes after response headers.

Result: the proxy records the disconnect, the fake upstream observes its
connection close, and the capture excludes the private response sentinel and
request content. Together, these probes show the diagnostic proxy and Herd's
in-process route propagate client cancellation to their upstream stream
interfaces. They do not prove that a real Ollama server stops GPU generation
immediately. The earlier backend reply that finished after Codex's timeout
cannot, by itself, be attributed to a Herd cancellation defect: the diagnostic
proxy had been fully draining that reply.

Focused proxy suite: **9 passed**.

## Candidate empty-response failure behavior

The route evidence supports a narrowly scoped candidate patch:
`patches/herd-v0.12.3-empty-response-failure.patch`. It converts an Ollama
`done:true` turn with no visible text or tool calls from `completed` to
`failed`, with an explicit error message. Existing `done_reason: length`
responses remain `incomplete`. This prevents Codex from presenting an empty
model response as an apparently successful blank turn.

In the disposable v0.12.3 checkout, **64 targeted translator/route tests
passed**, including stream and non-stream failure shape, cancellation, and
preserved length behavior. The full upstream suite plus candidate tests passed
**1,990 tests, 5 skipped** (3 existing queue-manager warnings). Codex 0.166.0
against the deterministic `empty_failed` mock exited **1**, emitted a visible
error and `turn.failed`, and made one request. Compared with the stock empty
completion, it no longer reports a blank successful turn. It does not retry or
recover, and it is not evidence of improved coding-task success.

The patch remains unapplied and unsubmitted upstream. It should be reviewed as
a user-visible failure-reporting change before any deployment; no production
Herd behavior was changed. Exact patch and application notes are in
[`fixtures/patches/`](../fixtures/patches/README.md).

## Next

Next, review the candidate error behavior and measure whether real Ollama
generation stops after Herd cancels its HTTP request, without using production
traffic. The adapter patch remains a review artifact only.
