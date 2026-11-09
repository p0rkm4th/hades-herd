# Qwen3.8 Codex idle-timeout investigation — 2026-11-09

## Observed failure

The failed 64K `codex-herd doctor` task ran on commit `878089c`. Codex reported
44.649 seconds to first token and 664.393 seconds total, made six successful
shell calls, recorded no context compactions, and returned
`idle timeout waiting for SSE` without completing the task. Its last recorded
usage was 44,158 total tokens; no final response or verified tests were
produced.

The Ollama journal recorded the final `/api/chat` request as HTTP 200 with a
5m00s duration at the same second as Codex's timeout. No matching kernel OOM
or NVIDIA Xid event was found. This rules out an observed runner crash or OOM.
It establishes a five-minute response gap, but the Ollama access log does not
show whether tokens were generated or forwarded by Herd during that interval.

## Bounded context comparison

The same task was run once on a clean disposable worktree with the 32K alias.
Ollama reported 32,768 context and 27% CPU / 73% GPU residency (the 64K
baseline was 33% CPU / 67% GPU). Five shell calls completed successfully, but
the task made no source changes and returned no final response before the
420-second harness cap. No compaction event or test result was recorded. The
matching Ollama request lasted 4m50s and returned HTTP 200 as the harness
stopped it. The corrected run's first-output latency was not captured by the
bounded harness.

Reducing context and CPU offload did not demonstrate improved completion. The
evidence is consistent with a model response that stopped producing Codex
events, but it does not distinguish silent model generation from events
withheld in Herd's Responses/SSE adapter. Herd service logs were unavailable
through the attempted strict-key route because no trusted host key was known;
host-key checking was not bypassed. No service timeout or routing change is
justified by this evidence.

## Outcome

No source or service configuration was changed. The 32K experiment was
discarded; the previously loaded 64K alias was restored. All 16K, 32K, and 64K
aliases and the saved default remain unchanged. The existing 16K alias remains
a bounded-task fallback; this investigation does not qualify any Qwen3.8
profile for reliable multi-step daily coding.
