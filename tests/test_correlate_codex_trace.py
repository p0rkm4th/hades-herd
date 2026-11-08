import json
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
