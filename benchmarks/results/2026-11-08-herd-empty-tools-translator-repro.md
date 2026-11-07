# Herd tool-less request translation reproduction — 2026-11-08

This is a deterministic source-level reproduction against the tagged Herd
v0.12.3 code, not a live inference test. It checks whether the adapter can
return an executable Responses tool call after a request offered no tools.

## Setup

- Shallow checkout of upstream tag `v0.12.3`, peeled commit
  `e0dac345515e8423e385ea2d465573a1e8b5a1bf`.
- Imported the tagged `responses_translator` module directly. No service,
  model, or production configuration was used.
- Submitted a synthetic Responses request with `tools: []`, then passed a
  synthetic Ollama `exec_command` tool call through the response converter.

## Result

The converted OpenAI chat body had no `tools` field. The response converter
still emitted a Responses `function_call` named `exec_command` when
`known_names` was empty. The route only gets `_known_tool_names` when at least
one tool is translated, and its default for a missing value is an empty set;
the response converter treats an empty set as “unknown offered set” and lets
the call pass through. The upstream test
`test_unknown_offered_set_never_redirects` records that intentional behavior.

This establishes a reproducible adapter behavior that is consistent with the
five `exec_command` outputs on tool-less requests in the earlier HTTPie trace.
It does **not** establish that Ollama generated those calls, that Codex executed
them, or that they caused the inspection loop; the historical run did not
capture the Ollama-side request/response body.

## Candidate follow-up

The smallest candidate is to distinguish “no tools were offered” from “the
offered set is unknown” and reject or clearly surface any Ollama tool call not
in the explicit offered set. This is an upstream Herd adapter change, not a
`codex-herd` client change. It has not been patched, deployed, or tested against
an isolated full Herd service. The next validation should add streaming and
non-streaming regression tests to a disposable upstream checkout, then use a
separate held-out live task only if the isolated adapter tests pass.

## Source

The relevant code is pinned to
[Herd `responses_translator.py` at the peeled v0.12.3 commit](https://github.com/geeks-accelerator/ollama-herd/blob/e0dac345515e8423e385ea2d465573a1e8b5a1bf/src/fleet_manager/server/responses_translator.py).
