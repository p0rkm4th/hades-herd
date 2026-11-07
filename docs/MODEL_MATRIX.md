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
