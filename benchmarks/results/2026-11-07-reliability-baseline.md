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
| [HTTPie #1958](https://github.com/httpie/cli/issues/1958), mixed-case JSON media type | MiMo-V2.6 9B Q4_K_M, 16K | Incomplete, 0/1 | Corrected run made 27 shell-command items, attempted unsupported `read_file` twice, no source/test edits; baseline 121 passed, 3 xfailed |
| [pytest #15341](https://github.com/pytest-dev/pytest/issues/15341), read-only parent cleanup | MiMo and Qwen3.8, 16K | Incomplete; duplicate fixture retired | A previous MiMo patch misplaced its regression inside another test and timed out without final; the later matched pair made no edits. The later preflight missed already-open [PR #15343](https://github.com/pytest-dev/pytest/pull/15343), so this is not a fresh task-family result. |

The Rich #4250 baseline issue was reproduced before inference; both profile
runs used identical code, task acceptance, test environment, and hard cap.
This straightforward task still produced repeated inspection without
implementation. It is one matched task, not proof that either model lacks
coding ability. The private evidence records direct reproductions, isolated
clones, event counts, and cleanup.

## Current diagnosis

- Tool transport is not the sole explanation: multiple runs successfully
  invoked Codex shell execution, and one MiMo task completed end to end.
- In the HTTPie #1958 run, Codex stderr records two
  `codex_core::tools::router` errors: `unsupported call: read_file`. The
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
