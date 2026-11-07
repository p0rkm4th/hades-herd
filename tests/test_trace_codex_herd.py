import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks" / "fixtures"))
import trace_codex_herd


class TraceMetadataTests(unittest.TestCase):
    def test_request_summary_keeps_tool_metadata_but_not_prompt_or_tool_arguments(self):
        summary = trace_codex_herd.request_metadata(json.dumps({
            "input": [
                {"type": "message", "content": "PRIVATE PROMPT SENTINEL"},
                {"type": "additional_tools", "role": "developer", "tools": [
                    {"type": "function", "name": "exec_command", "parameters": {"secret_schema": "discard"}},
                    {"type": "namespace", "name": "multi_agent_v1", "tools": [{"name": "spawn_agent"}]},
                ]},
                {"type": "function_call", "name": "read_file", "arguments": "PRIVATE ARGUMENT SENTINEL"},
                {"type": "function_call_output", "output": "PRIVATE TOOL RESULT SENTINEL"},
            ],
            "reasoning": {"effort": "low"},
        }).encode())
        serialized = json.dumps(summary)
        self.assertEqual(summary["tool_names"], ["exec_command", "multi_agent_v1", "spawn_agent"])
        self.assertFalse(summary["read_file_advertised"])
        self.assertFalse(summary["tools_field_present"])
        self.assertTrue(summary["additional_tools_present"])
        self.assertEqual(summary["additional_tool_count"], 2)
        self.assertIn("additional_tools", summary["input_item_types"])
        self.assertEqual(summary["prior_function_call_names"], ["read_file"])
        self.assertEqual(summary["tool_result_count"], 1)
        self.assertEqual(summary["reasoning_effort"], "low")
        for sentinel in ("PRIVATE PROMPT", "PRIVATE ARGUMENT", "PRIVATE TOOL RESULT", "secret_schema"):
            self.assertNotIn(sentinel, serialized)

    def test_sse_summary_handles_chunk_boundaries_without_capturing_arguments_or_text(self):
        parser = trace_codex_herd.SSEMetadata()
        frame = (
            b'event: response.output_item.done\ndata: {"type":"response.output_item.done",'
            b'"item":{"type":"function_call","name":"read_file","call_id":"call-secret",'
            b'"arguments":"PRIVATE ARGUMENT SENTINEL"}}\n\n'
            b'event: response.completed\ndata: {"type":"response.completed","response":'
            b'{"status":"completed","output":[{"type":"message","content":'
            b'[{"type":"output_text","text":"PRIVATE RESPONSE SENTINEL"}]}],"usage":'
            b'{"input_tokens":12,"output_tokens":4,"total_tokens":16}}}\n\n'
        )
        parser.feed(frame[:27])
        parser.feed(frame[27:])
        summary = json.dumps({"items": parser.items, "status": parser.terminal_status, "usage": parser.usage})
        self.assertIn('"name": "read_file"', summary)
        self.assertEqual(parser.terminal_status, "completed")
        self.assertEqual(parser.usage["total_tokens"], 16)
        for sentinel in ("PRIVATE ARGUMENT", "PRIVATE RESPONSE", "call-secret"):
            self.assertNotIn(sentinel, summary)


class TraceProxyTests(unittest.TestCase):
    def test_proxy_forwards_sse_and_writes_only_sanitized_summary(self):
        response_body = (
            b'data: {"type":"response.output_item.done","item":{"type":"function_call",'
            b'"name":"read_file","call_id":"private-id","arguments":"private-args"}}\n\n'
            b'data: {"type":"response.completed","response":{"status":"completed",'
            b'"output":[{"type":"message","content":[{"type":"output_text",'
            b'"text":"private response"}]}]}}\n\n'
        )

        class UpstreamHandler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)

            def do_GET(self):
                body = b'{"ok":true}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
        upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
        upstream_thread.start()
        with tempfile.TemporaryDirectory() as directory:
            capture_path = str(Path(directory) / "summary.json")
            proxy = trace_codex_herd.TraceServer(
                0, f"http://127.0.0.1:{upstream.server_port}", capture_path
            )
            proxy_thread = threading.Thread(target=proxy.serve_forever, daemon=True)
            proxy_thread.start()
            try:
                url = f"http://127.0.0.1:{proxy.server_port}/v1/responses"
                request_body = json.dumps({
                    "input": [
                        {"type": "message", "content": "private prompt"},
                        {"type": "additional_tools", "role": "developer", "tools": [
                            {"type": "function", "name": "exec_command", "parameters": {"secret": "private schema"}}
                        ]},
                    ],
                }).encode()
                request = Request(url, data=request_body, headers={"Content-Type": "application/json"})
                with urlopen(request, timeout=3) as response:
                    self.assertEqual(response.read(), response_body)
                capture = json.loads(Path(capture_path).read_text())
                summary = json.dumps(capture)
                self.assertEqual(capture["requests"][0]["request"]["tool_names"], ["exec_command"])
                self.assertTrue(capture["requests"][0]["request"]["additional_tools_present"])
                self.assertEqual(capture["requests"][0]["response_items"][0]["name"], "read_file")
                for sentinel in ("private prompt", "private schema", "private-args", "private response", "private-id"):
                    self.assertNotIn(sentinel, summary)
            finally:
                proxy.shutdown()
                proxy.server_close()
        upstream.shutdown()
        upstream.server_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
