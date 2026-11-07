#!/usr/bin/env python3
"""Loopback-only deterministic Codex Responses tool-router diagnostic."""
import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

MODEL = "mock-codex:latest"

class Handler(BaseHTTPRequestHandler):
    calls = 0
    def log_message(self, *_args): pass
    def send_json(self, status, value):
        body = json.dumps(value).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    @staticmethod
    def event(name, seq, **fields):
        return f"event: {name}\ndata: {json.dumps({'type': name, 'sequence_number': seq, **fields}, separators=(',', ':'))}\n\n"
    def stream(self, events):
        body = "".join(events).encode()
        self.send_response(200); self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(body))); self.end_headers()
        self.wfile.write(body); self.wfile.flush()
    def do_GET(self):
        if self.path == "/api/tags":
            self.send_json(200, {"models": [{"model": MODEL, "name": MODEL, "digest": "d"*64,
                "size": 1000, "details": {"family": "mock", "fleet_nodes": ["mock-node"]},
                "capabilities": ["tools"]}]})
        elif self.path == "/fleet/status":
            self.send_json(200, {"nodes": [{"node_id": "mock-node", "status": "online",
                "ollama_url": f"http://127.0.0.1:{self.server.server_port}",
                "ollama": {"models_loaded": []}}], "queues": []})
        else: self.send_json(404, {"error": "not found"})
    def do_POST(self):
        data = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if self.path == "/api/show":
            self.send_json(200, {"model_info": {"mock.context_length": 4096}, "parameters": ""}); return
        if self.path != "/v1/responses":
            self.send_json(404, {"error": "not found"}); return
        req = json.loads(data); Handler.calls += 1
        names = sorted(x["name"] for x in req.get("tools", []) if x.get("name"))
        self.server.capture["requests"].append({
            "request_number": Handler.calls, "tool_names": names,
            "read_file_advertised": "read_file" in names,
            "reasoning_effort": req.get("reasoning", {}).get("effort")
                if isinstance(req.get("reasoning"), dict) else None,
            "think_field_present": "think" in req,
            "rejected_call_result_present": any(
                x.get("type") == "function_call_output" and x.get("call_id") == "call_1"
                for x in req.get("input", []) if isinstance(x, dict)),
            "result_mentions_unsupported": any(
                x.get("type") == "function_call_output" and x.get("call_id") == "call_1"
                and "unsupported" in str(x.get("output", "")).lower()
                for x in req.get("input", []) if isinstance(x, dict)),
        })
        self.server.capture_path.write_text(json.dumps(self.server.capture, indent=2) + "\n")
        now = int(time.time()); rid = f"resp_{Handler.calls}"
        if Handler.calls == 1:
            args = '{"path":"README.md"}'
            item = {"id": "fc_1", "type": "function_call", "status": "completed",
                "call_id": "call_1", "name": "read_file", "arguments": args}
            output = [item]
            events = [
                self.event("response.created", 0, response={"id": rid, "object": "response", "status": "in_progress", "created_at": now, "model": MODEL, "output": []}),
                self.event("response.output_item.added", 1, output_index=0, item={**item, "status": "in_progress", "arguments": ""}),
                self.event("response.function_call_arguments.delta", 2, output_index=0, item_id="fc_1", delta=args),
                self.event("response.function_call_arguments.done", 3, output_index=0, item_id="fc_1", arguments=args),
                self.event("response.output_item.done", 4, output_index=0, item=item),
            ]
        else:
            text = "Diagnostic complete."
            item = {"id": "msg_2", "type": "message", "status": "completed", "role": "assistant",
                "content": [{"type": "output_text", "text": text, "annotations": []}]}
            output = [item]
            events = [
                self.event("response.created", 0, response={"id": rid, "object": "response", "status": "in_progress", "created_at": now, "model": MODEL, "output": []}),
                self.event("response.output_item.added", 1, output_index=0, item={**item, "status": "in_progress", "content": []}),
                self.event("response.content_part.added", 2, output_index=0, item_id="msg_2", content_index=0, part={"type": "output_text", "text": ""}),
                self.event("response.output_text.delta", 3, output_index=0, item_id="msg_2", content_index=0, delta=text),
                self.event("response.output_text.done", 4, output_index=0, item_id="msg_2", content_index=0, text=text),
                self.event("response.output_item.done", 5, output_index=0, item=item),
            ]
        response = {"id": rid, "object": "response", "status": "completed", "created_at": now,
            "model": MODEL, "output": output, "error": None}
        events.append(self.event("response.completed", len(events), response=response))
        self.stream(events)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--capture", type=Path, default=Path("/tmp/codex-tool-router-capture.json"))
    args = p.parse_args()
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    server.capture_path = args.capture; server.capture = {"requests": []}
    print(f"Loopback mock Herd: http://127.0.0.1:{server.server_port}", flush=True)
    print(f"Sanitized request summary: {server.capture_path}", flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__ == "__main__": main()
