# Operator guide

## Configure the endpoint

Set `CODEX_HERD_URL` in local shell startup. Do not put a private endpoint in a
public config file. The helper rejects non-HTTP(S) origins, embedded
credentials, query strings, and fragments.

## Daily use

- `codex-herd list` shows live model names, hosting nodes, availability,
  loaded state, context metadata, tool evidence, and the saved default.
- `codex-herd MODEL` launches the exact live model through Herd.
- `codex-herd config` edits the default and supported per-model preferences.
- `codex-herd config show MODEL` distinguishes the Codex context budget from
  observed backend allocation and model metadata.
- `codex-herd refresh` refreshes discovery and generated profile state.

Unknown, offline, embedding-only, or ineligible models produce an error. The
helper does not download or substitute a model. User config is isolated under
`~/.config/codex-herd/`; hosted Codex settings remain separate.

Use `codex-herd list` to copy the exact fast or advanced model identifier, then
pass it to `codex-herd MODEL`. The saved default and hosted Codex profile are
not changed by explicitly selecting a model.

## Recovery

If the saved default no longer exists, refresh reports the stale preference and
does not silently replace it. Select a discovered model explicitly or set a
new default with `codex-herd config MODEL`. For router outages, use a direct
Ollama endpoint only when that backend is reachable and allowed by local
policy. The helper itself does not change networking or services.

If a local session stalls or loops, press `Ctrl-C` to stop that Codex process,
review any partial work with `git diff` and the project tests, then start the
hosted Codex command explicitly if you want to continue there. The launcher
never redirects a local task to hosted inference. Hosted Codex configuration
remains unchanged.

As a practical supervised-use rule, stop a MiMo session if it rereads the same
files repeatedly without editing or makes no source change after about three
minutes. Stop after two consecutive failed corrections of the same test. For
Qwen3.8, allow more time when its reasoning helps, but stop after about five
minutes without a concrete edit or test result. These are operator stop cues,
not automatic timeouts. Unsupported tool errors and context exhaustion are
reasons to stop and review the partial diff rather than retry blindly.

## Verify

```sh
python3 -m unittest discover -s tests -v
codex-herd list
codex-herd MODEL --help
```

`--help` forwarding checks Codex argument routing, not inference or task
completion. Use the acceptance definitions in [benchmark methodology](../benchmarks/README.md).
