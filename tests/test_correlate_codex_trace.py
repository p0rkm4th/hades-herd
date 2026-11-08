import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from benchmarks.fixtures import correlate_codex_trace as correlate


def req(sequence, start, finish, tool_count, calls, output_types):
    return {
        "method": "POST",
        "path": "/v1/responses",
        "request_sequence": sequence,
        "request_started_monotonic_ns": start,
        "response_finished_monotonic_ns": finish,
        "request": {
            "tools_field_present": True,
            "top_level_tool_count": tool_count,
            "additional_tool_count": 0,
            "prior_function_call_names": ["exec_command"] * calls,
            "tool_result_count": calls,
        },
        "response_items": [{"type": item, "name": "exec_command"} for item in output_types],
    }


class CorrelateCodexTraceTests(unittest.TestCase):
    def test_correlates_ordered_tool_names_without_retaining_call_ids(self):
        first = req(1, 100, 200, 9, 0, ["function_call", "function_call"])
        first["response_items"] = [
            {"type": "function_call", "name": "exec_command", "call_id_present": True},
            {"type": "function_call", "name": "read", "call_id_present": True},
        ]
        second = req(2, 220, 300, 9, 2, ["message"])
        second["request"]["prior_function_call_names"] = ["exec_command", "read"]
        second["request"]["tool_result_count"] = 2
        ollama = [{
            "id": "PRIVATE_CALL_ID",
            "started_monotonic_ns": 120,
            "finished_monotonic_ns": 180,
            "status_code": 200,
            "request": {
                "endpoint": "/api/chat", "tools_field_present": True,
                "tool_names": ["exec_command", "read"],
            },
            "response": {"tool_call_names": ["exec_command", "read"]},
        }]

        result = correlate.correlate_tool_names([first, second], ollama)

        self.assertEqual(result["requests"][0]["codex_response_tool_names"], ["exec_command", "read"])
        self.assertEqual(result["requests"][0]["ollama_response_tool_names"], ["exec_command", "read"])
        self.assertTrue(result["requests"][0]["ordered_names_match"])
        self.assertTrue(result["requests"][0]["next_request_names_end_with_response_calls"])
        self.assertEqual(result["requests"][0]["next_request_prior_tool_result_count"], 2)
        self.assertNotIn("PRIVATE_CALL_ID", json.dumps(result))

    def test_overlapping_codex_requests_leave_backend_record_unassigned(self):
        requests = [req(1, 100, 250, 9, 0, ["function_call"]),
                    req(2, 180, 300, 9, 0, ["message"])]
        ollama = [{
            "started_monotonic_ns": 200,
            "finished_monotonic_ns": 210,
            "status_code": 200,
            "request": {"endpoint": "/api/chat"},
            "response": {"tool_call_names": ["exec_command"]},
        }]

        result = correlate.correlate_tool_names(requests, ollama)

        self.assertEqual(result["unassigned_ollama_chat_records"], 1)
        self.assertEqual([row["backend_observation"] for row in result["requests"]], ["missing", "missing"])

    def test_failed_ollama_request_does_not_claim_tool_names_match(self):
        request = req(1, 100, 200, 9, 0, ["message"])
        request["response_items"] = [{"type": "message"}]
        ollama = [{
            "started_monotonic_ns": 120,
            "finished_monotonic_ns": 180,
            "status_code": 502,
            "request": {"endpoint": "/api/chat"},
            "error_type": "ConnectionError",
        }]

        row = correlate.correlate_tool_names([request], ollama)["requests"][0]

        self.assertEqual(row["backend_observation"], "failed")
        self.assertIsNone(row["ordered_names_match"])
        self.assertEqual(row["successful_ollama_response_count"], 0)

    def test_reports_model_tool_call_absent_from_backend_offer(self):
        request = req(1, 100, 200, 9, 0, ["function_call"])
        request["response_items"] = [{"type": "function_call", "name": "read"}]
        ollama = [{
            "started_monotonic_ns": 120,
            "finished_monotonic_ns": 180,
            "status_code": 200,
            "request": {
                "endpoint": "/api/chat", "tools_field_present": True,
                "tool_names": ["exec_command"],
            },
            "response": {"tool_call_names": ["read"]},
        }]

        row = correlate.correlate_tool_names([request], ollama)["requests"][0]

        self.assertEqual(row["codex_response_tool_names"], ["read"])
        self.assertEqual(row["unadvertised_ollama_tool_names"], ["read"])
        self.assertTrue(row["ordered_names_match"])

    def test_cli_accepts_ollama_summary_and_emits_ordered_name_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path = root / "codex.json"
            events_path = root / "events.jsonl"
            ollama_path = root / "ollama.jsonl"
            codex_path.write_text(json.dumps({"requests": [{
                "method": "POST", "path": "/v1/responses", "request_sequence": 1,
                "request_started_monotonic_ns": 10, "response_finished_monotonic_ns": 50,
                "request": {},
                "response_items": [{"type": "function_call", "name": "exec_command"}],
            }]}))
            events_path.write_text("")
            ollama_path.write_text(json.dumps({
                "method": "POST",
                "started_monotonic_ns": 20, "finished_monotonic_ns": 40,
                "status_code": 200,
                "request": {
                    "endpoint": "/api/chat", "tools_field_present": True,
                    "tool_names": ["exec_command"],
                },
                "response": {"tool_call_names": ["exec_command"]},
            }) + "\n")

            completed = subprocess.run(
                [sys.executable, str(Path(correlate.__file__)), str(codex_path),
                 str(events_path), "--ollama-summary", str(ollama_path)],
                capture_output=True, text=True, timeout=5, check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        row = result["tool_name_correlation"]["requests"][0]
        self.assertTrue(row["ordered_names_match"])
        self.assertEqual(row["ollama_response_tool_names"], ["exec_command"])

    def test_counts_command_events_in_nonoverlapping_gaps(self):
        requests = [req(2, 200, 250, 0, 1, ["function_call"]), req(1, 100, 150, 9, 0, ["function_call"])]
        events = [
            {"monotonic_ns": 175, "type": "item.started", "item_type": "command_execution", "item_status": "in_progress"},
            {"monotonic_ns": 190, "type": "item.completed", "item_type": "command_execution", "item_status": "completed"},
            {"monotonic_ns": 260, "type": "item.started", "item_type": "command_execution", "item_status": "in_progress"},
            {"monotonic_ns": 270, "type": "item.completed", "item_type": "command_execution", "item_status": "failed"},
        ]
        output = correlate.correlate(requests, events)
        first, second = output["requests"]
        self.assertEqual(first["request_sequence"], 1)
        self.assertEqual(first["command_starts_in_gap"], 1)
        self.assertEqual(first["command_completions_in_gap"], 1)
        self.assertEqual(second["request_sequence"], 2)
        self.assertEqual(second["command_failures_in_gap"], 1)
        self.assertEqual(second["response_function_call_count"], 1)

    def test_overlapping_responses_are_not_given_false_event_attribution(self):
        requests = [req(1, 100, 250, 9, 0, ["function_call"]), req(2, 200, 300, 0, 1, ["function_call"])]
        events = [{"monotonic_ns": 275, "type": "item.started", "item_type": "command_execution"}]
        output = correlate.correlate(requests, events)
        self.assertTrue(output["requests"][0]["next_request_started_before_response_finished"])
        self.assertIsNone(output["requests"][0]["command_starts_in_gap"])
        self.assertEqual(output["overlapping_request_gaps_unassigned"], 1)
        self.assertEqual(output["command_event_summary"]["total"]["started"], 1)
        self.assertEqual(output["command_event_summary"]["unassigned"]["started"], 1)

    def test_reports_command_events_before_first_window_as_unassigned(self):
        requests = [req(1, 100, 150, 9, 0, ["function_call"])]
        events = [
            {"monotonic_ns": 90, "type": "item.started", "item_type": "command_execution"},
            {
                "monotonic_ns": 175, "type": "item.completed",
                "item_type": "command_execution", "item_status": "completed",
            },
            {
                "monotonic_ns": 260, "type": "item.completed",
                "item_type": "command_execution", "item_status": "failed",
            },
        ]
        summary = correlate.correlate(requests, events)["command_event_summary"]
        self.assertEqual(summary["total"], {
            "started": 1, "completed": 2, "completed_successfully": 1,
            "completed_failed": 1, "completed_other": 0,
        })
        self.assertEqual(summary["assigned_to_nonoverlapping_gaps"], {
            "started": 0, "completed": 2, "completed_successfully": 1,
            "completed_failed": 1, "completed_other": 0,
        })
        self.assertEqual(summary["unassigned"], {
            "started": 1, "completed": 0, "completed_successfully": 0,
            "completed_failed": 0, "completed_other": 0,
        })

    def test_loaders_reject_old_unstamped_traces(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.json"
            path.write_text(json.dumps({"requests": [{"method": "POST", "path": "/v1/responses", "request": {}}]}))
            with self.assertRaisesRegex(correlate.TraceError, "sequence/start/finish"):
                correlate.load_summary(path)

    def test_loader_ignores_unstamped_discovery_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.json"
            path.write_text(json.dumps({"requests": [
                {"method": "GET", "path": "/api/tags"},
                req(1, 100, 200, 0, 0, ["message"]),
            ]}))
            self.assertEqual([item["request_sequence"] for item in correlate.load_summary(path)], [1])


if __name__ == "__main__":
    unittest.main()
