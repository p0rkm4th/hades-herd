# Final distributed inference validation — 2026-11-09

## Hecate identity

Distributed testing stopped before SSH access. The infrastructure onboarding
record identifies Hecate as `fe80::67c:16ff:fe47:b5fa` / global
`2600:1700:1301:6030::48`, but also explicitly says its first-use host key
was accepted after password-authenticated access without independent
fingerprint verification. A saved first-use key is not an independent trust
source. Required operator action: read Hecate's ED25519 SSH host-key
fingerprint from its trusted local console and compare it with the presented
key before authorizing its use. Strict SSH checking remains enabled; no
fingerprint was accepted or changed.

## Nyx network route

Nyx routes to Hecate's documented global IPv6 address over `enp4s0`. The
interface reports UP/LOWER_UP and `/sys/class/net/enp4s0/speed` reports 100
Mb/s, so this is an active 100 Mb/s link. This is inadequate for a practical
RPC tensor-split comparison; no `iperf3` test or distributed benchmark was
run. No network settings changed.

## Herd Responses streaming

One bounded non-sensitive Qwen3.8 27B 64K request to Herd `/v1/responses`
returned HTTP 200 and nine SSE data events. First event arrived at 0.475 s;
`response.completed` reached the client at 5.247 s. Events included
`response.in_progress`; output events arrived at about 4.985 s. This confirms
only the short Responses path; the historical five-minute idle timeout in a
long Codex session remains unresolved.

| Configuration | Prompt tok/s | Generation tok/s | TTFT | GPU participation | Result |
|---|---:|---:|---:|---|---|
| Nyx only | Not run | Not run | Not measured | Not measured for this fixture | Blocked before RPC setup |
| Nyx + Hecate | Not run | Not run | Not measured | Not measured | Blocked by unverified host identity and 100 Mb/s Nyx link |

No model, service, build, or configuration was changed. Keep inference nodes
independent. Reconsider RPC only after Hecate's host key is independently
verified and Nyx has a faster inter-node connection.
