# Hermes local coding comparison: Qwen3.5 9B and MiMo 9B — 2026-11-09

Both models ran the same five isolated Python coding fixtures through Hermes 0.23.0 and the local `localherd` provider. Each run had a 180-second cap, file allowlists, independent contract checks, and offline pytest validation. No hosted fallback was configured.

| Profile | Independent pass | Mean wall time | Mean first-tool time | Tool calls | Notes |
|---|---:|---:|---:|---:|---|
| MiMo 9B Q4, `mimo-code`, 64K | 4/5 | 36.7 s | 37.4 s | 45 | Multi-file change failed the independent contract although pytest passed. |
| Qwen3.5 9B Q4, `qwen35-64k-charon:latest`, 64K | 5/5 external checks | 105.9 s | 106.6 s | 81 | Debug task used `execute_code` to run the prescribed offline pytest command instead of terminal; strict terminal-only success is 4/5. |

Reported token counts were unavailable. API-call counts are not token counts. Both profiles completed all turns within individual caps. Qwen was slower and its strict tool requirement lowers its score; MiMo was faster but missed one multi-file contract. This five-task sample does not qualify either model as an unattended daily driver.

Qwen3.5 128K was tested first: actual allocation 131,072, 28% CPU / 72% GPU residency, 75,301 prompt tokens, about 97 seconds, and a failed exact-marker retrieval contract. At 64K, a 50,302-token prompt allocated 65,536, stayed fully on GPU, used 8,487/10,240 MiB, completed in 20.0 seconds, and returned the exact marker. The opt-in alias reuses existing `qwen3.5:9b-q4_K_M` weights; alias digest `9a6c38c70831b96e51f4eaba2200eae5e85c0f3551d42ffd7cdcab7b5d280ba6` adds no duplicate weight set.

Commands:

```sh
hermes -m mimo-code --provider localherd
hermes -m qwen35 --provider localherd
```

Recommendation: MiMo 64K is the faster Hermes coding candidate; Qwen3.5 64K is an opt-in higher-pass-rate candidate with substantially slower first action. Keep the saved default unchanged and supervise both. Reproduce with the private fixture runner; the public report intentionally excludes private paths, endpoints, and raw traces.
