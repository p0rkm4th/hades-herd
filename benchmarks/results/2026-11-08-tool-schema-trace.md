# Tool schema trace instrumentation — 2026-11-08

## Purpose

The public code review noted that empty tool lists on some Codex Responses
requests did not, by themselves, establish whether Herd changed or omitted
tool definitions before sending requests to Ollama. The existing Codex-side
trace intentionally discarded full schemas, and no corresponding Ollama-side
observer existed.

## Change

The trace fixtures now normalize both Codex Responses function definitions and
Ollama `/api/chat` definitions into bounded structural summaries. Captured
fields are function names, schema types, property names/types, required keys,
and limited structural markers. Descriptions, defaults, enum/example values,
other schema constraints, prompts, tool arguments/results, and response text
are not recorded. Property and nested-tool traversal is bounded; capture files
remain mode `0600`, and both observers bind only to loopback.

## Verification

- The initial feature branch passed 32 offline unit tests on Python 3.14.
- Both trace fixtures passed `py_compile`.
- `git diff --check` passed.
- Tests cover equivalent OpenAI/Ollama schema summaries, omission of schema
  values, same-name call ordering, explicit empty versus absent tools,
  unchanged stream forwarding, loopback restrictions, and recursion/size caps.

No live inference was performed with these changes. The trace pair has not yet
been used to compare a single request across Herd's adapter. Therefore this
work improves observability but does not establish that schema translation is
the cause of empty-tool-list requests, unsupported tool attempts, or agent
inspection loops.

## Pinned adapter route check

On the updated review branch, the complete offline client suite passed 43
tests. A separate fixture was then run against a clean extracted Ollama Herd
v0.12.3 source tree (`e0dac345515e8423e385ea2d465573a1e8b5a1bf`) with its own
existing development virtual environment. The real in-process Responses route
and `httpx.MockTransport` passed 1/1 test: a representative function schema's
normalized structure was unchanged when it reached the fake Ollama `/api/chat`
boundary. No inference or network listener was involved. The test emitted only
pytest's existing async-fixture deprecation warning.

This narrows the schema-loss hypothesis for the tested function shape; it does
not cover every Codex tool schema or prove the exact shape seen by the model in
a historical run. A paired live trace would still be needed for that stronger
claim.
