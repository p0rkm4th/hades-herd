# Codex advertised-tool round trip

Date: 2026-11-07. Codex CLI 0.166.0 was tested against the loopback-only
Responses mock, with a fresh temporary `HOME` and `CODEX_HOME`, explicit
loopback `CODEX_HERD_URL`, no model, no hosted credentials, and a 45-second OS
timeout.

## Result

**PASS.** The fixture observed `exec_command` in Codex's advertised tool list,
returned one call with the harmless command `printf tool-roundtrip-ok`, and
received a matching `function_call_output` on request two. The returned result
contained the expected marker, had no unsupported-call marker, and Codex emitted
`turn.completed`. The request summary captures only names/types, presence
booleans, and the fixed output marker check; it retains no command output or
raw schemas.

The existing `unsupported-call` scenario was rerun with the same CLI. It also
completed its mock turn after returning Codex's synthetic unsupported-call
result for `read_file`, which was absent from the advertised tool list. Thus
Codex's local error recovery differs observably from a valid advertised tool
execution.

## Interpretation

This verifies Codex CLI's advertised function dispatch and continuation against
a deterministic Responses server. It does not test Herd, Ollama, or model
behavior. It makes a Codex CLI tool-router defect less likely for this valid
function shape; it does not rule out Herd stream translation errors on a live
request. The Herd source review and adapter evidence remain separate.

During fixture development, the first mock call used Codex's older custom
`exec` shape. The installed CLI 0.166.0 did not advertise that tool and
correctly rejected it. The capture was expanded to read Codex's current
`additional_tools` input structure, revealing `exec_command` as the callable
function, and the diagnostic was corrected. That initial invalid call is not
counted as a pass.

Reproduce using the steps in the [benchmark guide](../README.md#deterministic-codex-tool-router-check).
