#!/usr/bin/env python3
"""Run isolated local Codex/Herd coding fixtures; emit only sanitized metrics."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from pathlib import Path

try:
    from fixtures.local_coding_reliability import FULL_TASKS, TASKS
except ModuleNotFoundError:
    from benchmarks.fixtures.local_coding_reliability import FULL_TASKS, TASKS

ROOT = Path(__file__).resolve().parents[1]
FISH_FUNCTION = Path.home() / ".config/fish/functions/codex-herd.fish"
DEFAULT_TIMEOUT = 180


def reader(pipe, label, events):
    for line in iter(pipe.readline, ""):
        events.put((label, line, time.monotonic()))
    events.put((label, None, time.monotonic()))


def initial_repo(path: Path, spec: dict) -> None:
    for name, content in spec["files"].items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(path), "-c", "user.name=Local Benchmark", "-c",
         "user.email=local-benchmark.invalid", "commit", "-qm", "fixture baseline"],
        check=True,
    )


def pytest_result(workspace: Path) -> dict:
    pytest = shutil.which("pytest")
    if pytest:
        command = [pytest, "-q", "-p", "no:cacheprovider"]
    else:
        uv = shutil.which("uv")
        python = shutil.which("python3.11")
        if not uv or not python:
            return {"exit_code": 127, "environment_error": "pytest_and_uv_unavailable"}
        command = [uv, "run", "--isolated", "--with", "pytest", "--python", python,
                   "--", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    run = subprocess.run(
        command, cwd=workspace,
        capture_output=True, text=True, timeout=30,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    counts = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|error|skipped)", run.stdout + run.stderr)}
    return {"exit_code": run.returncode, **counts}


def independent_verify(workspace: Path, spec: dict) -> tuple[bool, str]:
    uv = shutil.which("uv")
    python = shutil.which("python3.11")
    if not uv or not python:
        return False, "pytest_environment_unavailable"
    bootstrap = "import sys; sys.path.insert(0, sys.argv[1]); exec(compile(sys.argv[2], '<independent-check>', 'exec'))"
    run = subprocess.run(
        [uv, "run", "--isolated", "--with", "pytest", "--python", python,
         "--", "python", "-c", bootstrap, str(workspace), spec["verify"]],
        cwd=workspace, capture_output=True, text=True, timeout=30,
    )
    if run.returncode == 0:
        return True, "passed"
    if "ModuleNotFoundError" in run.stderr:
        return False, "missing_test_dependency"
    line = re.search(r'File "<independent-check>", line (\d+)', run.stderr)
    if line:
        return False, f"assertion_failed_line_{line.group(1)}"
    return False, "assertion_failed"


def run_codex(model: str, context: int, workspace: Path, prompt: str, timeout: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="codex-herd-local-") as home:
        home_path = Path(home)
        helper_root = home_path / ".config/codex-herd"
        prefs = helper_root / "preferences.json"
        helper_root.mkdir(parents=True)
        shutil.copy2(ROOT / "codex_herd.py", helper_root / "codex_herd.py")
        prefs.write_text(json.dumps({"models": {model: {"codex_context_window": context}}}))
        bin_dir = home_path / "bin"
        bin_dir.mkdir()
        pytest_wrapper = bin_dir / "pytest"
        uv = shutil.which("uv")
        python = shutil.which("python3.11")
        if not shutil.which("pytest") and uv and python:
            pytest_wrapper.write_text(
                "#!/bin/sh\nexec " + uv + " run --isolated --with pytest --python "
                + python + " -- python -m pytest \"$@\"\n"
            )
            pytest_wrapper.chmod(0o755)
        env = os.environ.copy()
        env["HOME"] = home
        env.pop("CODEX_HOME", None)
        env["BENCH_MODEL"] = model
        env["BENCH_CWD"] = str(workspace)
        env["BENCH_PROMPT"] = prompt
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        for key in ("OPENAI_API_KEY", "CODEX_API_KEY", "AZURE_OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
            env.pop(key, None)
        command = (
            f"source {FISH_FUNCTION}; cd $BENCH_CWD; "
            "codex-herd $BENCH_MODEL exec --ephemeral --sandbox workspace-write "
            "--config 'approval_policy=\"never\"' -C $BENCH_CWD --json $BENCH_PROMPT"
        )
        start = time.monotonic()
        proc = subprocess.Popen(
            ["fish", "--no-config", "-c", command], cwd=workspace, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1,
            start_new_session=True,
        )
        events: queue.Queue = queue.Queue()
        threads = [
            threading.Thread(target=reader, args=(proc.stdout, "stdout", events), daemon=True),
            threading.Thread(target=reader, args=(proc.stderr, "stderr", events), daemon=True),
        ]
        for thread in threads:
            thread.start()
        deadline = start + timeout
        done = set()
        stderr_parts = []
        first_tool = None
        tool_calls = tool_success = tool_failures = 0
        repeated = 0
        command_hashes: set[str] = set()
        compactions = 0
        usage = None
        completed_turn = False
        raw_events = 0
        while len(done) < 2:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                label, line, at = events.get(timeout=min(0.2, remaining))
            except queue.Empty:
                if proc.poll() is not None and all(not thread.is_alive() for thread in threads):
                    break
                continue
            if line is None:
                done.add(label)
                continue
            if label == "stderr":
                stderr_parts.append(line)
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            raw_events += 1
            event_type = event.get("type", "")
            item = event.get("item", {}) if isinstance(event.get("item"), dict) else {}
            item_type = item.get("type", "")
            if event_type in {"context_compaction", "context.compacted", "compaction.completed"}:
                compactions += 1
            if event_type in {"turn.completed", "turn_complete"}:
                completed_turn = True
                usage = event.get("usage") or event.get("total_token_usage")
            if item_type in {"command_execution", "function_call", "tool_call"}:
                if first_tool is None:
                    first_tool = at - start
                if event_type.endswith(("started", "added")):
                    tool_calls += 1
                    command = item.get("command") or item.get("arguments") or item.get("input") or ""
                    digest = hashlib.sha256(str(command).encode()).hexdigest()
                    if digest in command_hashes:
                        repeated += 1
                    command_hashes.add(digest)
                elif event_type.endswith("completed"):
                    code = item.get("exit_code")
                    if code == 0 or (code is None and item.get("status") == "completed"):
                        tool_success += 1
                    elif code is not None or item.get("status") in {"failed", "error"}:
                        tool_failures += 1
        timed_out = time.monotonic() >= deadline and proc.poll() is None
        if timed_out:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=3)
        else:
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=3)
        for thread in threads:
            thread.join(timeout=1)
        stderr = "".join(stderr_parts).lower()
        profile_files = list((home_path / ".config/codex-herd/codex-home").glob("herd-*.config.toml"))
        profile = profile_files[0].read_text() if profile_files else ""
        base_match = re.search(r'^base_url = "([^"]+)"$', profile, re.MULTILINE)
        host = urllib.parse.urlsplit(base_match.group(1)).hostname if base_match else None
        try:
            local_host = host == "localhost" or ipaddress.ip_address(host).is_private
        except ValueError:
            local_host = False
        local_profile = (
            local_host and 'wire_api = "responses"' in profile
            and "requires_openai_auth = false" in profile
        )
        no_fallback = '"X-Fleet-No-Fallback" = "true"' in profile
        return {
            "elapsed_s": round(time.monotonic() - start, 2),
            "first_tool_s": round(first_tool, 2) if first_tool is not None else None,
            "tool_calls": tool_calls,
            "tool_events_completed": tool_success,
            "tool_events_failed": tool_failures,
            "repeated_commands": repeated,
            "compactions": compactions,
            "usage": usage,
            "event_count": raw_events,
            "turn_completed": completed_turn,
            "exit_code": proc.returncode,
            "timeout": timed_out,
            "sse_error": "idle timeout" in stderr or "stream disconnected" in stderr,
            "local_responses_profile": local_profile and no_fallback,
        }


def run_task(model: str, context: int, task_name: str, timeout: int) -> dict:
    spec = TASKS[task_name]
    with tempfile.TemporaryDirectory(prefix=f"hades-{task_name}-", dir=ROOT / "benchmarks") as tmp:
        workspace = Path(tmp) / "repo"
        workspace.mkdir()
        initial_repo(workspace, spec)
        baseline = pytest_result(workspace)
        result = run_codex(model, context, workspace, spec["prompt"], timeout)
        for cache_dir in workspace.rglob("__pycache__"):
            shutil.rmtree(cache_dir, ignore_errors=True)
        for cache_dir in workspace.rglob(".pytest_cache"):
            shutil.rmtree(cache_dir, ignore_errors=True)
        changed = subprocess.run(
            ["git", "-C", str(workspace), "status", "--porcelain"],
            check=True, capture_output=True, text=True,
        ).stdout.splitlines()
        paths = sorted(line[3:] for line in changed)
        allowed = set(spec["allowed"])
        after = pytest_result(workspace)
        verified, verify_status = independent_verify(workspace, spec)
        passed = (
            result["turn_completed"] and result["exit_code"] == 0 and result["local_responses_profile"]
            and bool(paths) and set(paths) <= allowed and after["exit_code"] == 0 and verified
        )
        return {
            "task": task_name,
            "pass": passed,
            "baseline_tests": baseline,
            "changed_paths": paths,
            "final_tests": after,
            "independent_check": verify_status,
            **result,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--context", required=True, type=int)
    parser.add_argument("--phase", choices=("smoke", "full"), required=True)
    parser.add_argument("--tasks", nargs="+", choices=tuple(TASKS))
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    args = parser.parse_args()
    if not FISH_FUNCTION.exists():
        parser.error("installed Fish codex-herd function is unavailable")
    if shutil.which("fish") is None or shutil.which("codex") is None:
        parser.error("Fish or Codex CLI is unavailable")
    names = ("smoke",) if args.phase == "smoke" else tuple(args.tasks or FULL_TASKS)
    results = []
    for name in names:
        result = run_task(args.model, args.context, name, args.timeout)
        results.append(result)
        print(json.dumps(result, sort_keys=True), flush=True)
        if args.phase == "full" and sum(not item["pass"] for item in results) >= 2:
            print(json.dumps({"stopped_early": "4-of-5 threshold is no longer reachable"}))
            break
    return 0 if all(r["pass"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
