# Isolated llama.cpp RPC comparison — 2026-11-09

## Setup

Used the official `ggml-org/llama.cpp` CUDA 12.8 Linux x64 release `b12211`
(commit `7d7f0287530bc8981690f361d8c1627dbae1c99a`). The binary archive SHA256
was `103fac975e807da6cdb5717e87ca594e25bb7703dd8a7f10c22269c124e1a552`; the
matching CUDA runtime archive SHA256 was
`d66dba34f0e45c66ce7d4484116c681aa71ff257ee1e47b02d9775aa59b5ef77`. Both
subjects were covered by the official GitHub release attestation. Driver
595.91.07 exceeded CUDA 12.8's 570.26 Linux minimum. Both nodes ran the same
release build. Existing Ollama GGUF (27B Q4_K_M, 17.44 GB) loaded successfully.

RPC worker bound to Hecate loopback and was reached through authenticated SSH
forwarding. The client used local CUDA devices plus the remote RPC device.
Services, aliases, routing, and defaults were unchanged. Idle Ollama runners
were unloaded; temporary RPC/server processes, tunnels, and binaries were
removed after the test.

## Results

Same 37-token prompt and 48-token deterministic generation; one warmup and one
measured request per setup. Model load time is separate from request latency.

| Measured metric | Nyx: 2 × RTX 3080 | Nyx + Hecate: 2 × RTX 3080 + RTX 4070 Ti |
|---|---:|---:|
| Prompt processing | 274.7 tok/s | 55.5 tok/s |
| Generation | 36.3 tok/s | 21.1 tok/s |
| First streamed token | 0.186 s | 1.286 s |
| Request total | 1.482 s | 3.511 s |
| Model load to ready | ~4.6 s | ~61.3 s |
| GPU memory after load (MiB used) | 8,625 / 8,513 | 5,951 / 5,131 / 6,497 |

Both requests completed with normal stop and the same 251-character response.
The Hecate GPU's memory rose from 207 MiB idle to 6,497 MiB with the distributed
model loaded, confirming remote GPU participation. Nyx's two GPUs also held
model allocations. The run selected CUDA0, CUDA1, and RPC0 with 999 GPU layers;
the build did not report a CPU-offloaded layer count, so CPU offload is not
claimed as independently measured. Across warmup and measured distributed
requests, interface counters showed about 270 MB sent Hecate-to-Nyx. The link
was 1 Gb/s; this short run does not indicate link saturation.

## Decision

Do not pursue this RPC setup for interactive inference: generation was 42%
slower, prompt processing about 80% slower, first-token latency 1.1 seconds
higher, and model loading about 57 seconds longer. Keep inference on independent
Ollama/Herd nodes. This is a bounded throughput comparison, not a long-context
or coding-agent quality benchmark.

## Provenance

- [Official release](https://github.com/ggml-org/llama.cpp/releases/tag/b12211)
- [Release attestation](https://github.com/ggml-org/llama.cpp/attestations/65083165)
- [CUDA 12.8 release notes](https://docs.nvidia.com/cuda/archive/12.8.0/cuda-toolkit-release-notes/index.html)
