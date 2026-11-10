# Hermes Gemma4 12B coding screen — 2026-11-10

One existing independent bug-fix fixture ran through Hermes with canonical
model `gemma4:12b` and explicit provider `localherd`. The task had a 180-second
hard process-group limit and ran without a hosted fallback.

| Measure | Result |
|---|---:|
| Task completion | 0/1 |
| Time | 180.079 s; timed out |
| First useful tool call | None |
| Source edits | None |
| Independent test/contract | Failed because implementation remained unchanged |
| Actual backend context | 65,536 |
| Runner / VRAM | 9.98 / 9.98 GB; full GPU residency |
| CPU offload | 0 bytes observed |

The baseline fixture test is expected to fail before the fix. Hermes produced
no tool calls, usage record, or output before timeout. One backend request and
its runner remained active after the client timeout; the test-owned model was
unloaded through the Ollama API, without a service restart. Follow-up checks
showed no loaded runner and zero GPU use. No model alias, role, saved default,
or service setting changed.

**Decision:** Gemma4 12B fails this coding-agent screen and receives no coding
role. Full GPU residency at 64K does not offset the absence of a first tool
action. Keep it only as an unqualified multimodal/vision candidate; no vision
task was tested. Do not infer that the separate E4B variant is qualified.
