# Two-node RPC benchmark prerequisite check — 2026-11-09

## Current availability

Herd reports Nyx and Hecate online with zero active requests. Every queue for
both nodes reports zero pending and zero in-flight requests. The latest
coordination-board entries for both nodes are released reservations. Via each
node's documented `OLLAMA_HOST`, `ollama ps` shows one resident model and zero
request activity:

| Node | Resident model | Placement | Context |
|---|---|---|---:|
| Nyx | `qwen38-27b-q4-codex-64k:latest` | 33% CPU / 67% GPU | 65,536 |
| Hecate | `mimo-v26-9b-codex-16k-hecate:latest` | 100% GPU | 16,384 |

Models were not evicted: the benchmark could not proceed with the existing
build prerequisites, so unloading would only disturb warm production state.

## RPC build blocker

No `llama-cli`, `llama-server`, or `llama-rpc-server` is on either node's
PATH. No llama.cpp source tree was found in the checked standard isolated
locations (`/opt/llama.cpp`, `/usr/local/src/llama.cpp`, `/home/codex/llama.cpp`).
Neither node has `cmake`, `ninja`, or `nvcc` available. An isolated CUDA/RPC
build therefore cannot be made without obtaining additional compiler/toolkit
dependencies. No packages or source were downloaded or installed. Nyx's
existing Ollama model metadata reports Q4_K_M / 27.3B; its backing GGUF was not
inspected because the missing CUDA build toolchain is already a hard blocker.

| Configuration | Prompt tok/s | Generation tok/s | TTFT | GPU participation | Result |
|---|---:|---:|---:|---|---|
| Nyx only | Not measured | Not measured | Not measured | Not measured | Blocked: no isolated llama.cpp CUDA build/toolchain |
| Nyx + Hecate | Not measured | Not measured | Not measured | Not measured | Blocked: no isolated llama.cpp CUDA/RPC build/toolchain |

No Ollama model, service, network, or Herd configuration was changed. The
next prerequisite is an approved way to provide matching isolated CMake and
CUDA compiler dependencies on both nodes without changing production system
libraries; then confirm the existing Nyx Q4_K_M backing file is usable by that
llama.cpp revision before evicting models or running inference.
