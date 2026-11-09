# Qwen3.8 Q4 context upgrade — 2026-11-08

## Configuration

Two Ollama aliases were created from the existing
`qwen38-27b-q4-codex-16k:latest` model, preserving its weights, template,
renderer, and parser:

| Alias | `num_ctx` | Ollama `ollama ps` context | CPU/GPU residency |
|---|---:|---:|---:|
| `qwen38-27b-q4-codex-32k:latest` | 32,768 | 32,768 | 27% / 73% |
| `qwen38-27b-q4-codex-64k:latest` | 65,536 | 65,536 | 33% / 67% |

The generated Codex profile and catalog for the 64K alias both reported 65,536
while the backend was loaded. `codex-herd list` discovered both aliases.
Neither alias became the saved default. No weights were downloaded and no
service settings changed. The original 16K alias remains present.

## Inference and tool smoke

On a dual RTX 3080 test node, a bounded short Ollama request completed on both
aliases. End-to-end request times were approximately 14.4 seconds at 32K and
14 seconds at 64K, including model load. At peak, 32K left 811 MiB and 3,287
MiB free on the two GPUs; 64K left 817 MiB and 3,051 MiB. The larger context
used more CPU residency and both configurations relied on CPU offload.

Codex CLI 0.167.0 then completed a disposable workspace task through
`codex-herd` using the 64K alias in 54 seconds. It created a small greeting
function and two `unittest` cases, invoked the shell tool, and completed the
turn. Independent verification passed both tests. No compaction or backend
error was observed. The saved Herd default and hosted Codex settings were not
changed.

The workstation `codex-herd` Python suite passed 22 tests after the run.

## Reproduction

The server Modelfiles are in [`models/`](../../models/). Create the aliases on
the Ollama host with `ollama create <alias> -f <Modelfile>`. Select the tested
64K profile with:

```sh
codex-herd qwen38-27b-q4-codex-64k:latest
```

The short prompt tests verify allocation and basic tool use; they do not
measure quality on long prompts near the full 64K window.
