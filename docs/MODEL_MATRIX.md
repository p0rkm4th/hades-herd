# Model and profile matrix

This matrix reports task-specific evidence from a private seven-node
installation. Hostnames and network addresses are intentionally omitted.
Digests refer to the exact local artifacts tested; they do not identify a
universal model build or imply general capability.

| Profile | Hardware class | Context tested | Evidence | Status |
|---|---|---:|---|---|
| `mimo-v26-9b-codex-16k-hecate:latest` (MiMo-V2.6 9B Q4_K_M) | Hecate, RTX 4070 Ti 12 GB | 16,384 actual | New local fixture suite 4/5; 100% GPU residency; task wall time 29–107 s; first tool 2.3–4.7 s | Best tested local profile; suitable for supervised FAST/BALANCED and bounded COMPLEX tasks; not a broad daily-driver guarantee |
| `mimo-v26-9b-codex-64k-hecate:latest` (same MiMo 9B Q4_K_M weights) | Hecate, RTX 4070 Ti 12 GB | 65,536 actual | 100% GPU residency; 8,463 / 12,282 MiB used after smoke; Codex tool task completed in 41.27 s (first tool 3.44 s), 9 tool calls, 17 independent tests passed; prior Hermes JSONL task passed | Qualified opt-in LONG for bounded coding; one Codex task only, not a broad reliability guarantee |
| `qwen38-27b-q4-codex-64k:latest` (Qwen3.8 27B Q4) | Nyx, 2 × RTX 3080 | 65,536 actual | Smoke changed the requested file and passed its test, but no completed Codex turn by 180 s; 66.7% GPU / 33.3% CPU residency | Not recommended at 64K for interactive coding; the bounded run does not rank the 16K alias |
| Qwen3.6 35B | Multi-GPU legacy node | Existing default | Remains the configured default; current evidence does not establish it as a dependable Codex agent | Preserve default; reassess only after controlled gate |

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
