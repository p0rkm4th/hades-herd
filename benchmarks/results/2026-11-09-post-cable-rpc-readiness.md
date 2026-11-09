# Post-cable distributed inference readiness — 2026-11-09

Nyx `enp4s0` reports link detected, autonegotiation enabled, 1000 Mb/s, full
duplex. Its IPv6 route to Hecate (`2600:1700:1301:6030::48`) uses `enp4s0`.
Hecate previously reported 1000 Mb/s full duplex. `iperf3` is not installed on
either node, so available throughput was not measured; no package was installed.

The RPC benchmark did not proceed because the GPUs were not available without
risking existing Ollama workloads. Read-only `nvidia-smi` snapshots showed
Ollama `llama-server` compute processes resident on both Nyx GPUs (9059/10240
MiB and 6827/10240 MiB used) and Hecate's GPU (7017/12282 MiB used). Utilization
was 0% at the sample, but those runners already held substantial VRAM. No
inference runner was stopped or displaced. No llama.cpp RPC binaries or source
were found in PATH or the standard isolated source directories checked; build
and model inspection were deferred because GPU capacity was the immediate
blocker.

| Configuration | Prompt tok/s | Generation tok/s | TTFT | GPU participation | Result |
|---|---:|---:|---:|---|---|
| Nyx only | Not measured | Not measured | Not measured | Not measured | Stopped: GPUs reserved by resident Ollama runners |
| Nyx + Hecate | Not measured | Not measured | Not measured | Not measured | Stopped: GPUs reserved by resident Ollama runners |

No network or service configuration, model, or process was changed. Available
link rate meets the 1 Gb/s prerequisite, but actual bandwidth and RPC benefit
remain unverified. A benchmark requires a separately approved idle window in
which the existing Ollama models can be unloaded or otherwise release VRAM;
this run did not alter them.
