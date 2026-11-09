# MiMo 64K long-prompt retrieval and tool smoke — 2026-11-09

## Result

The existing MiMo 9B Q4_K_M long-context profile allocated 65,536 tokens.
An explicit local Hermes request placed `HADES-64K-ALPHA-7Q3` at the beginning
of a prompt followed by 27,000 repeated filler words, then asked the model to
retrieve the marker and write it through its terminal tool. The run completed
in 16.38 seconds; the independently checked output matched exactly.

This is a long-prompt retrieval/tool smoke, not a coding benchmark or a test
that saturated the 64K allocation. The filler count is words, not verified
tokens. Hermes usage did not expose input-token or tool-call counts. No hosted
fallback was configured, and no production settings changed.

The first harness attempt exceeded the operating system's per-argument size
limit before inference. One bounded reduction to 27,000 words passed. Reuse
the private fixture and report for exact invocation and logs; this public
summary omits private host and endpoint details.
