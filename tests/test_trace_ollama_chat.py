import http.client
import json
import os
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from benchmarks.fixtures import trace_ollama_chat


class OllamaMetadataProxyTests(unittest.TestCase):
    def test_stream_forwards_unchanged_and_captures_only_tool_metadata(self):
        stream_body = (
            b'{"message":{"role":"assistant","tool_calls":[{"function":{"name":"exec_command",'
            b'"arguments":{"cmd":"ARGUMENT_SENTINEL"}}}]},"done":false}\n'
            b'{"message":{"role":"assistant","content":"RESPONSE_SENTINEL"},"done":true,'
            b'"prompt_eval_count":17,"eval_count":3}\n'
        )
        received = []

        class OllamaHandler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                received.append(self.rfile.read(int(self.headers["Content-Length"])))
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.send_header("Content-Length", str(len(stream_body)))
                self.end_headers()
                self.wfile.write(stream_body)

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), OllamaHandler)
        upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
        upstream_thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                capture = root / "ollama-metadata.jsonl"
                proxy = trace_ollama_chat.OllamaTraceServer(
                    ("127.0.0.1", 0), f"http://127.0.0.1:{upstream.server_port}", str(capture)
                )
                proxy_thread = threading.Thread(target=proxy.serve_forever, daemon=True)
                proxy_thread.start()
                try:
                    body = json.dumps({
                        "model": "fixture-model:latest",
                        "stream": True,
                        "messages": [{"role": "user", "content": "PROMPT_SENTINEL"}],
                        "tools": [],
                        "tool_schemas_secret": "SCHEMA_SENTINEL",
                    }).encode()
                    connection = http.client.HTTPConnection(
                        "127.0.0.1", proxy.server_port, timeout=4
                    )
                    connection.request(
                        "POST", "/api/chat", body=body,
                        headers={
                            "Content-Type": "application/json",
                            "Content-Length": str(len(body)),
                        },
                    )
                    response = connection.getresponse()
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.read(), stream_body)
                    connection.close()

                    deadline = time.monotonic() + 1
                    while not capture.read_text().strip() and time.monotonic() < deadline:
                        time.sleep(0.01)
                    record = json.loads(capture.read_text().splitlines()[0])
                    self.assertEqual(received, [body])
                    self.assertEqual(record["request"], {
                        "endpoint": "/api/chat",
                        "json_request": True,
                        "model": "fixture-model:latest",
                        "stream": True,
                        "tools_field_present": True,
                        "tool_count": 0,
                        "tool_names": [],
                        "message_count": 1,
                    })
                    self.assertEqual(record["status_code"], 200)
                    self.assertEqual(record["response"], {
                        "done": True,
                        "prompt_eval_count": 17,
                        "eval_count": 3,
                        "tool_call_count": 1,
                        "tool_call_names": ["exec_command"],
                    })
                    self.assertEqual(os.stat(capture).st_mode & 0o777, 0o600)
                    serialized = capture.read_text()
                    for secret in (
                        "PROMPT_SENTINEL",
                        "SCHEMA_SENTINEL",
                        "ARGUMENT_SENTINEL",
                        "RESPONSE_SENTINEL",
                    ):
                        self.assertNotIn(secret, serialized)
                finally:
                    proxy.shutdown()
                    proxy.server_close()
        finally:
            upstream.shutdown()
            upstream.server_close()

    def test_absent_tools_remains_distinct_from_explicit_empty(self):
        absent = trace_ollama_chat.request_metadata(
            "/api/chat", b'{"model":"x","messages":[],"stream":false}'
        )
        empty = trace_ollama_chat.request_metadata(
            "/api/chat", b'{"model":"x","messages":[],"tools":[],"stream":false}'
        )
        self.assertFalse(absent["tools_field_present"])
        self.assertIsNone(absent["tool_count"])
        self.assertTrue(empty["tools_field_present"])
        self.assertEqual(empty["tool_count"], 0)

    def test_proxy_rejects_nonloopback_bind_and_upstream(self):
        with tempfile.TemporaryDirectory() as directory:
            capture = str(Path(directory) / "metadata.jsonl")
            with self.assertRaisesRegex(ValueError, "must bind to 127.0.0.1"):
                trace_ollama_chat.OllamaTraceServer(
                    ("0.0.0.0", 0), "http://127.0.0.1:11434", capture
                )
            with self.assertRaisesRegex(ValueError, "upstream must be loopback"):
                trace_ollama_chat.OllamaTraceServer(
                    ("127.0.0.1", 0), "http://example.test:11434", capture
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
