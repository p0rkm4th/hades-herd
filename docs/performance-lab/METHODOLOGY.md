# Methodology and acceptance standards

## Baseline controls

- Runtime: Ollama 0.40.15.
- Three models/nodes, run serially to avoid GPU contention; three repeated runs per model.
- Context 65,536; `num_predict=128`; temperature 0; seed 7.
- Exact local model digests were checked before generation and retained in private evidence.
- Model cold-load behavior is reported separately from already-warm runs.
- Generated text and private endpoints are not part of public results.

The synthetic prompt is: “Write a concise numbered troubleshooting guide for a fictional local inference server. Give practical steps for diagnosing slow responses, report how to verify each step, and continue until the response token limit.”

The harness observed no nonempty answer chunks in these runs, despite reaching the token cap. TTFT is therefore unavailable; no useful-answer latency, model quality, or task-completion claim is made.

## Optimization acceptance

Use matched model artifact, runtime, context, workload, and contention conditions. Preserve repeated raw counters privately. Report medians and run variability, cold/warm state, peak resource use where available, and independent correctness. Separate infrastructure/backend failures from prompting, tool-use, and reasoning failures. Report negative results and uncertainty.

A throughput change alone is not a usable-task improvement. A meaningful result should show a material reduction in task time, more usable context/concurrency, lower memory without substantial quality regression, improved independently verified completion, or fewer tool errors. No production route/default changes are part of this research branch.

## Context allocation candidate control

The Qwen3.6 35B comparison changed only request context from 65,536 to 16,384. It used the same text, seed, temperature, 128-token cap, model artifact, and runtime. Report the initial context-transition load separately from warm runs, and restore the original runner context after the candidate. A reduced context is unsuitable if the task requires longer context.


## Worker acceptance

A worker claim is not acceptance. Use offline mock services to verify CLI
behavior, digest guards, experiment ordering, metric fields, privacy,
no-clobber behavior, and error handling. Preserve the initial artifact, record
supervisor corrections, and classify completion as autonomous,
retry-assisted, incomplete, or failed.
