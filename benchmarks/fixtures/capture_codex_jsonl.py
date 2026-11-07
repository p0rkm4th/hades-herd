#!/usr/bin/env python3
"""Capture Codex JSONL privately and write a timestamped, content-free event index."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import json
import os
import selectors
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def event_metadata(line: bytes) -> dict[str, Any] | None:
    """Extract only structural event metadata; never retain IDs or text."""
    try:
        event = json.loads(line)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(event, dict):
        return None
    item = event.get("item")
    return {
        "type": event.get("type") if isinstance(event.get("type"), str) else None,
        "item_type": item.get("type") if isinstance(item, dict) and isinstance(item.get("type"), str) else None,
        "item_status": item.get("status") if isinstance(item, dict) and isinstance(item.get("status"), str) else None,
    }


def _new_private_file(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    return os.fdopen(fd, "wb")


def run(args: argparse.Namespace) -> int:
    if not args.command:
        raise ValueError("provide a command after --")
    if args.timeout <= 0 or args.grace < 0:
        raise ValueError("timeout must be positive and grace nonnegative")
    stdout_path, stderr_path, timeline_path, summary_path = map(
        Path, (args.stdout, args.stderr, args.timeline, args.summary)
    )
    if len({path.resolve() for path in (stdout_path, stderr_path, timeline_path, summary_path)}) != 4:
        raise ValueError("stdout, stderr, timeline, and summary paths must be different")

    stdin = open(args.input, "rb") if args.input else subprocess.DEVNULL
    started_ns = time.monotonic_ns()
    timed_out = False
    proc = None
    try:
        with ExitStack() as stack:
            raw_out = stack.enter_context(_new_private_file(stdout_path))
            raw_err = stack.enter_context(_new_private_file(stderr_path))
            index = stack.enter_context(_new_private_file(timeline_path))
            proc = subprocess.Popen(
                args.command,
                stdin=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                bufsize=0,
            )
            selector = selectors.DefaultSelector()
            assert proc.stdout is not None and proc.stderr is not None
            selector.register(proc.stdout, selectors.EVENT_READ, ("stdout", raw_out))
            selector.register(proc.stderr, selectors.EVENT_READ, ("stderr", raw_err))
            pending = bytearray()
            deadline = time.monotonic() + args.timeout
            interrupt_sent = False
            kill_deadline = None
            while selector.get_map():
                now = time.monotonic()
                if now >= deadline and not interrupt_sent:
                    timed_out = True
                    interrupt_sent = True
                    try:
                        os.killpg(proc.pid, signal.SIGINT)
                    except ProcessLookupError:
                        pass
                    kill_deadline = now + args.grace
                elif kill_deadline is not None and now >= kill_deadline:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    kill_deadline = None
                wait = 0.1
                if not interrupt_sent:
                    wait = min(wait, max(0.0, deadline - now))
                events = selector.select(wait)
                for key, _ in events:
                    chunk = key.fileobj.read(65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    stream, raw_file = key.data
                    raw_file.write(chunk)
                    if stream == "stdout":
                        pending.extend(chunk)
                        while b"\n" in pending:
                            line, _, rest = pending.partition(b"\n")
                            pending[:] = rest
                            metadata = event_metadata(line)
                            if metadata is not None:
                                index.write((json.dumps({"monotonic_ns": time.monotonic_ns(), **metadata}) + "\n").encode())
            if pending:
                metadata = event_metadata(bytes(pending))
                if metadata is not None:
                    index.write((json.dumps({"monotonic_ns": time.monotonic_ns(), **metadata}) + "\n").encode())
            exit_status = proc.wait()
            selector.close()
            proc.stdout.close()
            proc.stderr.close()
    finally:
        if hasattr(stdin, "close"):
            stdin.close()
        if proc is not None:
            if proc.stdout is not None:
                proc.stdout.close()
            if proc.stderr is not None:
                proc.stderr.close()

    summary = {
        "command_exit_status": exit_status,
        "timed_out": timed_out,
        "duration_ns": time.monotonic_ns() - started_ns,
        "raw_stdout_path": str(stdout_path),
        "raw_stderr_path": str(stderr_path),
        "event_index_path": str(timeline_path),
        "raw_logs_are_private": True,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with _new_private_file(summary_path) as out:
        out.write((json.dumps(summary, indent=2) + "\n").encode())
    if timed_out:
        return 124
    return exit_status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, required=True, help="hard process timeout in seconds")
    parser.add_argument("--grace", type=float, default=5, help="seconds between SIGINT and SIGKILL")
    parser.add_argument("--input", help="optional task-instruction file supplied to the child stdin")
    parser.add_argument("--stdout", required=True, help="private raw Codex JSONL output path")
    parser.add_argument("--stderr", required=True, help="private raw Codex stderr path")
    parser.add_argument("--timeline", required=True, help="private metadata-only timestamped event index")
    parser.add_argument("--summary", required=True, help="private run summary JSON path")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="child command, placed after --")
    args = parser.parse_args()
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    try:
        return run(args)
    except (OSError, ValueError) as exc:
        print(f"capture_codex_jsonl: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
