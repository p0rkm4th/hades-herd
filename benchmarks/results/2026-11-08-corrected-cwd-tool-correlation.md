# Corrected-CWD Codex/Herd tool correlation

## Result

A new disposable elapsed-time formatter task ran from its actual repository
checkout using the capture helper's explicit `--cwd`. Codex CLI 0.166.0
completed the turn in 16.4 seconds through a disposable Herd v0.12.3 app to
MiMo-V2.6 9B Q4_K_M (digest
`47f141d59fb9ece0a349cf27e8292b8c192ae0087b2a051c2e29c06526feea4b`). The
configured and observed loaded context was 16,384 tokens. Independent
`unittest` verification passed 7/7; the initial fixture had one expected
failure at the one-hour boundary.

The model changed the formatter and added tests. One added boundary test
duplicates an existing test, a minor patch-quality issue. It also recovered
from a failed edit command and an initial test-discovery invocation that found
no tests; the subsequent `-s tests` invocation passed. No human code correction
was needed. This is one synthetic task, not a model-quality or daily-driver
qualification result.

## Protocol observations

- Six completed Codex Responses requests each had a corresponding complete
  Ollama chat observation. There were no overlapping or unassigned windows.
- Five function calls were returned in Ollama responses; all were
  `exec_command`, which was present in each request's advertised tool list.
- Each following Responses request included the previous tool-call/result
  history. Codex then returned a completed final turn.
- No empty tool offer or unadvertised tool name appeared in this run.

This verifies ordered name and tool-result continuity for this one task. It does
not explain the earlier isolated unadvertised `read` call or prove that such a
call cannot recur.

## Cleanup

The model was unloaded; the GPU returned to 5 MiB / 0%. The temporary Herd app,
loopback proxies, and SSH tunnel were stopped. Production Herd remained 7/7
online with zero active or queued requests. No production route, service,
configuration, or default changed.
