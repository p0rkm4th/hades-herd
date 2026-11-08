# Full-tool Responses control — 2026-11-08

This is a protocol-control run, not a model-quality benchmark. It checks the
ordinary Codex tool-call cycle against stock Ollama Herd v0.12.3 after the
historical HTTPie trace showed requests with an empty tool list.

## Fixture and setup

- Public, synthetic fixture:
  [`protocol-control/header-merge`](../fixtures/protocol-control/header-merge/).
  The six-test baseline intentionally has three failures. SHA-256 values for
  the task prompt, starting implementation, and starting tests are recorded in
  the fixture README's initial source snapshot.
- Codex CLI 0.166.0; Ollama 0.40.15; stock Herd v0.12.3 translator at commit
  `e0dac345515e8423e385ea2d465573a1e8b5a1bf`.
- MiMo-V2.6 9B Q4_K_M, digest
  `47f141d59fb9ece0a349cf27e8292b8c192ae0082b8a051c2e29c06526feea4b`, with
  configured and observed allocation of 16,384 context tokens.
- Codex ran in an isolated home and disposable repository with a
  workspace-write sandbox, `approval_policy=never`, and a 180-second
  process-group timeout. The temporary router and metadata proxy bound to
  loopback; the test router had mDNS disabled in the disposable clone. No
  private network address, node name, or raw Codex trace is included here.

## Result

- Codex exited 0 and emitted `turn.completed` after 81.7 seconds.
- The request trace contained 16 successful `/v1/responses` POSTs. Every request
  advertised the same 13-name tool catalog; 15 responses contained an
  `exec_command`, followed by a final message. No empty-tool request occurred.
- Codex changed the implementation and added regression cases. The independent
  post-run suite passed 12/12 tests; the unchanged baseline had failed 3/6.
- Review found overlapping assertions and redundant test cases in the generated
  patch. The task needed no human correction to pass, but the patch still merits
  ordinary code review for test maintainability.
- The model was unloaded after the run. No production service, provider setting,
  or routing configuration changed.

## Interpretation

The normal tool-follow-up path worked through the stock adapter for this task.
The run does not reproduce or exercise the empty-tool guard, and therefore
provides no evidence that the guard improves task completion. It also does not
qualify this model as a daily driver: this was one synthetic diagnostic task,
excluded from the model leaderboard and the 20-task acceptance gate.

The historical empty-tool pattern remains specific to the stalled HTTPie trace.
Keep the adapter prototype isolated until that request class or an equivalent
live case is reproduced.
