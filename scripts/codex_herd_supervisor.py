#!/usr/bin/env python3
"""Bound a local Codex-Herd JSONL exec and preserve a private checkpoint."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import queue
import re
import shlex
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path


TOOL_ITEM_TYPES = {"command_execution", "function_call", "mcp_tool_call", "web_search"}
TEST_COMMAND = re.compile(r"\b(pytest|unittest|tox|nox|cargo test|npm test|pnpm test|yarn test|go test)\b", re.I)


def _text(value: object, limit: int = 500) -> str:
    if isinstance(value, str):
        return value[:limit]
    if value is None:
        return ""
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False)[:limit]
    except (TypeError, ValueError):
        return str(value)[:limit]


def _usage(event: dict) -> int | None:
    usage = event.get("usage") or event.get("token_usage")
    if not isinstance(usage, dict):
        response = event.get("response")
        usage = response.get("usage") if isinstance(response, dict) else None
    if not isinstance(usage, dict):
        return None
    total = usage.get("total_tokens")
    if isinstance(total, int):
        return total
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    if isinstance(input_tokens, int) and isinstance(output_tokens, int):
        return input_tokens + output_tokens
    return None


def parse_tool_event(event: dict) -> tuple[str, dict] | None:
    kind = event.get("type")
    item = event.get("item")
    if kind not in {"item.started", "item.completed"} or not isinstance(item, dict):
        return None
    item_type = item.get("type")
    if item_type not in TOOL_ITEM_TYPES:
        return None
    return kind, item


def _git_state(workspace: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(workspace), "status", "--short"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    return result.stdout.splitlines()[:100] if result.returncode == 0 else []


class Guard:
    def __init__(self, args: argparse.Namespace, workspace: Path, log_path: Path, checkpoint_path: Path):
        self.args = args
        self.workspace = workspace
        self.log_path = log_path
        self.checkpoint_path = checkpoint_path
        self.calls = 0
        self.failures = 0
        self.tokens = 0
        self.token_events = 0
        self.repeated = collections.Counter()
        self.pending: dict[str, str] = {}
        self.actions: list[dict[str, object]] = []
        self.last_test_failure = ""
        self.stop_reason = ""
        self._checkpoint("running", "Await Codex-Herd JSONL events.")

    def _checkpoint(self, state: str, next_action: str) -> None:
        record = {
            "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "state": state,
            "goal": self.args.goal,
            "acceptance": self.args.acceptance,
            "limits": {
                "wall_seconds": self.args.wall_seconds,
                "tool_calls": self.args.max_tool_calls,
                "same_command": self.args.max_identical,
                "consecutive_failures": self.args.max_failures,
                "cumulative_tokens": self.args.max_tokens,
            },
            "tool_calls_started": self.calls,
            "consecutive_failures": self.failures,
            "reported_cumulative_tokens": self.tokens,
            "token_usage_events": self.token_events,
            "files_changed": _git_state(self.workspace),
            "completed_actions": self.actions[-30:],
            "latest_test_failure": self.last_test_failure,
            "logs": {"jsonl": self.log_path.name, "stderr": self.log_path.with_suffix(".stderr.log").name},
            "next_required_action": next_action,
        }
        temp = self.checkpoint_path.with_suffix(".tmp")
        temp.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        os.chmod(temp, 0o600)
        temp.replace(self.checkpoint_path)

    def observe(self, raw: str, event: dict) -> None:
        tool = parse_tool_event(event)
        if tool:
            kind, item = tool
            command = _text(item.get("command") or item.get("name") or item.get("arguments") or item_type(item), 2000)
            item_id = _text(item.get("id"), 200)
            if kind == "item.started":
                self.calls += 1
                normalized = " ".join(command.split())
                self.repeated[normalized] += 1
                self.pending[item_id] = command
                if self.calls > self.args.max_tool_calls:
                    self.stop_reason = "tool-call limit reached"
                if self.repeated[normalized] > self.args.max_identical:
                    self.stop_reason = "identical-command limit reached"
            else:
                exit_code = item.get("exit_code")
                failed = item.get("status") == "failed" or (isinstance(exit_code, int) and exit_code != 0)
                self.failures = self.failures + 1 if failed else 0
                self.actions.append({
                    "tool": item_type(item),
                    "command": command,
                    "status": item.get("status", "failed" if failed else "completed"),
                    "exit_code": exit_code if isinstance(exit_code, int) else None,
                })
                if failed and TEST_COMMAND.search(command):
                    output = _text(item.get("aggregated_output") or item.get("output"), 1200)
                    self.last_test_failure = output or f"Test command failed: {command[:300]}"
                if self.failures >= self.args.max_failures:
                    self.stop_reason = "consecutive failed-tool limit reached"
                self.pending.pop(item_id, None)

        if event.get("type") == "turn.completed":
            usage = _usage(event)
            if usage is not None:
                self.tokens += usage
                self.token_events += 1
                if self.tokens > self.args.max_tokens:
                    self.stop_reason = "reported cumulative-token limit reached"
        self._checkpoint("limit-reached" if self.stop_reason else "running", self.stop_reason or "Continue the active turn; verify tests before accepting changes.")

    def finish(self, state: str, detail: str) -> None:
        self._checkpoint(state, detail)


def item_type(item: dict) -> str:
    return _text(item.get("type") or "tool", 100)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--log-dir", type=Path, default=None)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--acceptance", required=True)
    parser.add_argument("--wall-seconds", type=int, default=180)
    parser.add_argument("--max-tool-calls", type=int, default=24)
    parser.add_argument("--max-identical", type=int, default=2)
    parser.add_argument("--max-failures", type=int, default=2)
    parser.add_argument("--max-tokens", type=int, default=500_000)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def validate(args: argparse.Namespace) -> list[str]:
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        raise ValueError("provide a command after --")
    if not any("codex-herd" in arg for arg in command):
        raise ValueError("only Codex-Herd local commands are permitted")
    if "--json" not in command:
        raise ValueError("Codex exec must use --json so tool limits can be monitored")
    if any(arg in {"--dangerously-bypass-approvals-and-sandbox", "danger-full-access"} for arg in command):
        raise ValueError("sandbox bypass is prohibited")
    for name, value in (("wall-seconds", args.wall_seconds), ("max-tool-calls", args.max_tool_calls),
                        ("max-identical", args.max_identical), ("max-failures", args.max_failures),
                        ("max-tokens", args.max_tokens)):
        if value <= 0:
            raise ValueError(f"--{name} must be positive")
    return command


def run(args: argparse.Namespace) -> int:
    command = validate(args)
    workspace = args.workspace.resolve()
    if not workspace.is_dir():
        raise ValueError(f"workspace does not exist: {workspace}")
    log_dir = (args.log_dir or workspace / ".codex-herd-supervisor").resolve()
    log_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(log_dir, 0o700)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"{stamp}.jsonl"
    stderr_path = log_path.with_suffix(".stderr.log")
    checkpoint_path = log_path.with_suffix(".checkpoint.json")
    for path in (log_path, stderr_path, checkpoint_path):
        if path.exists():
            raise ValueError(f"refusing to overwrite existing run artifact: {path.name}")
    guard = Guard(args, workspace, log_path, checkpoint_path)
    start = time.monotonic()
    with log_path.open("x", encoding="utf-8") as log, stderr_path.open("x", encoding="utf-8") as err:
        os.chmod(log_path, 0o600)
        os.chmod(stderr_path, 0o600)
        process = subprocess.Popen(command, cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, bufsize=1, start_new_session=True)

        def copy_stderr() -> None:
            assert process.stderr
            for line in process.stderr:
                err.write(line)
                err.flush()
                sys.stderr.write(line)
                sys.stderr.flush()

        thread = threading.Thread(target=copy_stderr, daemon=True)
        thread.start()
        timed_out = False
        assert process.stdout
        lines: queue.Queue[str | None] = queue.Queue()

        def read_stdout() -> None:
            for output_line in process.stdout:
                lines.put(output_line)
            lines.put(None)

        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stdout_thread.start()
        while True:
            remaining = args.wall_seconds - (time.monotonic() - start)
            if remaining <= 0:
                timed_out = True
                guard.stop_reason = "wall-clock limit reached"
                break
            try:
                line = lines.get(timeout=remaining)
            except queue.Empty:
                timed_out = True
                guard.stop_reason = "wall-clock limit reached"
                break
            if line is None:
                break
            log.write(line)
            log.flush()
            sys.stdout.write(line)
            sys.stdout.flush()
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                guard.observe(line, event)
            if guard.stop_reason:
                break
        if not guard.stop_reason and process.poll() is None and time.monotonic() - start >= args.wall_seconds:
            timed_out = True
            guard.stop_reason = "wall-clock limit reached"
        if guard.stop_reason:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=3)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            thread.join(timeout=2)
            stdout_thread.join(timeout=2)
            process.stdout.close()
            process.stderr.close()
            state = "timed-out" if timed_out else "stopped-by-limit"
            guard.finish(state, "Read checkpoint/logs and inspect the preserved worktree before resuming; do not replay completed actions.")
            print(f"codex-herd-supervisor: {guard.stop_reason}; checkpoint={checkpoint_path}", file=sys.stderr)
            return 124 if timed_out else 125
        result = process.wait()
        thread.join(timeout=2)
        stdout_thread.join(timeout=2)
        process.stdout.close()
        process.stderr.close()
    elapsed = time.monotonic() - start
    guard.finish("completed" if result == 0 else "failed", "Independently verify the final diff and acceptance tests before accepting this result.")
    print(f"codex-herd-supervisor: exit={result}; elapsed={elapsed:.1f}s; tool_calls={guard.calls}; reported_tokens={guard.tokens}; checkpoint={checkpoint_path}", file=sys.stderr)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"codex-herd-supervisor: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
