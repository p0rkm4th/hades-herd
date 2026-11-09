import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "codex_herd_supervisor.py"
SPEC = importlib.util.spec_from_file_location("codex_herd_supervisor", MODULE_PATH)
supervisor = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(supervisor)


class SupervisorTests(unittest.TestCase):
    def test_wall_limit_interrupts_silent_process_and_preserves_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "work"
            workspace.mkdir()
            command = root / "codex-herd"
            command.write_text("#!/bin/sh\nsleep 10\n")
            command.chmod(0o700)
            args = supervisor.build_parser().parse_args([
                "--workspace", str(workspace), "--log-dir", str(root / "logs"),
                "--goal", "fixture", "--acceptance", "exit cleanly", "--wall-seconds", "1",
                "--", str(command), "exec", "--json",
            ])
            self.assertEqual(supervisor.run(args), 124)
            checkpoints = list((root / "logs").glob("*.checkpoint.json"))
            self.assertEqual(len(checkpoints), 1)
            self.assertEqual(__import__("json").loads(checkpoints[0].read_text())["state"], "timed-out")
            self.assertEqual(checkpoints[0].stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
