# HADES Herd

A small, dependency-free Fish/Python client that discovers Ollama models in an
Ollama Herd fleet and launches Codex CLI through Herd's OpenAI-compatible
Responses endpoint. The client does not download models, change server
configuration, fall back to hosted OpenAI inference, or change a Codex default
unless the operator chooses one.

The source of truth and public engineering handoff is this repository:
[`p0rkm4th/hades-herd`](https://github.com/p0rkm4th/hades-herd).

## Requirements

- Python 3.10 or newer
- Fish shell (for the supplied command workflow)
- Codex CLI
- An Ollama Herd deployment that exposes `/api/tags`, `/fleet/status`, and an
  OpenAI-compatible `/v1` API to the client

## Install

Clone this repository and set the endpoint in your Fish configuration. Keep
private endpoints in local shell configuration, not in the repository:

```fish
set -Ux CODEX_HERD_URL http://herd.example.test:11435
function codex-herd --description 'Run Codex against the configured Ollama Herd'
    python3 /path/to/hades-herd/codex_herd.py $argv
end
```

Run `codex-herd refresh` once, then use:

```fish
codex-herd                 # saved default model
codex-herd list            # current fleet catalog and status
codex-herd qwen-model-tag  # select an exact discovered model
codex-herd config          # configure the default
codex-herd config show qwen-model-tag
codex-herd refresh         # refresh discovery
```

The first refresh creates a saved default when none exists. Each launch writes
an atomic, model-specific Codex profile and catalog under
`~/.config/codex-herd/codex-home/`, so simultaneous sessions selecting different
models do not share generated profile files. Tool-verification digests are
optional deployment metadata in the private `model-digests.json` file; the
public source includes no fleet-specific digest allowlist. User preferences
and generated files stay outside `~/.codex`; hosted Codex configuration remains
separate. For unloaded models, configured `num_ctx` is advertised only when
all online hosts report it; otherwise the client uses a 4K unverified safe
fallback. This metadata is not a measurement of current Ollama allocation. Run
`codex-herd --help` for the command interface. See the [operator guide](docs/OPERATOR_GUIDE.md).

## Safety and limits

The client only selects models found in the live fleet catalog. Missing models
are reported; they are never pulled automatically. A selected local profile
uses Herd's OpenAI-compatible endpoint and sends `X-Fleet-No-Fallback: true`.
Codex still applies its configured sandbox. Endpoint reachability is not
inference qualification, and a tool-capable model is not automatically a
reliable coding agent.

Current implementation and evaluation limits are in [`docs/STATUS.md`](docs/STATUS.md).
The deployment migration and canonical-source strategy are in
[`docs/SOURCE_OF_TRUTH.md`](docs/SOURCE_OF_TRUTH.md). No open-source license is
granted yet; see [`SECURITY.md`](SECURITY.md) for security guidance.

## Development

The client and tests use only the Python standard library:

```sh
python3 -m unittest discover -s tests -v
git diff --check
```

See [architecture](docs/ARCHITECTURE.md), [model matrix](docs/MODEL_MATRIX.md),
[benchmark method](benchmarks/README.md), and the [roadmap](docs/ROADMAP.md).
