# Qwen3.8 context profile retention and cleanup — 2026-11-10

## Short-task quantization evidence

Two earlier real Codex runs used the same unchanged eight-test repository task
at 8K. Qwen3.8 27B Q3_K_M completed four tool calls and passed all 8 tests in
63 seconds. Q4_K_M also passed all 8 tests in 102 seconds. This is one run per
quantization, so retain Q3 only as a task-specific short-context Codex
candidate; it does not qualify for broad autonomous coding. A separate Q3 16K
task timed out after 240 seconds without edits. At 8K it does not meet the
64K minimum of the deployed Hermes version.

## Context alias decision

The Q4 32K and 64K aliases were removed from Ollama after repeated longer-
context coding attempts did not complete. The Q4 base model and 8K/16K aliases
remain. These aliases shared the existing Q4 weight layers, so the removal
recovered no model-weight storage. No default, role, route, or service changed.

The previous 64K runner remained loaded after its tag was deleted: 65,536
context, 33% CPU / 67% GPU, about 15.1 GB resident in VRAM, and an indefinite
keep-alive. Ollama still exposed it as a runner-only entry without advertised
tool capability. The supported stop command could not resolve the deleted tag;
two bounded restore attempts returned HTTP 400. No production service was
restarted. This is incomplete cleanup: do not select or count the stale runner
as a valid profile. The private record contains exact manifests, Modelfiles,
and a recovery procedure whose create step is not yet verified.

At 2026-11-10 02:19 UTC the queue and active-request counters were again zero.
Ollama's documented empty-prompt unload API (`keep_alive: 0`) also returned
`model not found`; the runner remained at 65,536 context and 33% CPU / 67% GPU.
No further attempt or service restart was made. A planned service lifecycle
window or vendor-supported cleanup path is required to remove this orphan.

## Reproduction and evidence limits

Refresh the installed local catalog with `codex-herd refresh`, inspect it with
`codex-herd list`, and verify actual loaded context with Ollama `ps`/`/api/ps`.
The historical task bundles retain the unchanged fixture, source diff, and
independent test output. The local score is task-specific and does not establish
a general Q3-versus-Q4 quality ranking. The post-removal catalog still showed
the resident 64K runner, so the two aliases are removed from Ollama manifests
but not fully cleared from live Herd discovery.
