# Agent profile context check — 2026-11-09

## Snapshot and decision

`codex-herd list` discovered 29 local model IDs on 7/7 online nodes; 26 IDs
advertise tool capability and one is embedding-only. The saved Codex default
remains `qwen3.6:35b`. Existing FAST, BALANCED, and COMPLEX mappings remain on
MiMo 9B Q4 at 16K. The 64K MiMo alias is available as an opt-in LONG profile and is assigned to
Codex LONG after a bounded tool-driven coding smoke completed.

Herd reported three loaded models: Hecate MiMo 64K, Nyx Qwen3.8 64K, and
Tartarus Qwen3.6. After waiting for a transient queue counter discrepancy to clear, the smoke
ran with zero active/pending requests. Reservation state is not exposed by the
Herd API; no production service or unrelated workload was changed.

## Context and agent evidence

| Model profile | Context | GPU / CPU residency | Task evidence | Decision |
|---|---:|---|---|---|
| Hecate MiMo 9B Q4, `mimo-v26-9b-codex-16k-hecate:latest` | 16,384 | 100% GPU in previous measured fixture | 4/5 distinct local coding fixtures; 29–107 s/task | Keep FAST, BALANCED, and bounded COMPLEX |
| Hecate MiMo 9B Q4, `mimo-v26-9b-codex-64k-hecate:latest` | 65,536 actual `ollama ps` allocation | 100% GPU; 8,455 / 12,282 MiB used | Prior Hermes JSONL task and one Codex tool-driven coding task independently validated; 17 tests passed | Hermes LONG alias and opt-in Codex LONG |
| Nyx Qwen3.8 27B Q4, `qwen38-27b-q4-codex-16k:latest` | 16,384 configured | No current runner | Historical task-specific passes; broader completion reliability is weak | Keep explicit, task-limited use only |
| Nyx Qwen3.8 27B Q4, `qwen38-27b-q4-codex-32k:latest` | 32,768 configured | Not loaded in this snapshot | Basic inference passed; two bounded agent coding attempts did not complete | Do not promote |
| Nyx Qwen3.8 27B Q4, `qwen38-27b-q4-codex-64k:latest` | 65,536 actual allocation | 66.7% GPU / 33.3% CPU in prior measurement | Matched Codex smoke did not complete by 180 s | Reject for interactive COMPLEX/LONG work |

Hecate MiMo 64K measurements on the existing alias:

| Run | Result | First text | Total | Backend details |
|---|---|---:|---:|---|
| Warmup | `READY` | 3.44 s (includes 3.21 s load) | 3.45 s | 14 generated tokens, 100% GPU |
| Short measured call | Completed after warmup with thinking disabled | 0.095 s | 0.109 s | 2 generated tokens; 65,536 context; 100% GPU |
| Code-shaped prompt, default thinking | Hit 64-token generation cap without user-visible text | No text | 0.86 s | No service error; do not treat as a completed response |

The single corrective short request used Ollama request-level `think:false`;
that setting was not applied globally. A separate bounded Codex smoke then
used the installed Codex CLI with the exact 64K alias, isolated workspace and
local-only profile. It completed in 41.27 s; first tool action was at 3.44 s.
There were 9 successful tool calls (2 shell invocations returned nonzero while
the agent corrected/validated), no compactions, and a final completed turn.
Independent validation passed all 17 tests and `git diff --check`; only the
requested analyzer source file changed. This single task does not establish
general long-context reliability.

## Optimization and limits

- No Flash Attention, KV-cache, prompt-cache, global context, routing, or
  service settings were changed. The MiMo 64K runner fit fully in GPU memory
  with headroom; a broad service-level cache change is not justified by this
  evidence.
- Other installed models remain discoverable but unqualified for new roles;
  the full inventory is recorded in the private infrastructure profile report.
- Hermes' opt-in aliases are `hades-mimo-fast` and `hades-mimo-long`. Invoke
  with `hermes -m hades-mimo-fast chat` or `hermes -m hades-mimo-long chat`.
- Codex's LONG role is supported by the launcher but unassigned. Use the
  explicit model ID only for a bounded supervised trial; FAST/BALANCED/COMPLEX
  remain available through the current 16K mapping.

## Reproduction and validation

Read-only fleet/catalog snapshot:

```sh
fish -lc 'codex-herd list'
```

Hecate alias was inspected with `ollama ps` and `nvidia-smi`; no model pull or
service restart was used. The independent JSONL fixture baseline passes:

```sh
python3 -m unittest discover -s benchmarks/results/hermes-jsonl -v
```

Launcher/configuration tests after friendly-label and LONG-role changes:

```sh
python3 -m unittest discover -s tests -v
git diff --check
```

Codex LONG is enabled as an opt-in. Hermes aliases remain `hermes -m
hades-mimo-fast chat` and `hermes -m hades-mimo-long chat`; Codex LONG is
`codex-herd role long`.
