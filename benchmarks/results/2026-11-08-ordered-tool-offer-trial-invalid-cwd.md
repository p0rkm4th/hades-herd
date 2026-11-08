# Ordered tool-offer diagnostic — excluded working-directory trial

## Outcome

This bounded run is excluded from coding-quality and protocol-causality
results. The synthetic repository was created in a temporary directory, but
Codex inherited the public client checkout as its current directory.
The task asked for a boundary fix in the disposable repository; the model
instead spent the 90-second limit inspecting paths and made no patch. This was
a harness invocation error, not a model pass or failure.

The run used Codex CLI 0.166.0, the pinned Herd v0.12.3 test app, and installed
MiMo-V2.6 9B Q4_K_M on an RTX 4070 Ti host (digest
`47f141d59fb9ece0a349cf27e8292b8c192ae0087b2a051c2e29c06526feea4b`, configured
16K context). A fresh temporary home and isolated test router were used; the
production Herd endpoint was not in the inference path.

## Trace observations

- The external process-group timeout fired at 90 seconds. The independent task
  checkout had no source or test diff; only Python cache files were created.
- The content-free Codex event index recorded 16 successful shell-command
  events. Fifteen non-overlapping request windows were assignable to backend
  observations, and those exchanges returned only advertised `exec_command`.
- One completed Responses request explicitly carried an empty tool list and
  returned no function calls.
- A late Codex response carried `exec_command` and `read` call names, but the
  reducer could not assign an Ollama exchange to that response. The trace
  therefore cannot establish whether either name was model-selected, changed
  by Herd, or accepted by Codex. It does not resolve the unsupported-tool
  hypothesis.
- The observation is not comparable to prior live tasks because Codex operated
  from the wrong working directory. No model-quality score is reported.

## Cleanup and harness correction

MiMo was unloaded after the run; the inference host returned to 5 MiB GPU use
and 0% GPU utilization. The test app, loopback proxies, and strict-key SSH
tunnel were stopped. Production Herd remained 7/7 online with no active or
queued requests.
No production configuration, service, routing, or default changed.

The capture helper now accepts `--cwd` and passes it directly to the child
process. A regression test verifies the child's working directory. Future
trials must set this explicitly to the disposable checkout. No same-task retry
was made.
