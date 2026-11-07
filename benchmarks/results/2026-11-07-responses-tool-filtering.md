# Herd Responses tool filtering: verified behavior

Date: 2026-11-07. This check investigated the `web_search` drop logged during
one isolated Codex coding task. It did not change or deploy Herd.

## Finding

Herd v0.12.3 intentionally removes hosted tools that have no local Ollama
equivalent, including `web_search`, `file_search`, and MCP tools. The adapter
logs a warning that names the dropped type. In the observed coding-task run,
`web_search` was dropped; this is an explicit capability gap, not evidence that
Herd accidentally lost Codex's executable tools.

The same translator expands Codex's default `functions` namespace and keeps
its callable tools, including `exec` and ordinary functions. It records other
namespaces as nested tools rather than independent functions. A direct check of
the v0.12.3 translator returned `exec_command` when given it alongside
`web_search`, and emitted the warning `Responses: dropped ... web_search`.

The input-history translator also converts a prior Responses `function_call`
into an Ollama assistant tool call and its matching `function_call_output` into
a tool message carrying the same call ID. Upstream has a focused conversation
continuity regression test for a complete call/result/follow-up sequence. This
supports the conclusion that the basic tool-result mapping exists; it does not
prove that no other history shape is lost in every live Codex request.

Finally, ordinary Ollama function-call names are emitted back as Responses
`function_call` items. The Codex 0.166.0 loopback diagnostic separately showed
that Codex rejects an unadvertised name such as `read_file` locally and returns
an unsupported-call result. Together these observations make model-selected
invalid names a plausible source of that specific error; they do not establish
what happened in the earlier historical `read_file` trace.

## Evidence and limits

- Source reviewed: Ollama Herd v0.12.3, upstream commit
  [`e0dac345515e8423e385ea2d465573a1e8b5a1bf`](https://github.com/geeks-accelerator/ollama-herd/tree/e0dac345515e8423e385ea2d465573a1e8b5a1bf).
- Relevant implementation: `src/fleet_manager/server/responses_translator.py`,
  `_expand_default_namespace`, `_tools_to_openai`, `responses_to_openai_body`,
  and `responses_input_to_messages`.
- Existing upstream tests cover hosted-tool removal, warning visibility,
  default-namespace exposure, and tool-call/result continuity in
  `tests/test_server/test_responses_translator.py`.
- A direct import-level check against the inspected source confirmed the hosted
  tool is absent from the Ollama request while `exec_command` remains.
- The prior isolated task log reported a `web_search` drop, but its raw router
  logs remain private. No raw prompts, arguments, messages, hostnames, or LAN
  details are included here.

The exact upstream pytest cases were inspected but not rerun in this check
because the local Python environment lacks Herd's test dependencies. This is
source and direct-function evidence, not a new full-suite run.

## Next diagnostic

Do not change the server translator to preserve hosted tools: Ollama has no
implementation for them. Next, use a minimal Codex tool fixture to distinguish
an unadvertised model-selected function name from an advertised tool whose
call/result continuation is malformed. Keep hosted web search out of claims
about local capability.
