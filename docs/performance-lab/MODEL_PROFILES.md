# Local model behavior profiles

These summaries use observed Hermes tasks, not public benchmark scores. Task evidence is still limited and should guide supervision, not unattended deployment.

## Qwen3.5 9B Q4_K_M

- **Observed:** 5/5 independent contracts passed in a five-task bounded coding suite; mean wall time 105.9 s. One debugging run used a different execution tool than requested, so strict tool-path compliance was 4/5.
- **Best role:** supervised, bounded coding tasks with explicit acceptance checks.
- **Weak role:** tasks where exact tool-path adherence or low latency is essential without supervision.
- **Effective prompt pattern:** state allowed tools, changed-file boundaries, and independent acceptance criteria. This was useful in the suite, but no prompt ablation proves a Qwen-specific wording advantage.
- **Ineffective prompts:** none isolated in the available evidence.
- **Task boundary and supervision:** one self-contained change per task; use a hard deadline and audit the tool trace.
- **Confidence:** low to moderate for this narrow fixture suite; low for long-context and repository-scale work.

## MiMo V2.6 9B Q4_K_M

- **Observed:** 4/5 independent contracts passed; mean wall time 36.7 s. A multi-file task passed its test suite but failed the independent contract.
- **Best role:** supervised bounded bug fixes, small features, refactors, and debugging fixtures.
- **Weak role:** multi-file work without an independent contract and human review.
- **Effective prompt pattern:** explicit changed-file allowlist, offline test command, and independent acceptance criteria. The evidence does not isolate a model-specific prompt advantage.
- **Ineffective prompts:** no prompt ablation is available. The failed contract shows that passing tests alone was insufficient.
- **Task boundary and supervision:** prefer one cohesive change; separately verify every requirement and inspect the diff.
- **Confidence:** low to moderate for the five synthetic tasks; not evidence of production reliability.

## Gemma4 12B

One bounded smoke run timed out at 180 seconds without useful tool activity. This single result is insufficient to characterize strengths, prompting, or ideal task scope; keep this model profile provisional.

See [STATUS.md](STATUS.md) for the current live comparison and outstanding evidence.
