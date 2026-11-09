# Local security-model feasibility smoke — 2026-11-09

## Scope

One existing Cyber-Ornith 1.5 9B OBLITERATED imatrix Q4_K_M GGUF was tested in
an isolated Ollama 0.40.15 runtime bound to loopback. The source card declares
Apache-2.0 and advertises tool-use; this is publisher metadata, not a legal
review. Source revision:
[mradermacher/Cyber-Ornith i1-GGUF](https://huggingface.co/mradermacher/Cyber-Ornith-1.5-9B-OBLITERATED-i1-GGUF/tree/5936e88f1885b856b54520c372f2cd41e71819fd).
The 5,629,111,872-byte Q4_K_M artifact SHA-256 was verified as
`5b7bdec6919db868e517e9ab9a05ce8be096f6f139798a7b94a3aa3d2d1eab28`.

## Result

| Test | Result |
|---|---:|
| Cold model load plus short warmup | 43.32 s |
| Warm tool request first stream event | 0.57 s |
| Warm tool request complete | 2.23 s |
| Prompt / generated tokens | 313 / 61 |
| Prompt processing / generation | 0.532 s / 1.662 s (~588 / 36.7 tok/s) |
| Context / residency | 8,192; 100% GPU; no CPU layer offload |
| VRAM | 5,507 MiB / 10,240 MiB after request |
| KV cache | 136 MiB, Q8_0 for K and V |
| Functional result | Exact benign function call returned; a fixed local stub executed and the model reported its result |

This proves only GGUF import compatibility and one benign Ollama API tool-call
cycle. It does **not** validate security analysis, CVE/CWE accuracy, detection
quality, false positives, incident response, CTF capability, or Hermes tool
integration. The test used `OLLAMA_FLASH_ATTENTION=1`; the backend log confirms
Q8_0 allocation but has no explicit Flash Attention status line. No model was
registered with Herd, Codex-Herd, or Hermes. This remains an unqualified,
opt-in security-lab candidate; do not use it against public or production
targets.

The separate Ollama process and all GPU allocations were released afterward;
production defaults and services were left unchanged. Private runtime details
and reproducible command evidence are retained in the infrastructure-only
acceptance record.
