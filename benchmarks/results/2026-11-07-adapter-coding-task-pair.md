# One paired Codex task through stock and patched Herd

Date: 2026-11-07. This was a bounded diagnostic of the isolated Herd reasoning
adapter patch, not a model benchmark or estimate of general reliability.

## Task and controls

The disposable task exposed a client validation gap: `CODEX_HERD_URL` is
specified as an HTTP(S) origin, but a path prefix was accepted even though the
client appends `/api/tags`, `/fleet/status`, and `/v1` paths to the value. A
regression test was added before both runs and failed on the unchanged code.
Both fresh clones used client base commit
`609f0a777f72e641d6e8852ceaf0e38f7f491b74`, identical task instructions and
fixtures, Codex CLI 0.166.0, the same model/context, workspace-write sandbox,
`approval_policy = "never"`, temporary `HOME` and `CODEX_HOME`, and a 180-second
OS timeout. No hosted credentials were available in either process.

The model was Qwen3.8 27B Q4 (`qwen38-27b-q4-codex-16k:latest`, digest
`0c315bae2dc37d912ae0ba10b1a2ea053296bce7f5be8f77283613df0d5f974b`). Codex
used a 16,384-token context; live Ollama residency during the patched run also
reported 16,384. Both profiles selected the backend-advertised `low`
reasoning preset.

The control used stock Herd. The experimental arm used a loopback-only Herd
v0.12.3 instance with the review patch from the
[`show-thinking-controls` branch](https://github.com/p0rkm4th/hades-herd/blob/codex-herd/show-thinking-controls/patches/ollama-herd-v0.12.3-reasoning-effort.patch).
That router had a synthetic registry with one explicit backend, auto-pull
turned off, retries disabled, and temporary state. It was not connected to
Herd nodes or production services. An earlier live request capture verified
the patch can map an advertised `low` effort to Ollama `think: "low"`; this
task did not separately capture its outbound body.

## Results

| Route | Agent result | Independent verification |
|---|---|---|
| Stock Herd | Timed out at 180 s after writing a patch; no completed Codex turn or final response. | The partial patch passed the 9-test endpoint module and `git diff --check`; it remains an incomplete autonomous result. |
| Patched Herd | Completed in about 129 s with a `turn.completed` event and patch. | The full client suite passed 18/18 and `git diff --check` passed without reviewer correction. |

Both attempts completed seven Codex tool items. The patched router also logged
that it removed an untranslatable `web_search` tool; this did not prevent the
model from completing the local task.

This single pair is encouraging evidence that explicit effort forwarding can
help this task finish. It does not establish causation or general improvement:
model generation is stochastic, the sample is one task, and no repeated suite
has been run. The adapter patch remains experimental and undeployed.

## Safety and cleanup

The OS timeout bounded both runs. Each model instance was unloaded afterward.
The disposable router was stopped, the backend returned to 5/1 MiB GPU use at
0%, and Herd reported 7/7 online with zero active requests. No production route,
service, model default, Codex profile/catalog, or HADES provider was changed.
Only sanitized outcome metadata is published; raw event streams and router
logs remain local.
