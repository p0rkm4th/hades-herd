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

## Recovery

If the saved default no longer exists, refresh reports the stale preference and
does not silently replace it. Select a discovered model explicitly or set a
new default with `codex-herd config MODEL`. For router outages, use a direct
Ollama endpoint only when that backend is reachable and allowed by local
policy. The helper itself does not change networking or services.

## Verify

```sh
python3 -m unittest discover -s tests -v
codex-herd list
codex-herd MODEL --help
```

`--help` forwarding checks Codex argument routing, not inference or task
completion. Use the acceptance definitions in [benchmark methodology](../benchmarks/README.md).
