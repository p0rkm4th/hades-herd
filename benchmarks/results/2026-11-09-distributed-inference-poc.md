# Distributed inference proof of concept — 2026-11-09

## Streaming check

One short, identical `STREAM_OK` request per path, Qwen3.8 27B 64K, 24-token
output cap. Nyx's direct Ollama `/api/chat` NDJSON stream returned HTTP 200,
25 lines, first data at 0.701 s, second line 0.141 s later, completion in
3.676 s. Herd's OpenAI-compatible `/v1/chat/completions` SSE returned HTTP
200, 64 lines, first data at 0.461 s, and completed in 4.740 s. Both reached
the client and completed without a stall. This bounded check does not establish
why the earlier long Codex request had a five-minute idle interval; the
historical failure remains unproven.

## Distributed inference status

No Nyx-only versus Nyx+Hecate benchmark was run. Strict SSH verification to
Hecate failed because no ED25519 host key is trusted for that destination.
Host-key checking was preserved. Without a verified Hecate connection, its
GPU availability, link speed, llama.cpp/RPC build, and safe isolated transport
cannot be checked. Nyx has no `llama-server` or `llama-rpc-server` in PATH.
Nyx's two RTX 3080s reported 817 MiB and 3051 MiB free of 10,240 MiB at the
check. No process, package, model, service, or routing changes were made.

## Decision

Distributed inference is unqualified; do not pursue an RPC deployment until
Hecate's SSH host identity is independently verified and compatible isolated
llama.cpp builds can be checked. Keep the nodes independent meanwhile.
