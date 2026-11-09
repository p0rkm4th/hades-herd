#!/usr/bin/env python3
"""Small, dependency-free client for the HADES Ollama Herd Codex profile."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_HERD_URL = "http://127.0.0.1:11435"
HERD_URL_ENV = "CODEX_HERD_URL"
ROOT = Path.home() / ".config" / "codex-herd"
CODEX_HOME = ROOT / "codex-home"
PREFS = ROOT / "preferences.json"
DIGEST_EVIDENCE = ROOT / "model-digests.json"
CATALOG = ROOT / "model-catalog.json"
INVENTORY = ROOT / "inventory.json"
PROFILE = CODEX_HOME / "herd.config.toml"
DEFAULT_STREAM_IDLE_TIMEOUT_MS = 300_000
MIN_STREAM_IDLE_TIMEOUT_MS = 30_000
MAX_STREAM_IDLE_TIMEOUT_MS = 900_000
ROLES = ("fast", "balanced", "complex")


class HerdError(Exception):
    pass


def read_digest_evidence() -> tuple[dict[str, str], dict[str, str]]:
    """Read optional deployment-specific tool-evidence digests from local config."""
    if not DIGEST_EVIDENCE.exists():
        return {}, {}
    try:
        data = json.loads(DIGEST_EVIDENCE.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise HerdError(f"Cannot read model digest evidence at {DIGEST_EVIDENCE}: {exc}") from exc
    if not isinstance(data, dict):
        raise HerdError("Model digest evidence must be a JSON object.")
    result = []
    for key in ("verified_tool_digests", "inconsistent_tool_digests"):
        values = data.get(key, {})
        if not isinstance(values, dict) or any(
            not isinstance(name, str)
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest.lower())
            for name, digest in values.items()
        ):
            raise HerdError(f"{key} must map model names to 64-character SHA-256 digests.")
        result.append({name: digest.lower() for name, digest in values.items()})
    return result[0], result[1]


def herd_base_url() -> str:
    """Return the configured Herd origin without embedding a private endpoint."""
    value = os.environ.get(HERD_URL_ENV, DEFAULT_HERD_URL).strip().rstrip("/")
    parsed = urllib.parse.urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise HerdError(
            f"{HERD_URL_ENV} must be an http(s) origin without credentials, query, or fragment."
        )
    return value


def get_json(path: str) -> dict:
    base = herd_base_url()
    request = urllib.request.Request(base + path, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HerdError(f"Cannot reach Herd at {base}: {exc}") from exc


def post_json(url: str, value: dict, timeout: float = 2.0) -> dict | None:
    request = urllib.request.Request(url, data=json.dumps(value).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def get_url_json(url: str, timeout: float = 3.0) -> dict | None:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as out:
            json.dump(value, out, indent=2, sort_keys=True)
            out.write("\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def model_profile_paths(name: str) -> tuple[str, Path, Path]:
    """Return isolated Codex profile/catalog paths for one model session."""
    suffix = hashlib.sha256(name.encode("utf-8")).hexdigest()[:12]
    profile_name = f"herd-{suffix}"
    return profile_name, CODEX_HOME / f"{profile_name}.config.toml", CODEX_HOME / f"model-catalog-{suffix}.json"


def read_prefs() -> dict:
    if not PREFS.exists():
        return {"default_model": None, "models": {}}
    try:
        prefs = json.loads(PREFS.read_text())
        prefs.setdefault("models", {})
        return prefs
    except (OSError, json.JSONDecodeError) as exc:
        raise HerdError(f"Cannot read {PREFS}: {exc}") from exc


def fetch() -> tuple[dict[str, dict], dict]:
    verified_tool_digests, inconsistent_tool_digests = read_digest_evidence()
    tags = get_json("/api/tags")
    fleet = get_json("/fleet/status")
    online = {n["node_id"] for n in fleet.get("nodes", []) if n.get("status") == "online"}
    endpoints = {n["node_id"]: n.get("ollama_url") for n in fleet.get("nodes", []) if n.get("status") == "online"}
    node_tags: dict[str, dict[str, str]] = {}
    for node_id, endpoint in endpoints.items():
        catalog = get_url_json(endpoint.rstrip("/") + "/api/tags") if endpoint else None
        node_tags[node_id] = {
            item.get("model") or item.get("name"): item.get("digest")
            for item in (catalog or {}).get("models", [])
            if item.get("model") or item.get("name")
        }
    loaded: dict[str, list[dict]] = {}
    for node in fleet.get("nodes", []):
        for model in node.get("ollama", {}).get("models_loaded", []):
            loaded.setdefault(model.get("name", ""), []).append({
                "node": node.get("node_id"),
                "context_length": model.get("context_length"),
            })

    result = {}
    for item in tags.get("models", []):
        name = item.get("model") or item.get("name")
        if not name:
            continue
        nodes = item.get("details", {}).get("fleet_nodes", [])
        caps = item.get("capabilities", [])
        model_contexts = []
        model_parameters = {}
        local_digests = {node_id: node_tags.get(node_id, {}).get(name) for node_id in nodes}
        for node_id in nodes:
            endpoint = endpoints.get(node_id)
            if not endpoint:
                continue
            shown = post_json(endpoint.rstrip("/") + "/api/show", {"model": name})
            if not shown:
                continue
            info = shown.get("model_info", {})
            model_contexts.extend(v for k, v in info.items() if k.endswith(".context_length") and isinstance(v, int))
            if shown.get("parameters"):
                model_parameters[node_id] = shown["parameters"]
        expected_digest = verified_tool_digests.get(name)
        known_inconsistent = inconsistent_tool_digests.get(name)
        observed_digests = [digest for digest in local_digests.values() if digest]
        if expected_digest and nodes and all(local_digests.get(node_id) == expected_digest for node_id in nodes):
            tool_status = "verified"
        elif expected_digest and any(digest == expected_digest for digest in observed_digests):
            tool_status = "mixed"
        elif known_inconsistent and any(digest == known_inconsistent for digest in observed_digests):
            tool_status = "inconsistent"
        else:
            tool_status = "unverified"
        tool_status_detail = ", ".join(
            f"{node_id}:{'verified' if digest == expected_digest else 'unverified'}"
            for node_id, digest in local_digests.items()
        )
        result[name] = {
            "name": name,
            "digest": item.get("digest"),
            "size_bytes": item.get("size"),
            "family": item.get("details", {}).get("family"),
            "parameter_size": item.get("details", {}).get("parameter_size"),
            "quantization": item.get("details", {}).get("quantization_level"),
            "nodes": nodes,
            "node_digests": local_digests,
            "online_nodes": [n for n in nodes if n in online],
            "loaded": loaded.get(name, []),
            "model_context_window": min(model_contexts) if model_contexts else None,
            "model_parameters": model_parameters,
            "capabilities": caps,
            "embedding_only": bool(caps) and set(caps) <= {"embedding"},
            "tool_capable": "tools" in caps,
            "tool_status": tool_status,
            "tool_status_detail": tool_status_detail,
        }
    return result, fleet


def effective_codex_context(model: dict, prefs: dict) -> tuple[int, str]:
    name = model["name"]
    live_contexts = [x["context_length"] for x in model["loaded"] if x.get("context_length")]
    override = prefs.get("models", {}).get(name, {}).get("codex_context_window")
    configured_contexts = []
    for node_id in model.get("online_nodes", []):
        parameters = model.get("model_parameters", {}).get(node_id, "")
        if isinstance(parameters, str):
            for line in parameters.splitlines():
                key, _, value = line.partition(" ")
                if key == "num_ctx" and value.strip().isdigit():
                    configured_contexts.append(int(value.strip()))
                    break
        elif isinstance(parameters, dict):
            value = parameters.get("num_ctx")
            if isinstance(value, int) and value > 0:
                configured_contexts.append(value)
    online_nodes = set(model.get("online_nodes", []))
    loaded_nodes = {item.get("node") for item in model.get("loaded", []) if item.get("context_length")}
    if override:
        context, context_source = override, "user override"
    elif live_contexts and online_nodes and online_nodes <= loaded_nodes:
        context, context_source = min(live_contexts), "loaded allocation on all online nodes"
    elif online_nodes and len(configured_contexts) == len(online_nodes):
        context, context_source = min(configured_contexts), "Ollama configured num_ctx on all online nodes"
    else:
        context, context_source = 4096, "unverified safe fallback"
    return context, context_source


def codex_entry(model: dict, prefs: dict) -> dict:
    name = model["name"]
    context, context_source = effective_codex_context(model, prefs)
    modalities = ["text"]
    if "vision" in model["capabilities"]:
        modalities.append("image")
    return {
        "slug": name,
        "display_name": name,
        "context_window": context,
        "context_source": context_source,
        "shell_type": "default",
        "visibility": "list",
        "supported_in_api": True,
        "priority": 0,
        "truncation_policy": {"mode": "bytes", "limit": 10000},
        "input_modalities": modalities,
        "base_instructions": "",
        "support_verbosity": True,
        "default_verbosity": "low",
        "supports_parallel_tool_calls": False,
        "supports_reasoning_summaries": False,
        "supported_reasoning_levels": [],
        "experimental_supported_tools": [],
    }


def stream_idle_timeout_ms(name: str, prefs: dict) -> int | None:
    value = prefs.get("models", {}).get(name, {}).get("stream_idle_timeout_ms")
    if value is None:
        return None
    if type(value) is not int or not MIN_STREAM_IDLE_TIMEOUT_MS <= value <= MAX_STREAM_IDLE_TIMEOUT_MS:
        raise HerdError(
            f"Saved Codex SSE idle timeout for {name} must be an integer from "
            f"{MIN_STREAM_IDLE_TIMEOUT_MS} through {MAX_STREAM_IDLE_TIMEOUT_MS} milliseconds."
        )
    return value


def saved_developer_instructions(name: str, prefs: dict) -> str | None:
    value = prefs.get("models", {}).get(name, {}).get("developer_instructions")
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise HerdError(f"Saved developer_instructions for {name} must be text.")
    return value


def sync_catalog(models: dict[str, dict], prefs: dict, default: str | None = None) -> None:
    base = herd_base_url()
    selectable = [m for m in models.values() if not m["embedding_only"] and m["tool_capable"]]
    if not selectable:
        raise HerdError("Herd returned no non-embedding tool-capable models")
    saved_default = prefs.get("default_model")
    online_defaults = sorted(m["name"] for m in selectable if m["online_nodes"])
    default_candidates = online_defaults or sorted(m["name"] for m in selectable)
    if default is None:
        default = saved_default or default_candidates[0]
    if default not in {m["name"] for m in selectable}:
        raise HerdError(
            f"Saved default_model {default!r} is no longer selectable. "
            f"Live models: {', '.join(sorted(m['name'] for m in selectable))}. "
            f"Run `codex-herd config <live-model>` and choose a live default."
        )
    idle_timeout = stream_idle_timeout_ms(default, prefs)
    instructions = saved_developer_instructions(default, prefs)
    instruction_block = (
        f"developer_instructions = {json.dumps(instructions, ensure_ascii=False)}\n"
        if instructions is not None
        else ""
    )
    CODEX_HOME.mkdir(parents=True, exist_ok=True)
    _, profile_path, catalog_path = model_profile_paths(default)
    catalog_models = [codex_entry(m, prefs) for m in sorted(selectable, key=lambda x: x["name"])]
    write_json(catalog_path, {"models": [{k: v for k, v in entry.items() if k != "context_source"} for entry in catalog_models]})
    config = f'''model = {json.dumps(default)}
model_provider = "herd"
model_catalog_json = {json.dumps(str(catalog_path))}
{instruction_block}

[model_providers.herd]
name = "HADES Ollama Herd"
base_url = {json.dumps(base + "/v1")}
wire_api = "responses"
requires_openai_auth = false
supports_websockets = false
request_max_retries = 0
stream_max_retries = 0
{f'stream_idle_timeout_ms = {idle_timeout}' if idle_timeout is not None else ''}

[model_providers.herd.http_headers]
"X-Fleet-No-Fallback" = "true"
'''
    atomic_write_text(profile_path, config)
    write_json(INVENTORY, {"endpoint": base, "models": models})
    if saved_default is None and default == default_candidates[0]:
        prefs["default_model"] = default
        write_json(PREFS, prefs)


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as out:
            out.write(value)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def eligible(name: str, models: dict[str, dict]) -> dict:
    model = models.get(name)
    if model is None:
        available = ", ".join(sorted(models)) or "none"
        raise HerdError(f"Unknown model {name!r}. Live inventory: {available}. Run `codex-herd refresh` and check the exact identifier.")
    if model["embedding_only"]:
        raise HerdError(f"{name} is embedding-only. It remains in fleet inventory but cannot be selected for Codex.")
    if not model["tool_capable"]:
        raise HerdError(f"{name} does not advertise Ollama tool capability and is excluded from Codex selection.")
    if not model["online_nodes"]:
        raise HerdError(f"{name} is unavailable: no hosting node is online. No download or hosted fallback will be attempted.")
    return model


def assign_role(role: str, name: str, models: dict[str, dict], prefs: dict) -> None:
    role = role.lower()
    if role not in ROLES:
        raise HerdError(f"Unknown role {role!r}. Choose one of: {', '.join(ROLES)}.")
    model = eligible(name, models)
    if not model.get("online_nodes"):
        raise HerdError(f"{name} is not online and cannot be assigned to the {role} role.")
    prefs.setdefault("roles", {})[role] = name
    write_json(PREFS, prefs)


def resolve_role(role: str, prefs: dict) -> str:
    role = role.lower()
    if role not in ROLES:
        raise HerdError(f"Unknown role {role!r}. Choose one of: {', '.join(ROLES)}.")
    name = prefs.get("roles", {}).get(role)
    if not isinstance(name, str) or not name:
        raise HerdError(
            f"The {role} role is unsupported until you assign a validated local model: "
            f"`codex-herd config role {role} <model-id>`. No hosted fallback is used."
        )
    return name


def display_list(models: dict[str, dict], prefs: dict, fleet: dict) -> None:
    default = prefs.get("default_model")
    print("MODEL\tNODE(S)\tSIZE\tAVAILABILITY\tLOADED / CONTEXT\tCODEX CONTEXT\tMODEL MAX\tTOOLS\tDEFAULT")
    for name in sorted(models):
        m = models[name]
        size = f"{m['size_bytes'] / (1024**3):.1f} GiB" if m.get("size_bytes") else "?"
        loaded = ", ".join(f"{x['node']} ({x.get('context_length', '?'):,} ctx)" for x in m["loaded"]) or "unloaded"
        override = prefs.get("models", {}).get(name, {}).get("codex_context_window")
        contexts = [x["context_length"] for x in m["loaded"] if x.get("context_length")]
        entry = codex_entry(m, prefs)
        codex_ctx = f"{entry['context_window']:,} ({entry['context_source']})"
        availability = "online" if m["online_nodes"] else "offline"
        tools = (f"{m['tool_status']} ({m['tool_status_detail']})" if m["tool_status"] == "mixed" else m["tool_status"]) if m["tool_capable"] else ("embedding" if m["embedding_only"] else "not advertised")
        max_context = f"{m['model_context_window']:,}" if m["model_context_window"] else "unknown"
        print(f"{name}\t{','.join(m['online_nodes']) or ','.join(m['nodes']) or '?'}\t{size}\t{availability}\t{loaded}\t{codex_ctx}\t{max_context}\t{tools}\t{'*' if name == default else ''}")
    configured_roles = prefs.get("roles", {})
    role_summary = ", ".join(
        f"{role}={configured_roles[role]}" for role in ROLES if configured_roles.get(role)
    ) or "none"
    print(f"Configured local roles: {role_summary}")
    queues = fleet.get("queues", {})
    if isinstance(queues, dict):
        pending = in_flight = 0
        queue_counts_valid = True
        for queue in queues.values():
            if not isinstance(queue, dict):
                queue_counts_valid = False
                break
            queue_pending = queue.get("pending")
            queue_in_flight = queue.get("in_flight")
            if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in (queue_pending, queue_in_flight)):
                queue_counts_valid = False
                break
            pending += queue_pending
            in_flight += queue_in_flight
        queue_summary = f"Herd queue: {pending} pending, {in_flight} in-flight" if queue_counts_valid else "Herd queue: unavailable"
    else:
        queue_summary = "Herd queue: unavailable"
    ollama_active = fleet.get("fleet", {}).get("requests_active", "?")
    print(f"\nFleet nodes: {fleet.get('fleet', {}).get('nodes_online', '?')}/{fleet.get('fleet', {}).get('nodes_total', '?')} online; {queue_summary}; Ollama active-request telemetry: {ollama_active}")


def config_show(name: str, models: dict[str, dict], prefs: dict) -> None:
    model = models.get(name)
    if model is None:
        raise HerdError(f"Unknown model {name!r}; run `codex-herd list` to see the live inventory.")
    override = prefs.get("models", {}).get(name, {}).get("codex_context_window")
    codex_context, context_source = effective_codex_context(model, prefs)
    contexts = [x["context_length"] for x in model["loaded"] if x.get("context_length")]
    print(f"Model: {name}")
    print(f"Default model: {'yes' if prefs.get('default_model') == name else 'no'}")
    context_labels = {
        "user override": "saved local Codex preference",
        "loaded allocation on all online nodes": "live loaded backend allocation",
        "Ollama configured num_ctx on all online nodes": "Ollama configured num_ctx",
        "unverified safe fallback": "safe fallback; backend allocation unobserved",
    }
    catalog_context = f"{codex_context:,} ({context_labels[context_source]})"
    print(f"Codex catalog context: {catalog_context}")
    print(f"Model-declared maximum context: {model['model_context_window'] or 'unknown'}")
    print("Backend allocated context: " + (", ".join(f"{x['node']}={x['context_length']:,}" for x in model["loaded"]) if contexts else "unloaded; unknown"))
    timeout = stream_idle_timeout_ms(name, prefs)
    if timeout is None:
        print(f"Codex SSE idle timeout: {DEFAULT_STREAM_IDLE_TIMEOUT_MS:,} ms (Codex default; no saved per-model preference)")
    else:
        print(f"Codex SSE idle timeout: {timeout:,} ms (saved for sessions launched with this model)")
    print("  This is the client stream-inactivity limit, not a server generation timeout; `/model` switches do not change the active session value.")
    instructions = saved_developer_instructions(name, prefs)
    if instructions is None:
        print("Codex session developer instructions: none saved")
    else:
        print("Codex session developer instructions: saved for sessions launched explicitly with this model")
        print("  `/model` switches do not change instructions in the active session.")
        print(f"  {instructions!r}")
    if override:
        backend_context, backend_source = effective_codex_context(model, {"models": {}})
    else:
        backend_context, backend_source = None, "unverified safe fallback"
    if override and backend_source != "unverified safe fallback" and override > backend_context:
        backend_description = {
            "loaded allocation on all online nodes": "lowest live backend allocation",
            "Ollama configured num_ctx on all online nodes": "lowest Ollama configured num_ctx",
        }.get(backend_source, "known backend context")
        print(
            f"Context warning: saved Codex budget {override:,} exceeds the "
            f"{backend_description} {backend_context:,}. This preference changes "
            "Codex budgeting only; it does not raise Ollama's allocation."
        )
    print("Server model-derived Ollama parameters (read-only; Codex does not set these):")
    if model["model_parameters"]:
        for node, raw in model["model_parameters"].items():
            print(f"  {node}: {raw.strip().replace(chr(10), '; ')}")
    else:
        print("  unavailable (model metadata could not be read)")
    print("Per-model Codex sampling controls (temperature/top-p/top-k/repeat penalty/seed): unsupported; no saved values")
    print("Reasoning effort/thinking controls: not configured; Codex catalog advertises no selectable effort because Herd 0.12.3 does not map Codex reasoning_effort to Ollama think")
    print("Preferred node/routing score/priority/concurrency/keep-alive: not model-specific client controls in this Herd/Codex path")
    print("Max generated tokens: controlled by Codex model catalog/request; no separate per-model preference is exposed")
    print("Compaction: Codex manages history compaction using catalog context; no per-model override is exposed")


def configure(name: str, models: dict[str, dict], prefs: dict) -> None:
    model = eligible(name, models)
    config_show(name, models, prefs)
    if not sys.stdin.isatty():
        raise HerdError("Interactive config requires a terminal. Use `codex-herd config show MODEL` for read-only output.")
    old = prefs.get("models", {}).get(name, {}).get("codex_context_window")
    values = [x["context_length"] for x in model["loaded"] if x.get("context_length")]
    suggested = old or (min(values) if values else 4096)
    print("\nSupported preferences: Codex context metadata, Codex SSE idle timeout, and optional per-session developer instructions. Context changes Codex budgeting only. Timeout changes how long this Codex client waits for a streamed event; it does not change Ollama/Herd generation or routing.")
    raw = input(f"Codex context window [{suggested}; Enter keeps current]: ").strip()
    if raw:
        try:
            value = int(raw)
            if not 1024 <= value <= 262144:
                raise ValueError
        except ValueError as exc:
            raise HerdError("Context window must be an integer from 1,024 through 262,144.") from exc
        prefs.setdefault("models", {}).setdefault(name, {})["codex_context_window"] = value
    timeout_old = stream_idle_timeout_ms(name, prefs)
    timeout_default_seconds = timeout_old // 1000 if timeout_old is not None else DEFAULT_STREAM_IDLE_TIMEOUT_MS // 1000
    timeout_raw = input(
        f"Codex SSE idle timeout seconds [30–900; 0 resets to Codex default; "
        f"{timeout_default_seconds}]: "
    ).strip()
    if timeout_raw:
        try:
            seconds = int(timeout_raw)
            if seconds == 0:
                prefs.setdefault("models", {}).setdefault(name, {}).pop("stream_idle_timeout_ms", None)
            elif 30 <= seconds <= 900:
                prefs.setdefault("models", {}).setdefault(name, {})["stream_idle_timeout_ms"] = seconds * 1000
            else:
                raise ValueError
        except ValueError as exc:
            raise HerdError("Codex SSE idle timeout must be 0 or an integer from 30 through 900 seconds.") from exc
    old_instructions = saved_developer_instructions(name, prefs) or ""
    instructions_raw = input(
        "Codex session developer instructions (one line; Enter keeps current, !clear removes) "
        f"[{old_instructions!r}]: "
    ).strip()
    model_prefs = prefs.setdefault("models", {}).setdefault(name, {})
    if instructions_raw == "!clear":
        model_prefs.pop("developer_instructions", None)
    elif instructions_raw:
        model_prefs["developer_instructions"] = instructions_raw
    default_answer = input(f"Make {name} the default model? [y/N]: ").strip().lower()
    if default_answer in {"y", "yes"}:
        prefs["default_model"] = name
    write_json(PREFS, prefs)
    sync_catalog(models, prefs)
    print(f"Saved preferences to {PREFS}")


def launch(name: str, args: list[str], models: dict[str, dict], prefs: dict) -> int:
    eligible(name, models)
    sync_catalog(models, prefs, name)
    profile_name, _, _ = model_profile_paths(name)
    env = os.environ.copy()
    env["CODEX_HOME"] = str(CODEX_HOME)
    os.execvpe("codex", ["codex", "--no-daemon", "--profile", profile_name, "--model", name, "--config", 'model_provider="herd"', *args], env)
    return 127


def main(argv: list[str]) -> int:
    try:
        if argv and argv[0] in {"-h", "--help", "help"}:
            print("Usage: codex-herd [MODEL] [CODEX-ARGS...]\n       codex-herd role ROLE [CODEX-ARGS...]\n       codex-herd list\n       codex-herd refresh\n       codex-herd config [MODEL]\n       codex-herd config role ROLE MODEL\n       codex-herd config show MODEL")
            return 0
        models, fleet = fetch()
        prefs = read_prefs()
        if not argv or argv[0] == "--":
            selectable = sorted(
                m["name"] for m in models.values()
                if not m["embedding_only"] and m["tool_capable"] and m["online_nodes"]
            )
            name = prefs.get("default_model") or (selectable[0] if selectable else None)
            if name is None:
                raise HerdError("Herd returned no online Codex-eligible models")
            if prefs.get("default_model") is None:
                prefs["default_model"] = name
                write_json(PREFS, prefs)
            return launch(name, argv[1:] if argv[:1] == ["--"] else [], models, prefs)
        command = argv[0]
        if command == "role":
            if len(argv) < 2:
                raise HerdError(f"Usage: codex-herd role <{'|'.join(ROLES)}> [CODEX-ARGS...]")
            name = resolve_role(argv[1], prefs)
            return launch(name, argv[2:], models, prefs)
        if command == "list":
            display_list(models, prefs, fleet)
            return 0
        if command == "refresh":
            sync_catalog(models, prefs)
            print(f"Refreshed live fleet inventory and Codex catalog ({sum(not m['embedding_only'] and m['tool_capable'] for m in models.values())} Codex-eligible models).")
            return 0
        if command == "config":
            if len(argv) == 3 and argv[1] == "show":
                config_show(argv[2], models, prefs)
                return 0
            if len(argv) == 4 and argv[1] == "role":
                assign_role(argv[2], argv[3], models, prefs)
                print(f"Configured {argv[2].lower()} role: {argv[3]}")
                return 0
            name = argv[1] if len(argv) > 1 else prefs.get("default_model")
            configure(name, models, prefs)
            return 0
        name = command
        codex_args = argv[1:]
        return launch(name, codex_args, models, prefs)
    except HerdError as exc:
        print(f"codex-herd: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
