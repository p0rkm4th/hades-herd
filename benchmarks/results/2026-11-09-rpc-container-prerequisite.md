# Isolated RPC container prerequisite — 2026-11-09

Herd's live status reports Nyx and Hecate online with zero active requests;
all their model queues have zero pending and in-flight requests. The latest
coordination-board reservations for both hosts are released. Each GPU is at
0% sampled utilization, with its existing Ollama model still resident:

| Node | Loaded Ollama model | VRAM used / total |
|---|---|---:|
| Nyx | `qwen38-27b-q4-codex-64k:latest` | 9059 / 10240 MiB; 6827 / 10240 MiB |
| Hecate | `mimo-v26-9b-codex-16k-hecate:latest` | 7017 / 12282 MiB |

Neither node has Docker or Podman executables available. Therefore no
container runtime, NVIDIA container runtime configuration, or cached image
inventory could be queried. The isolated build environment prerequisite is
unavailable. No model was unloaded, no container image pulled, no GGUF or
source inspected, and no RPC process/tunnel started. Production Ollama/Herd
and model residency remain unchanged.

| Configuration | Prompt tok/s | Generation tok/s | TTFT | GPU participation | Result |
|---|---:|---:|---:|---|---|
| Nyx only | Not measured | Not measured | Not measured | Not measured | Blocked: no container engine |
| Nyx + Hecate | Not measured | Not measured | Not measured | Not measured | Blocked: no container engine |

Next prerequisite: provide Docker or Podman with NVIDIA GPU passthrough on
both hosts. Then check for an existing image before pulling the authorized
pinned CUDA development image. No global software or service settings changed.
