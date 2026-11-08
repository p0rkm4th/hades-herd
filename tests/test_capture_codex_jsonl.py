import json
import stat
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from benchmarks.fixtures.capture_codex_jsonl import run


class CodexEventCaptureTests(unittest.TestCase):
    def test_preserves_private_streams_and_writes_content_free_timeline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {name: root / name for name in ("stdout", "stderr", "timeline", "summary")}
            secret = "DO_NOT_COPY_COMMAND_OR_RESPONSE"
            event = json.dumps({
                "type": "item.completed",
                "item": {"type": "command_execution", "status": "completed", "command": secret},
            })
            status = run(Namespace(
                command=[sys.executable, "-c", f"import sys; print({event!r}); print({secret!r}, file=sys.stderr)"],
                timeout=5,
                grace=0.1,
                input=None,
                cwd=None,
                stdout=str(paths["stdout"]),
                stderr=str(paths["stderr"]),
                timeline=str(paths["timeline"]),
                summary=str(paths["summary"]),
            ))
            self.assertEqual(status, 0)
            self.assertIn(secret.encode(), paths["stdout"].read_bytes())
            self.assertIn(secret.encode(), paths["stderr"].read_bytes())
            timeline = [json.loads(line) for line in paths["timeline"].read_text().splitlines()]
            self.assertEqual(timeline, [{
                "monotonic_ns": timeline[0]["monotonic_ns"],
                "type": "item.completed",
                "item_type": "command_execution",
                "item_status": "completed",
            }])
            self.assertNotIn(secret, paths["timeline"].read_text())
            for path in paths.values():
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_timeout_terminates_process_group_and_returns_124(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {name: root / name for name in ("stdout", "stderr", "timeline", "summary")}
            status = run(Namespace(
                command=[sys.executable, "-c", "import time; time.sleep(30)"],
                timeout=0.1,
                grace=0.1,
                input=None,
                cwd=None,
                stdout=str(paths["stdout"]),
                stderr=str(paths["stderr"]),
                timeline=str(paths["timeline"]),
                summary=str(paths["summary"]),
            ))
            self.assertEqual(status, 124)
            self.assertTrue(json.loads(paths["summary"].read_text())["timed_out"])

    def test_timeout_still_kills_descendant_when_command_leader_exits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {name: root / name for name in ("stdout", "stderr", "timeline", "summary")}
            child = "import subprocess,sys; subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])"
            status = run(Namespace(
                command=[sys.executable, "-c", child],
                timeout=0.1,
                grace=0.2,
                input=None,
                cwd=None,
                stdout=str(paths["stdout"]),
                stderr=str(paths["stderr"]),
                timeline=str(paths["timeline"]),
                summary=str(paths["summary"]),
            ))
            self.assertEqual(status, 124)

    def test_nonzero_exit_status_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {name: root / name for name in ("stdout", "stderr", "timeline", "summary")}
            status = run(Namespace(
                command=[sys.executable, "-c", "raise SystemExit(23)"],
                timeout=5,
                grace=0.1,
                input=None,
                cwd=None,
                stdout=str(paths["stdout"]),
                stderr=str(paths["stderr"]),
                timeline=str(paths["timeline"]),
                summary=str(paths["summary"]),
            ))
            self.assertEqual(status, 23)

    def test_child_runs_in_explicit_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child_cwd = root / "task"
            child_cwd.mkdir()
            paths = {name: root / name for name in ("stdout", "stderr", "timeline", "summary")}
            status = run(Namespace(
                command=[sys.executable, "-c", "import os; print(os.getcwd())"],
                timeout=5,
                grace=0.1,
                input=None,
                cwd=str(child_cwd),
                stdout=str(paths["stdout"]),
                stderr=str(paths["stderr"]),
                timeline=str(paths["timeline"]),
                summary=str(paths["summary"]),
            ))
            self.assertEqual(status, 0)
            self.assertEqual(paths["stdout"].read_text().strip(), str(child_cwd))


if __name__ == "__main__":
    unittest.main()
