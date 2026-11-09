# Local agent long-run scorecard — 2026-11-09

## Scope and evidence labels

This compares two independently authored implementations of the JSONL analyzer, each run through its own harness with MiMo 9B 64K. The implementations and self-authored tests are preserved separately in `benchmarks/results/hermes-jsonl/` and `benchmarks/results/codex-herd-jsonl-64k/`. The original one-path CLI contract is in `benchmarks/fixtures/jsonl-analyzer-acceptance/`; the optional strict-mode task remains separate in `benchmarks/fixtures/jsonl-strict-cli/`. No original acceptance fixture was modified.

- **User-observed run reports:** times, context compactions, approval waits, and self-report contradictions below were supplied by the operator after those runs. Raw session transcripts/telemetry were not available here for independent timing reconstruction.
- **Agent-reported outcomes:** self-authored test counts and claimed completion are not equivalent to independent acceptance.
- **Current independent checks:** exact source copies were tested in this checkout using their supplied unit tests and the shared black-box CLI fixture.

## Comparison

| Harness and model | User-observed wall time | Self-authored tests | Independent evidence | Compactions / execution | Reliability assessment |
|---|---:|---:|---|---|---|
| Hermes Agent, MiMo 9B 64K | ~15m27s original completion; resumed confirmation time is separate and excluded | 14/14 reported and re-run here | Operator reports separate CLI acceptance; shared CLI check passes here | Approval timeouts and context compaction observed; separate approval/tool/inference durations unavailable | Completed, but approval friction and compaction; one task does not qualify daily-driver use |
| Codex-Herd, MiMo 9B 64K | ~43m across visible long-run segments | 19/19 reported and re-run here | Operator reports separate CLI acceptance; shared base check passes here, but an additional valid `+00:00` timestamp check fails | At least 3 compactions; many failed corrections; ignored the requested 180s/two-correction limits. Agent reported no compactions/errors, contradicting observed evidence | Outcome is not trustworthy without independent checks; factual self-report mismatch is a reliability defect |
| Separate bounded Codex smoke, MiMo 9B 64K | 41.27s; first tool 3.44s | 17 independent fixture tests passed | Completed source edit, tool execution, final turn; 9 tool calls, 2 failed command invocations | No compactions reported for that short run; this does not describe the long run | Useful bounded-task result; keep distinct from the ~43m run |

The reported 6.17M cumulative tokens were an intermediate checkpoint value. It is cumulative consumption as reported, **not final context occupancy**; there is no raw token trace to reconcile it. Inference time, tool runtime, approval wait, and human wait were not separately measurable from the supplied evidence, so no throughput comparison is claimed.

## Reproduced checks

Commands, from the repository root:

```sh
python3 -m unittest discover -s benchmarks/results/hermes-jsonl -v
python3 -m unittest discover -s benchmarks/results/codex-herd-jsonl-64k -v
python3 benchmarks/fixtures/jsonl-analyzer-acceptance/check_cli.py benchmarks/results/hermes-jsonl/log_analyzer.py
python3 benchmarks/fixtures/jsonl-analyzer-acceptance/check_cli.py benchmarks/results/codex-herd-jsonl-64k/log_analyzer.py
python3 benchmarks/fixtures/jsonl-analyzer-acceptance/check_timezone_offset.py benchmarks/results/hermes-jsonl/log_analyzer.py
python3 benchmarks/fixtures/jsonl-analyzer-acceptance/check_timezone_offset.py benchmarks/results/codex-herd-jsonl-64k/log_analyzer.py
```

Results: Hermes 14/14; Codex 19/19; common black-box base acceptance passed both; numeric ISO-8601 offset acceptance passed Hermes and failed Codex (Codex returned `total=0`, `skipped=1` for `+00:00`). The Codex implementation's strict `Z`-only timestamp validator is narrower than the Hermes implementation and the shared timezone-offset acceptance. This is a verified correctness gap, not evidence of weaker security expertise or general reasoning.

`py_compile` passed on both implementations. The stored strict-mode extension is a different task and must not be added to the original scorecard's task success count.

## Decision

Neither long run qualifies either harness as an unattended daily driver. Use independently checked, task-specific acceptance and hard external time/tool limits. The separate 41.27s smoke establishes a bounded local success only; its success must not mask the long-run timeout, compaction, correction-loop, or false self-report failures.
