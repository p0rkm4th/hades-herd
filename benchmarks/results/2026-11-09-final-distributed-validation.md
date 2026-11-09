# Final distributed inference validation — 2026-11-09

## Hecate identity

Authenticated SSH access works over Hecate's documented wired IPv6 link-local
address `fe80::67c:16ff:fe47:b5fa` using the existing Codex identity and
`StrictHostKeyChecking=yes`; the remote hostname is `hecate`. My earlier
attempt used the IPv4 address, which had no matching known-host entry, and
incorrectly treated that as lack of SSH access. The infrastructure record says
the link-local key was first accepted after password-authenticated access but
was not independently fingerprint-checked out of band. No key was added,
removed, or replaced; SSH's existing strict pin matched.

## Nyx network route

Nyx routes to Hecate's documented global IPv6 address over `enp4s0`; it is
UP/LOWER_UP and reports 100 Mb/s. Hecate's `enp4s0` is also UP/LOWER_UP and
reports 1000 Mb/s. The Nyx link is the bottleneck and is inadequate for a
practical RPC tensor-split comparison, so no `iperf3` test or distributed
benchmark was run. No network settings changed.

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
independent. Reconsider RPC after upgrading Nyx's inter-node link; the existing
strict SSH pin allowed verified access, although its initial fingerprint was
not checked out of band.
