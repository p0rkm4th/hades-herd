# Sanitized local Codex/Herd reliability baseline — 2026-11-07

This report summarizes isolated disposable-repository runs. It excludes raw
prompts, shell transcripts, private hostnames, addresses, access data, and
unredacted logs. Public issues are linked so an independent reviewer can inspect
the task definition. The profiles ran through Codex CLI 0.166.0 and Herd 0.12.3;
model contexts and digests are recorded below. Ollama was 0.40.15 on the
private fleet at the time of these runs.

| Task | Profile | Result | Observed behavior |
|---|---|---|---|
| [HTTPie #1960](https://github.com/httpie/cli/issues/1960), repeated-header ordering | MiMo-V2.6 9B Q4_K_M, 16K | Complete pass@1; ~126 s | Patch and regression completed; focused and independent module verification passed 122 tests, 3 expected xfails |
| HTTPie #1960, same task | Qwen3.8 27B Q4, 16K | Incomplete, 0/1 | Core edit and smoke output existed, but the 180 s turn ended before tests/final review; 300 s retry still ended before final completion and required a test expectation correction |
| [Rich #4250](https://github.com/Textualize/rich/issues/4250), `FileProxy.write` return count | MiMo-V2.6 9B Q4_K_M, 16K | Incomplete, 0/1 | 180 s timeout; 22 shell calls, repeated reads of the same source/tests, no edits; baseline focused suite 15 passed |
| Rich #4250, matched | Qwen3.8 27B Q4, 16K | Incomplete, 0/1 | 180 s timeout; two shell calls, no edits; generation was observed near 11.1 tokens/s; baseline 15 passed |
| [HTTPie #1958](https://github.com/httpie/cli/issues/1958), mixed-case JSON media type — 15:50 untraced attempt | MiMo-V2.6 9B Q4_K_M, configured 16K | Incomplete, 0/1 | 27 shell-command items; Codex logged two unsupported `read_file` calls; no source/test edits; baseline 121 passed, 3 xfailed |
| [pytest #15341](https://github.com/pytest-dev/pytest/issues/15341), read-only parent cleanup | MiMo and Qwen3.8, 16K | Incomplete; duplicate fixture retired | A previous MiMo patch misplaced its regression inside another test and timed out without final; the later matched pair made no edits. The later preflight missed already-open [PR #15343](https://github.com/pytest-dev/pytest/pull/15343), so this is not a fresh task-family result. |

The Rich #4250 baseline issue was reproduced before inference; both profile
runs used identical code, task acceptance, test environment, and hard cap.
This straightforward task still produced repeated inspection without
implementation. It is one matched task, not proof that either model lacks
coding ability. The private evidence records direct reproductions, isolated
clones, event counts, and cleanup.

## Current diagnosis

- The two HTTPie #1958 observations below came from separate runs. The 15:50
  no-proxy attempt logged two unsupported `read_file` calls; the 19:42 traced
  attempt had no such call or Codex rejection, but did include requests with
  `tools: []`. They share the task fixture, not a Codex session or a
  call-level trace. Do not infer that the unsupported calls occurred on the
  empty-tool requests.
- Tool transport is not the sole explanation: multiple runs successfully
  invoked Codex shell execution, and one MiMo task completed end to end.
- In the 15:50 HTTPie #1958 run, Codex stderr records two
  `codex_core::tools::router` errors: `unsupported call: read_file`. This is
  the earlier 15:50 untraced run. The separate 19:42 wire trace did not
  contain `read_file`. The
  exported event stream contains shell command events but not the rejected
  call payload or the Responses request/response body. This proves Codex's
  local tool router rejected that name; it does not establish whether the model
  emitted an undeclared name or Herd altered the advertised schema. Capture a
  sanitized tool-schema and function-call trace before changing the adapter.
- A loopback deterministic fixture now advertises Codex's actual tool catalog,
  then returns an undeclared `read_file` call. Codex 0.166.0 reproduced the
  same local `unsupported call` rejection, did not execute the call, included
  a synthetic unsupported-call result in the next request, and accepted the
  subsequent final response. Its first capture listed eight top-level named
  entries and did not include `read_file`. This validates the Codex-side
  mechanism, not the origin of the name in the real MiMo trace. See the reproducible
  [fixture instructions](../README.md#deterministic-codex-tool-router-check).
- The fixture's sanitized catalog shape shows seven top-level function tools,
  one `multi_agent_v1` namespace with five nested tools, and one `web_search`
  hosted tool. None is `read_file`. A no-inference call to the installed Herd
  0.12.3 translator preserved representative function definitions, kept nested
  namespace tools out of the direct function list, and returned an Ollama
  `read_file` tool name unchanged as a Responses `function_call`. The most
  likely cause is that the model emitted an undeclared name; the real Ollama
  call item was not captured, so this remains a probable rather than proven
  attribution. The reviewed implementation is Ollama Herd's
  [`v0.12.3` Responses translator](https://github.com/geeks-accelerator/ollama-herd/blob/v0.12.3/src/fleet_manager/server/responses_translator.py).
- A separate no-inference translation check showed that a prior Codex
  `function_call` and its matching `function_call_output` become an assistant
  tool call and a tool message with the same call ID and unchanged result
  content. With tools present, Herd also appends its existing turn-completion
  guidance to the system message. This lowers the likelihood of lost tool
  results or absent preamble guidance as causes for repeated inspection or
  missing final turns, but does not rule out truncation, compaction, or model
  behavior in a real run.
- A read-only source audit of Herd 0.12.3 found that the Responses route
  translates and stores the incoming tool definitions in the request body;
  the streaming path retains that body for Ollama. Herd has targeted repairs
  for a couple of known call patterns, but no general repair for arbitrary
  unknown tool names. This makes a model-emitted undeclared name plausible; the
  real Ollama response body was not captured, so this is not proven.
- Reasoning control was tested with the same loopback mock and isolated Codex
  home. The helper's generated catalog advertises no reasoning levels, and the
  request carried neither `reasoning.effort` nor Ollama's `think` field. After
  manually adding only `low` to that disposable model entry and selecting
  `model_reasoning_effort = "low"` in its generated profile, Codex sent
  `reasoning.effort: "low"`; it still did not send `think`. This proves the
  client can emit the Responses field when its catalog advertises support, not
  that Herd 0.12.3 forwards or maps it. The local Codex profile exposes no
  control because Herd does not currently demonstrate that mapping. Codex's
  [configuration reference](https://developers.openai.com/codex/config-reference)
  documents `model_reasoning_effort`; Ollama's [thinking API](https://github.com/ollama/ollama/blob/main/docs/capabilities/thinking.mdx)
  accepts a boolean or an exact model-supported level. A safe adapter change
  would need to map only values confirmed by the selected model's metadata and
  leave the default request unchanged.
- A no-inference call to the installed Herd 0.12.3
  `responses_to_openai_body` translator with a synthetic Responses request
  confirmed the conversion boundary: the output retained the function tool
  and message body, but had neither `reasoning` nor `think`. The route stores
  this translated body for inference and the streaming path uses that body.
  This localizes the missing control to Herd's Responses-to-chat translation;
  the actual downstream `/api/chat` network body was not intercepted. The
  unsupported `read_file` response remains a separate question: no event trace
  captured the real model's emitted function-call item.
- Repeated reads may reflect model planning, task prompting, or context/state
  handling. Existing evidence does not identify the cause.
- The installed Herd Responses adapter's Codex catalog advertises no reasoning
  levels, and the current integration was observed not to forward Codex
  `reasoning.effort` or Ollama's native `think` field. A prompt-level Qwen
  `/no_think` attempt was not verified as changing the actual request. No
  reasoning default was changed.
- Some prior runs had invalid sandbox paths, missing dependencies, or
  unverified timeouts. Those are harness defects and are excluded from model
  pass rates.

Next: inspect sanitized wire-level tool schemas/results and Herd conversation
reconstruction, then make a deterministic minimal reproducer. No model default,
production routing, or server behavior changed as part of this baseline.

## Follow-up: bounded inspection instruction (2026-11-07)

One additional MiMo/Hecate trial used the same disposable Rich checkout at
`3a109ccdffe5b2d0e30684a304fbd388e99ce57b`, same task, Q4 digest, 16K
context, workspace-write sandbox, no-approval policy, and 180-second OS timeout
as the prior MiMo Rich attempt. The only changed variable was a developer
instruction limiting pre-edit inspection to two shell commands and requiring
the first edit within those calls. Focused preflight: 15 tests passed. Result:
Codex timed out (exit 124) after 22 shell calls, 21 unique command hashes,
one repeated command, and no source or test edits. Four command items failed;
18 completed successfully. The trial did not establish why inspection
continued, and the instruction did not fix it. It is excluded from any model
pass-rate or model ranking and this exact fixture will not be retried. Private
run data remains on the workstation; no raw Codex events or commands are
published. No production configuration changed.

## Live HTTPie #1958 Responses trace (2026-11-07)

A fresh isolated Codex CLI 0.166.0 run on the same public issue/task and HTTPie
base commit `5b604c37c6c67e18e7c3e9aee6c88a8c22b98345` used the loopback
metadata-only proxy. The focused baseline again passed 121 tests with 3
expected xfails. MiMo 9B Q4 / configured 16K / workspace-write / no approvals /
180-second OS timeout remained unchanged. The task turn timed out (124) with no
code or test edits after 27 unique shell calls. This is incomplete and not a
model pass.

The proxy saw 30 `/v1/responses` calls; all returned HTTP 200. Response items
included 21 `function_call` and 13 `message` items. All function-call names
were `exec_command`; no `read_file` response item or Codex unsupported-call
error occurred in this attempt. Across these calls, 16 requests contained nine
top-level tool entries and 14 carried an empty `tools` array. Five of the 14
empty-list requests returned `exec_command`; the remaining nine returned
messages. Each request carried full stateless input: 26 prior function-call
items and 26 tool outputs were observed, with no `previous_response_id`.
The Responses usage counters totalled 114,472 input tokens and 12,293 output
tokens. The deployed Herd 0.12.3 translator source supports both top-level
`tools` and Codex `additional_tools` input items; this capture used only the
top-level field. An earlier trace parser failed to account for those alternate
locations; v2 corrected that parser and supersedes its incomplete catalog
counts. Source audit reference: [Herd v0.12.3 Responses translator](https://github.com/geeks-accelerator/ollama-herd/blob/v0.12.3/src/fleet_manager/server/responses_translator.py).

An offline count of the same run's local Codex JSON event stream found 27
completed `command_execution` items, while the proxy summary captured 21
Responses `function_call` items. The six-item difference is not reconciled:
the two artifacts have no shared response/call correlation key, and the raw
event stream contains command text that is intentionally not published. All
14 empty-tool requests explicitly carried `tools: []`; none carried
`additional_tools`, and none set `tool_choice`. The Responses API defines
`tools` as the array of tools the model may call ([official reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)).
Five of their responses contained an `exec_command` item, but the count
mismatch means we cannot establish which calls corresponded to executed shell
commands. The review branch now adds monotonic request/response timestamps to
the proxy and a process-group-bounded Codex JSONL capture helper that stores raw
streams privately and emits a content-free event timeline. This instrumentation
has passed offline tests but has not yet been used in a live model run.

This run does not reproduce the historical unsupported `read_file` event and
does not explain why the task stalled. In particular, it does not prove that
empty tool lists caused the repeated investigation or that the model's tool
selection was invalid. It establishes that Codex/Herd successfully exchanged
stateless call/result history while some requests omitted tool definitions;
what that pattern means for model behavior remains open. Raw requests,
responses, arguments, commands, and prompts were not published.
