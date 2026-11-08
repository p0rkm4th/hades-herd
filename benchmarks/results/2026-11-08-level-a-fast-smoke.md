# Level A fast-profile smoke — 2026-11-08

## Decision

**Level A is not met.** Three distinct, reproducible maintenance tasks were
attempted with MiMo-V2.6 9B Q4 through the local Codex/Herd profile. None
produced an independently verified implementation. Because the 4-of-5 target
was already unreachable after these three failures, the campaign stopped; two
more similar runs would not change the release decision.

The separate matched launch smoke in
[`2026-11-08-supervised-codex-launch-smoke.md`](2026-11-08-supervised-codex-launch-smoke.md)
showed both MiMo and Qwen3.8 can execute tools, make a small edit, pass tests,
and complete a Codex turn. That small formatter task is not counted here.

## Method

Each task used the installed Codex CLI 0.166.0 through the model-specific Herd
Responses profile, a fresh temporary HOME, a disposable clone of public `main`,
workspace-write sandbox, no hosted credentials, and a hard timeout. Each bug
was reproduced before inference with a focused regression test. Results were
checked independently. No task patch was applied to a development branch or
production system.

## Attempts

| Task | Baseline | Codex result | Independent result | Score |
|---|---|---|---|---:|
| First-run default selection and persistence | No-argument launch returned `Unknown model None` | Turn ended after 9 shell calls; no source or test edit | Regression still failed | Fail |
| Effective context with duplicate online hosts | Catalog reported 16K while another online host was configured for 8K | 180-second timeout after 37 shell calls; source-only patch | Regression still reported 16K; patch used model metadata rather than the configured per-host value | Fail |
| Distinct same-name trace calls | Two calls were collapsed into one trace entry | Turn ended after 7 shell calls; no source or test edit | Regression still failed | Fail |

Result: **0/3 verified completions**. The matched formatter task passed for both
models, but it was one small synthetic integration smoke and cannot offset
these failures or support a general coding-reliability claim.

## Supported use scope

Use local profiles only for supervised, low-risk work where the operator can
quickly inspect the diff and run the relevant tests. Start with MiMo for a
small, clearly scoped edit; use Qwen3.8 selectively when a harder task merits
the observed extra latency. Do not assign unattended configuration, protocol,
or cross-host correctness work based on these results. Keep hosted Codex as an
explicit fallback.
