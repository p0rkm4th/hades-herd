import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CLIENT = REPO / "codex_herd.py"


class HerdHandler(BaseHTTPRequestHandler):
    models = []

    def log_message(self, *_args):
        pass

    def send_json(self, value):
        body = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        origin = f"http://127.0.0.1:{self.server.server_port}"
        if self.path == "/api/tags":
            self.send_json({"models": self.models})
        elif self.path == "/fleet/status":
            self.send_json({
                "fleet": {"nodes_online": 1, "nodes_total": 1, "requests_active": 0},
                "queues": {},
                "nodes": [{
                    "node_id": "test-node",
                    "status": "online",
                    "ollama_url": origin,
                    "ollama": {"models_loaded": []},
                }],
            })
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/show":
            self.send_json({
                "model_info": {"test.context_length": 131072},
                "parameters": "num_ctx 16384\ntemperature 0.2\n",
            })
        else:
            self.send_error(404)


class LauncherIntegrationTests(unittest.TestCase):
    def setUp(self):
        HerdHandler.models = [
            {
                "model": "z-model:latest",
                "digest": "a" * 64,
                "size": 1024,
                "details": {
                    "fleet_nodes": ["test-node"],
                    "family": "test",
                    "parameter_size": "1B",
                    "quantization_level": "Q4_K_M",
                },
                "capabilities": ["completion", "tools"],
            },
            {
                "model": "a-model:latest",
                "digest": "b" * 64,
                "size": 1024,
                "details": {
                    "fleet_nodes": ["test-node"],
                    "family": "test",
                    "parameter_size": "1B",
                    "quantization_level": "Q4_K_M",
                },
                "capabilities": ["completion", "tools"],
            },
        ]
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), HerdHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.fake_bin = self.root / "bin"
        self.fake_bin.mkdir()
        self.capture = self.root / "codex-capture.json"
        fake_codex = self.fake_bin / "codex"
        fake_codex.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, pathlib, sys\n"
            "home = pathlib.Path(os.environ['CODEX_HOME'])\n"
            "capture = {'args': sys.argv[1:], 'profile': (home / 'herd.config.toml').read_text(), "
            "'catalog': json.loads((home.parent / 'model-catalog.json').read_text()), "
            "'preferences': json.loads((home.parent / 'preferences.json').read_text()) if (home.parent / 'preferences.json').exists() else {}}\n"
            "pathlib.Path(os.environ['FAKE_CODEX_CAPTURE']).write_text(json.dumps(capture))\n"
            "raise SystemExit(int(os.environ.get('FAKE_CODEX_EXIT', '0')))\n"
        )
        fake_codex.chmod(0o755)
        self.env = os.environ.copy()
        self.env.update({
            "HOME": str(self.root / "home"),
            "PATH": str(self.fake_bin) + os.pathsep + self.env.get("PATH", ""),
            "CODEX_HERD_URL": f"http://127.0.0.1:{self.server.server_port}",
            "FAKE_CODEX_CAPTURE": str(self.capture),
            "FAKE_CODEX_EXIT": "23",
        })

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def run_client(self, *args):
        return subprocess.run(
            [sys.executable, str(CLIENT), *args],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_clean_home_default_launches_and_saves_first_model(self):
        result = self.run_client()
        self.assertEqual(result.returncode, 23, result.stderr)
        capture = json.loads(self.capture.read_text())
        self.assertEqual(capture["args"][capture["args"].index("--model") + 1], "a-model:latest")
        self.assertEqual(capture["preferences"]["default_model"], "a-model:latest")
        entries = {item["slug"]: item for item in capture["catalog"]["models"]}
        self.assertEqual(entries["a-model:latest"]["context_window"], 16384)
        self.assertIn("--no-daemon", capture["args"])
        self.assertEqual(capture["args"][-2:], ["--config", 'model_provider="herd"'])

    def test_explicit_model_is_used_on_clean_home_without_becoming_default(self):
        result = self.run_client("z-model:latest", "--help")
        self.assertEqual(result.returncode, 23, result.stderr)
        capture = json.loads(self.capture.read_text())
        self.assertEqual(capture["args"][capture["args"].index("--model") + 1], "z-model:latest")
        self.assertNotIn("default_model", capture["preferences"])
        self.assertEqual(capture["args"][-1], "--help")


if __name__ == "__main__":
    unittest.main(verbosity=2)
