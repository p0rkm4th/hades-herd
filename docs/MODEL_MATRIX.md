# Model and profile matrix

This matrix reports task-specific evidence from a private seven-node
installation. Hostnames and network addresses are intentionally omitted.
Digests refer to the exact local artifacts tested; they do not identify a
universal model build or imply general capability.

| Profile | Hardware class | Context tested | Evidence | Status |
|---|---|---:|---|---|
| `mimo-v26-9b-codex-16k-hecate:latest` (MiMo-V2.6 9B Q4_K_M) | Hecate, RTX 4070 Ti 12 GB | 16,384 actual | New local fixture suite 4/5; 100% GPU residency; task wall time 29–107 s; first tool 2.3–4.7 s | Best tested local profile; suitable for supervised FAST/BALANCED and bounded COMPLEX tasks; not a broad daily-driver guarantee |
| `mimo-v26-9b-codex-64k-hecate:latest` (same MiMo 9B Q4_K_M weights) | Hecate, RTX 4070 Ti 12 GB | 65,536 actual | 100% GPU residency; 8,463 / 12,282 MiB used after smoke; Codex tool task completed in 41.27 s (first tool 3.44 s), 9 tool calls, 17 independent tests passed; prior Hermes JSONL task passed | Qualified opt-in LONG for bounded coding; one Codex task only, not a broad reliability guarantee |
| `qwen3.5:9b-q4_K_M` | Charon RTX 3080 10 GB; same digest also on Hecate | 16,384 on tested Charon profile | Charon passed a four-test slug task 10/10 times and one seven-test multi-module task; latter took 131 s / 28 command executions and agent misstated baseline test status. Hecate passed once and stopped twice in inspection loops on the slug task. | Strong small-task candidate, but not advanced in the matched five-category suite; keep unqualified for FAST/BALANCED/COMPLEX pending diverse, same-harness comparison. Historical evidence: private 2026-11-06 model evaluation. |
| `qwen38-27b-q4-codex-64k:latest` (Qwen3.8 27B Q4) | Nyx, 2 × RTX 3080 | 65,536 actual | Smoke changed the requested file and passed its test, but no completed Codex turn by 180 s; 66.7% GPU / 33.3% CPU residency | Not recommended at 64K for interactive coding; the bounded run does not rank the 16K alias |
| Qwen3.6 35B | Multi-GPU legacy node | Existing default | Remains the configured default; current evidence does not establish it as a dependable Codex agent | Preserve default; reassess only after controlled gate |
| Cyber-Ornith 1.5 9B OBLITERATED i1 Q4_K_M | RTX 3080 10 GB | 8,192 actual | Isolated Ollama import; one benign tool call, 100% GPU, 5,507 MiB VRAM, 43.32 s cold load/warmup and 2.23 s warm tool request | Feasibility only; not a security profile and not registered in Herd. See [security-lab smoke](../benchmarks/results/2026-11-09-security-lab-feasibility.md) |
| `mimo-v26-9b-codex-64k-hecate:latest` (MiMo 9B Q4_K_M) | RTX 4070 Ti 12 GB | 65,536 actual | 27,000-word long-prompt retrieval plus terminal tool completed in 16.38 s; independent output check passed | Long-context/tool smoke only; prompt token count unavailable and this did not saturate 64K. See [probe report](../benchmarks/results/2026-11-09-mimo-64k-long-context.md) |

A model's declared context maximum is not proof of runtime allocation. Catalog
metadata and live `/api/ps` allocation must be reported separately. See the
[operator guide](OPERATOR_GUIDE.md) and the
[2026-11-09 local reliability scorecard](../benchmarks/results/local-model-reliability.md)
for exact settings, task scores, and limitations.

## External benchmark context (not local acceptance)

The owner-provided November 6 model study recommends Qwen3.8 27B as the
practical high-capability candidate and treats Flash-Next / GLM-5.3-Flash as
larger offload experiments. The official Qwen model card reports Qwen3.8 27B
at 61.7 SWE-bench Pro, 73.0 Terminal-Bench 2.1, and 42.2 DeepSWE 1.1; the
Qwen3.8-Flash-Next release blog reports 62.5 SWE-bench Pro and 58.7
DeepSWE 1.1. The GLM-5.3-Flash card reports 84.3 Terminal-Bench 2.1 and 63.4
DeepSWE 1.1, and describes a 320B total / 18B active model. See the [Qwen3.8
27B card](https://huggingface.co/Qwen/Qwen3.8-27B), [Qwen3.8-Flash-Next
release blog](https://qwen.ai/blog?id=qwen3.8-flash-next), and [GLM-5.3-Flash
card](https://huggingface.co/zai-org/GLM-5.3-Flash).

These are vendor-reported results, not a controlled comparison and not results
for our quantized local artifacts or Codex/Herd configuration. In particular,
active parameter count does not equal total weight storage, and Herd does not
pool VRAM across independent hosts. The new five-task local fixture run supports
MiMo 9B Q4 at 16K for bounded supervised coding. Qwen3.8 Q4 at 64K remains slow
and incomplete on the matched smoke; the run does not qualify or disqualify its
separate 16K alias. No default, hardware, or production-route change is based on
public model scores.


## Long-run harness evidence

The user-observed Hermes (~15m27s) and Codex-Herd (~43m across visible
segments) JSONL tasks are separate long runs. Despite 14/14 and 19/19
self-authored tests, the agent-reported outcomes conflict with resource and
compaction observations; Codex also failed a new black-box timezone-offset
check. Neither harness is qualified as an unattended daily driver by these
runs. See the [long-run comparison](../benchmarks/results/2026-11-09-harness-longrun-scorecard.md).

## Hermes 64K matched coding comparison (2026-11-09)

| Hermes profile | Five-task result | Mean wall / first-tool latency | Decision |
|---|---:|---:|---|
| MiMo 9B Q4, `mimo-code` | 4/5 | 36.7 / 37.4 s | Faster; one multi-file contract failure. |
| Qwen3.5 9B Q4, `qwen35` | 5/5 external checks; 4/5 strict terminal-only | 105.9 / 106.6 s | Slower, but all independent checks passed; one task used the code tool to execute pytest. |

Both used local Herd inference, identical fixtures, a 180 s per-task cap, and offline validation. Neither is qualified for unattended work from this sample. Qwen3.5 64K was fully GPU resident (8,487/10,240 MiB) and passed exact long-prompt marker retrieval; 128K offloaded 28% to CPU and failed that retrieval contract. See [the sanitized report](../benchmarks/results/2026-11-09-hermes-qwen35-mimo-comparison.md). Select explicitly with `hermes -m mimo-code --provider localherd` or `hermes -m qwen35 --provider localherd`; the saved Hermes default is unchanged.
