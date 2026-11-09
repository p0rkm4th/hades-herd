# Architecture

## Request path

1. The Python helper reads the configured Herd origin from `CODEX_HERD_URL`
   (default: loopback `http://127.0.0.1:11435`).
2. `list`/`refresh` read `/api/tags` and `/fleet/status`; for online nodes, the
   helper reads node model tags and `/api/show` metadata to distinguish known
   digests, declared context, and loaded context.
3. It writes a dedicated Codex model catalog and provider profile below
   `~/.config/codex-herd/`. Private preferences are stored separately from
   `~/.codex` with restrictive file permissions.
4. Codex CLI sends inference to Herd's `/v1` Responses endpoint. The profile
   sends `X-Fleet-No-Fallback: true` and disables request retry at the provider
   layer. Herd translates requests to Ollama on registered backends.
5. Codex executes its own tools under its configured sandbox. The helper does
   not create a second agent loop.

## Local client responsibilities

The helper dynamically discovers the fleet model catalog and validates exact
model names before launch. Embedding-only models are retained in inventory but
excluded from Codex selection. Deployment-specific tool-verification digests
are read from the private `~/.config/codex-herd/model-digests.json`; no local
fleet/model allowlist is published. Per-model user preferences are opt-in. Context
metadata, actual backend allocation, model-declared maximum, and Codex's budget
are displayed separately where available.

Generated Codex catalog entries keep the canonical Herd model ID in `slug` and
use a separate `display_name` for the friendly HADES label. Context labels are
derived from the effective catalog context; they do not replace the backend
identifier or claim that an unqualified model is agent-reliable. FAST,
BALANCED, COMPLEX, and LONG are local preference mappings only. An unassigned
role fails locally and never falls back to hosted inference.

The helper does not manage Herd nodes, change Ollama services, pull models,
modify firewall rules, or alter production provider routing. Keep direct Ollama
endpoints available as an operational fallback.

## Reliability boundary under investigation

The Codex client, Herd Responses translator, Ollama chat API, and model template
are separate layers. A tool-call attempt alone does not prove that the tool
name was advertised, accepted, executed, and returned to the model correctly.
The public repository currently contains the client, not Herd's server source.
See [status](STATUS.md) and the reliability roadmap before attributing a failure
to a model or changing the service adapter.
