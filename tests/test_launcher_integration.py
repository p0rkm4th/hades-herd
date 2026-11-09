import json
import os
import stat
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class HerdHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == "/api/tags":
            payload = {"models": [{"name": "alpha:latest", "model": "alpha:latest", "digest": "abc", "size": 100,
                "details": {"family": "test", "fleet_nodes": ["node-a"]}, "capabilities": ["tools"]}]}
        elif self.path == "/fleet/status":
            payload = {"nodes": [{"node_id": "node-a", "status": "online", "ollama_url": f"http://127.0.0.1:{self.server.server_port}/node"}]}
        elif self.path == "/node/api/tags":
            payload = {"models": [{"name": "alpha:latest", "digest": "abc"}]}
        else:
            self.send_error(404)
            return
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", "0")))
        body = json.dumps({"parameters": "num_ctx 16384", "model_info": {"x.context_length": 131072}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class LauncherSubprocessTests(unittest.TestCase):
    def test_clean_install_default_and_explicit_model_reach_fake_codex(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), HerdHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                fake_bin = root / "bin"
                fake_bin.mkdir()
                capture = root / "codex.json"
                fake_codex = fake_bin / "codex"
                fake_codex.write_text(
                    "#!/usr/bin/env python3\n"
                    "import json, os, sys\n"
                    "from pathlib import Path\n"
                    "home = Path(os.environ['CODEX_HOME'])\n"
                    "profile_name = sys.argv[sys.argv.index('--profile') + 1]\n"
                    "profile = (home/(profile_name+'.config.toml')).read_text()\n"
                    "catalog_path = json.loads(next(line.split('=',1)[1] for line in profile.splitlines() if line.startswith('model_catalog_json')))\n"
                    "catalog = json.loads(Path(catalog_path).read_text())\n"
                    "(Path(os.environ['CAPTURE'])).write_text(json.dumps({'args':sys.argv[1:], 'profile':profile, 'catalog':catalog}))\n"
                    "raise SystemExit(23)\n"
                )
                fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IXUSR)
                env = os.environ.copy()
                env.update({"HOME": str(root / "home"), "PATH": f"{fake_bin}:{env['PATH']}",
                    "CODEX_HERD_URL": f"http://127.0.0.1:{server.server_port}", "CAPTURE": str(capture)})
                helper = REPO / "codex_herd.py"
                first = subprocess.run(["python3", str(helper)], env=env, text=True, capture_output=True, timeout=10)
                self.assertEqual(first.returncode, 23, first.stderr)
                result = json.loads(capture.read_text())
                self.assertIn("alpha:latest", result["args"])
                self.assertIn('model = "alpha:latest"', result["profile"])
                self.assertIn('model_provider = "herd"', result["profile"])
                self.assertEqual(result["catalog"]["models"][0]["context_window"], 16384)
                self.assertEqual(result["catalog"]["models"][0]["slug"], "alpha:latest")
                self.assertEqual(
                    result["catalog"]["models"][0]["display_name"],
                    "HADES Test | Unverified | 16K | Node-A",
                )
                pref = root / "home/.config/codex-herd/preferences.json"
                self.assertEqual(json.loads(pref.read_text())["default_model"], "alpha:latest")

                second = subprocess.run(["python3", str(helper), "alpha:latest", "--help"], env=env,
                    text=True, capture_output=True, timeout=10)
                self.assertEqual(second.returncode, 23, second.stderr)
                result = json.loads(capture.read_text())
                self.assertEqual(result["args"][-1], "--help")
                self.assertIn('"X-Fleet-No-Fallback" = "true"', result["profile"])

                pref.write_text(json.dumps({
                    "default_model": "alpha:latest",
                    "models": {},
                    "roles": {"balanced": "alpha:latest"},
                }))
                third = subprocess.run(
                    ["python3", str(helper), "role", "balanced", "--help"], env=env,
                    text=True, capture_output=True, timeout=10,
                )
                self.assertEqual(third.returncode, 23, third.stderr)
                result = json.loads(capture.read_text())
                self.assertIn("alpha:latest", result["args"])
                self.assertEqual(result["args"][-1], "--help")
                self.assertEqual(json.loads(pref.read_text())["default_model"], "alpha:latest")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
