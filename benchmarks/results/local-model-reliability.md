# Local coding reliability — 2026-11-09

## Decision

The selected profile is MiMo-V2.6 9B Q4_K_M, alias
`mimo-v26-9b-codex-16k-hecate:latest`, on Hecate. It completed **4/5** distinct
local coding fixtures. The tested backend and Codex catalog context were both
16,384; Ollama reported 6,147,423,600 bytes of 6,147,423,600 bytes in VRAM
(100% GPU, 0% CPU). Task time ranged from 29.1 to 106.6 seconds, with first
useful tool action at 2.3–4.7 seconds. This meets the 4/5 fixture target, not
the separate 20-task/85% daily-driver gate.

The verified assignments are FAST, BALANCED, and bounded COMPLEX to this same
MiMo profile. Keep the scope near the tested 16K context and verify the
generated diff/tests. Do not use it for refactoring that depends on a precise
structural contract without an additional independent check.

## Candidate inventory and configuration

The live Herd catalog had 7/7 nodes online, zero pending/in-flight requests,
zero active-request telemetry, and no active reservation recorded at check
time. The selected candidates were already available; no model was downloaded.

| Candidate | Live node and model | Actual context | Residency | Tool/thinking and parameters | Compatibility |
|---|---|---:|---:|---|---|
| FAST/BALANCED/COMPLEX | Hecate — `mimo-v26-9b-codex-16k-hecate:latest`, 9B Q4_K_M | 16,384 | 100% GPU / 0% CPU (6,147,423,600 / 6,147,423,600 bytes) | Tool digest verified. Ollama: `num_ctx=16384`, `temperature=0.6`, `top_p=0.95`, `top_k=20`, `min_p=0`, `repeat_penalty=1`, `presence_penalty=0`. Codex reasoning effort is not selectable through Herd 0.12.3; no per-session developer instruction or sampling override was used. | Real Fish launcher, local Responses profile, shell tools, edits, pytest, and independent checks passed on four tasks. |
| Advanced comparison | Nyx — `qwen38-27b-q4-codex-64k:latest`, 27B Q4_K_M | 65,536 | 66.7% GPU / 33.3% CPU (15,133,730,403 / 22,673,862,158 bytes) | Catalog tool digest is unverified; the smoke did return a shell tool, edit the requested file, and pass the independent check. Backend parameter observed: `num_ctx=65536`; other sampling parameters were not separately exposed. Codex reasoning effort is not mapped to Ollama thinking. | Did not emit a completed Codex turn before the 180-second smoke cap. Not selected. |

Other online catalog entries were not advanced: their tool evidence was
unverified or there was no stronger task-completion evidence than these two
profiles. The separate Qwen 16K alias was not loaded or benchmarked in this run;
do not infer its performance from the 64K result.

## Results

All work ran through the installed Fish `codex-herd` function with an explicit
local model, fresh temporary HOME/CODEX_HOME, workspace-write sandbox,
approval `never`, and no hosted API credentials. The generated profile used
the Herd Responses API with `requires_openai_auth=false` and
`X-Fleet-No-Fallback=true`. Each task used a disposable Git repository, a
180-second process-group timeout, a baseline pytest run, post-run pytest, an
independent contract check, and an allowed-path check. Workspaces and raw event
text were discarded. Pytest ran via isolated `uv` when not installed locally.

| Model / task | Result | First tool | Total | Calls (completed / failed) | Tokens in / out | Tests / independent check | Compactions |
|---|---:|---:|---:|---:|---:|---|---:|
| MiMo smoke | Pass | 3.18 s | 23.46 s | 5 (4 / 1) | 20,421 / 815 | 1 passed / pass | 0 |
| MiMo bug fix | Pass | 2.91 s | 97.97 s | 16 (10 / 6) | 154,372 / 4,829 | 6 passed / pass | 0 |
| MiMo feature | Pass | 2.56 s | 46.49 s | 9 (7 / 2) | 48,233 / 2,580 | 1 passed / pass | 0 |
| MiMo refactor | **Fail** | 2.70 s | 57.75 s | 10 (8 / 2) | 71,577 / 4,171 | 1 passed / contract failed | 0 |
| MiMo multi-file | Pass | 2.64 s | 106.56 s | 19 (14 / 5) | 147,655 / 6,554 | 3 passed / pass | 0 |
| MiMo debugging | Pass | 4.67 s | 29.06 s | 10 (7 / 3) | 48,064 / 1,574 | 2 passed / pass | 0 |
| Qwen3.8 64K smoke | **Incomplete** | 14.74 s | 180.01 s cap | 11 (8 / 3) | not emitted | 1 passed / pass; source edit present | 0 |

The MiMo refactor preserved behavior and passed pytest but did not satisfy the
independent requirement to extract and use the specified pure helper. This is
a model instruction-following/correctness miss, not an infrastructure error.
The four successful MiMo tasks passed without human edits. Across its five
scored tasks, Codex reported 64 tool calls: 46 completed successfully and 18
failed; exact failed-command text was not retained. No repeated identical tool
command or compaction was observed. Codex token counts were cumulative across
stateless requests, so they do not represent peak context utilization. Peak
per-request utilization was not emitted; context budgets were 16,384 and
65,536 as listed above.

Qwen3.8 64K made the requested smoke edit and its tests passed, but the session
did not return a final Codex turn at 180 seconds. No SSE disconnect or backend
crash was recorded. With 33.3% CPU residency, slow offloaded inference is a
plausible contributor, but this run cannot distinguish it from model progress
failure. The separate short RPC comparison also found lower throughput with
distributed inference; do not route this profile across nodes.

## Historical Qwen3.5 9B evidence (not part of this matched suite)

Existing November 6 records show Qwen3.5 9B Q4_K_M on Charon passed the same
four-test slug task in 10/10 trials, then passed one seven-test multi-module
task in 131 seconds with 28 command executions. That multi-module run's agent
incorrectly reported that baseline tests passed, so its completion required
independent replay. On Hecate, the same small fixture passed once but twice
stopped in inspection loops. These older Codex 0.166 runs used a different
fixture and harness setup from the 2026-11-09 MiMo suite; do not combine their
rates or infer Qwen3.5's general task reliability from them. Qwen3.5 remains a
strong candidate for controlled diverse comparison, not a promoted role.

## Use and limitations

Set roles without changing the saved default:

```sh
codex-herd config role fast mimo-v26-9b-codex-16k-hecate:latest
codex-herd config role balanced mimo-v26-9b-codex-16k-hecate:latest
codex-herd config role complex mimo-v26-9b-codex-16k-hecate:latest
codex-herd role balanced
```

FAST is suitable for small, clear edits; BALANCED for ordinary bug fixes and
features; COMPLEX for bounded multi-file/debugging tasks similar to the tested
fixtures. All use the same 16K context and model. Unsupported/unconfigured
roles fail with an actionable local-model assignment message; the launcher
never falls back to a hosted provider. Existing defaults and server routing
were not changed. The legacy MiMo failure campaigns (0/3 on separate
maintenance tasks) remain relevant evidence, so use this profile for
task-specific local autonomy with review, not unrestricted unattended work.
