# Operator guide

## Configure the endpoint

Set `CODEX_HERD_URL` in local shell startup. Do not put a private endpoint in a
public config file. The helper rejects non-HTTP(S) origins, embedded
credentials, query strings, and fragments.

## Daily use

- `codex-herd list` shows live model names, hosting nodes, availability,
  loaded state, context metadata, tool evidence, and the saved default.
- `codex-herd MODEL` launches the exact live model through Herd.
- `codex-herd role fast|balanced|complex` launches that locally configured role.
- `codex-herd config` edits the default and supported per-model preferences.
- `codex-herd config role ROLE MODEL` maps a role to a live, tool-capable local model.
- `codex-herd config show MODEL` distinguishes the Codex context budget from
  observed backend allocation and model metadata.
- `codex-herd refresh` refreshes discovery and generated profile state.

Unknown, offline, embedding-only, or ineligible models produce an error. The
helper does not download or substitute a model. User config is isolated under
`~/.config/codex-herd/`; hosted Codex settings remain separate.

Role assignments are stored only in local preferences and do not change the
saved default. Explicit model and role launches use model-isolated local
Responses profiles with Herd's no-fallback header.

The scoped local reliability benchmark selected MiMo-V2.6 9B Q4 at 16K: 4/5
verified fixture tasks, 100% GPU residency, and 23–107 seconds per full task.
Qwen3.8 27B Q4 at 64K failed to complete its smoke within 180 seconds and used
about 33% CPU residency. Map FAST, BALANCED, and bounded COMPLEX tasks to MiMo
if desired; this evidence does not establish long-context or broad repository
reliability. MiMo has failed separate diagnostic maintenance tasks in prior
campaigns, so inspect every diff and test result. See the [local reliability
scorecard](../benchmarks/results/local-model-reliability.md).

## Recovery

If the saved default no longer exists, refresh reports the stale preference and
does not silently replace it. Select a discovered model explicitly or set a
new default with `codex-herd config MODEL`. For router outages, use a direct
Ollama endpoint only when that backend is reachable and allowed by local
policy. The helper itself does not change networking or services.

If a local session stalls or loops, press `Ctrl-C` to stop that Codex process,
review any partial work with `git diff` and the project tests, then start the
hosted Codex command explicitly with `codex` if you want to continue there.
The launcher never redirects a local task to hosted inference. Hosted Codex
configuration remains unchanged.

Stop a session that repeats inspections without editing, reaches two failed
test corrections, or approaches its 180-second task budget without a verified
change. These are operator stop cues, not automatic timeouts. Unsupported
tool errors and context exhaustion are reasons to stop and review the partial
diff rather than retry blindly.

## Verify

```sh
python3 -m unittest discover -s tests -v
codex-herd list
codex-herd MODEL --help
```

`--help` forwarding checks Codex argument routing, not inference or task
completion. Use the acceptance definitions in [benchmark methodology](../benchmarks/README.md).
