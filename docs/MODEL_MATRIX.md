# Model and profile matrix

This matrix reports task-specific evidence from a private seven-node
installation. Hostnames and network addresses are intentionally omitted.
Digests refer to the exact local artifacts tested; they do not identify a
universal model build or imply general capability.

| Profile | Hardware class | Context tested | Evidence | Status |
|---|---|---:|---|---|
| MiMo-V2.6 9B Q4_K_M | Single 12 GB GPU | 16K | One HTTPie #1960 task completed and independently verified; several different issue tasks timed out without edits; Rich #4250 0/1 | Task-qualified for the observed header-formatting task; otherwise experimental |
| Qwen3.8 27B Q4 | Dual 10 GB GPUs | 8K–16K | Repeated registry/multi-file passes at 8K; several 16K Codex tasks incomplete; Rich #4250 0/1 | Experimental; stronger-task performance and practical responsiveness unqualified |
| Qwen3.6 35B | Multi-GPU legacy node | Existing default | Remains the configured default; current evidence does not establish it as a dependable Codex agent | Preserve default; reassess only after controlled gate |

A model's declared context maximum is not proof of runtime allocation. Catalog
metadata and live `/api/ps` allocation must be reported separately. See the
[operator guide](OPERATOR_GUIDE.md) for selection and context display.

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
pool VRAM across independent hosts. The current reliability goal remains ahead
of offload-engine or hardware-layout experiments: keep Qwen3.8 Q4 as the
advanced experimental profile, keep MiMo as a task-qualified fast profile, and
make no default, hardware, or production-route changes based on public scores.
