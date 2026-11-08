# Empty-tool request shape analysis — 2026-11-08

Offline analysis of the content-free metadata from the stalled HTTPie #1958
trace, compared with the later full-tool protocol control. This uses only
request item types, catalog counts, token counters, and response item types;
no prompts, command text, arguments, or tool results were read or published.
The two `read_file` rejections reported elsewhere came from a separate earlier
no-proxy attempt on the same issue; they are not present in this wire trace and
cannot be correlated with these empty-tool requests.

| Observation | HTTPie #1958 stalled trace | Full-tool control |
|---|---:|---:|
| Responses requests | 30 | 16 |
| Requests with an empty `tools` array | 14 | 0 |
| Requests advertising the 13-name catalog | 16 | 16 |
| Prior function calls in requests with tools | 0 in 15/16; 1 in 1/16 | 0–15 |
| Prior calls/results in empty-tool requests | 1–3 pairs in all 14 | n/a |
| Input token usage on empty-tool requests | 2,493–5,451 | n/a |
| Largest input-token usage with tools advertised | 4,128 | 13,613 |
| `previous_response_id`, `tool_choice`, `reasoning.effort` | absent on all 30 | absent on all 16 |

## What this narrows down

- The empty-tool pattern is not simply caused by reaching the 16K context
  budget: the historical empty-tool requests used at most 5,451 input tokens,
  while the control retained the full tool catalog at 13,613 input tokens.
- Having prior tool calls/results in the input is not sufficient to make Codex
  omit tools: the control retained the catalog with as many as 15 prior
  call/result pairs.
- In the stalled trace, the empty catalog was associated with a distinct
  request shape that included prior tool history. This points toward a
  task-specific or Codex request-state difference, but does not identify its
  cause.
- Five empty-tool requests still received a translated `exec_command` item
  from Herd. The trace does not establish whether Codex executed those calls;
  27 Codex command events versus 21 Responses function-call items remain
  unreconciled.

Do not treat this as proof the adapter caused the task stall. The stock-adapter
control completed normally and did not reproduce an empty catalog. The guard
prototype remains unvalidated against the request state above and is not
deployed. See the [historical trace](2026-11-07-reliability-baseline.md),
[translator reproduction](2026-11-08-herd-empty-tools-translator-repro.md),
and [control run](2026-11-08-full-tools-protocol-control.md).
