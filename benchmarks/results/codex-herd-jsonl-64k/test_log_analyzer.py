"""Unit tests for log_analyzer."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

import log_analyzer

VALID_LEVELS = ("INFO", "WARNING", "ERROR")


def valid_record(service="api", level="INFO", message="ok", timestamp="2024-01-01T00:00:00Z"):
    """Build a valid JSON log record."""
    return {
        "timestamp": timestamp,
        "service": service,
        "level": level,
        "message": message,
    }


class TempFileTestCase(unittest.TestCase):
    """Helpers that create a temporary JSONL file and analyze it."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = os.path.join(self.temp_dir.name, "logs.jsonl")

    def write_records(self, records, blank_lines=0):
        """Write records to the temp file and return the file path."""
        with open(self.path, "w", encoding="utf-8") as handle:
            for _ in range(blank_lines):
                handle.write("\n")
            for record in records:
                handle.write(json.dumps(record) + "\n")
        return self.path

    def analyze(self, records=None, blank_lines=0):
        """Analyze the temp file and return the summary."""
        return log_analyzer.analyze_jsonl(self.path)

    def run_cli(self, path, args=None):
        """Run the CLI in a subprocess and return its result."""
        command = [sys.executable, "-m", "log_analyzer"]
        if args is None:
            args = [path]
        command.extend(args)
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
            env={**os.environ, "PYTHONPATH": os.path.dirname(__file__)},
        )

class AnalyzerTests(TempFileTestCase):
    """Core counting behavior."""

    def test_correct_counts_for_six_valid_records(self):
        records = [
            valid_record(service="api", level="INFO", message="ok"),
            valid_record(service="api", level="INFO", message="ok"),
            valid_record(service="database", level="WARNING", message="slow"),
            valid_record(service="database", level="ERROR", message="e1"),
            valid_record(service="database", level="ERROR", message="e2"),
            valid_record(service="web", level="ERROR", message="e3"),
        ]
        self.write_records(records)
        summary = self.analyze(records)
        self.assertEqual(summary, {
            "total": 6,
            "levels": {"ERROR": 3, "INFO": 2, "WARNING": 1},
            "errors_by_service": {"database": 2, "web": 1},
            "skipped": 0,
        })

    def test_all_three_severity_keys_always_present(self):
        records = [valid_record(service="api", level="INFO", message="ok")]
        self.write_records(records)
        summary = self.analyze(records)
        self.assertEqual(summary["levels"], {"ERROR": 0, "INFO": 1, "WARNING": 0})
        self.assertEqual(summary["errors_by_service"], {})

    def test_case_insensitive_severity(self):
        records = [
            valid_record(service="api", level="info", message="ok"),
            valid_record(service="api", level="Info", message="ok"),
            valid_record(service="database", level="warning", message="slow"),
            valid_record(service="database", level="error", message="e1"),
            valid_record(service="database", level="error", message="e2"),
            valid_record(service="web", level="error", message="e3"),
        ]
        self.write_records(records)
        summary = self.analyze(records)
        self.assertEqual(summary["levels"], {"ERROR": 3, "INFO": 2, "WARNING": 1})
        self.assertEqual(summary["errors_by_service"], {"database": 2, "web": 1})

    def test_invalid_timestamps_are_skipped(self):
        records = [
            valid_record(),
            {"timestamp": "2024-01-01", "service": "api", "level": "INFO", "message": "bad date"},
            {"timestamp": "2024-01-01T00:00:00", "service": "api", "level": "INFO", "message": "no timezone"},
            {"timestamp": "not-a-date", "service": "api", "level": "INFO", "message": "bad"},
            {"timestamp": 12345, "service": "api", "level": "INFO", "message": "non-string"},
            {"timestamp": "2024-01-01T00:00:60Z", "service": "api", "level": "INFO", "message": "bad time"},
        ]
        self.write_records(records)
        summary = self.analyze(records)
        self.assertEqual(summary["levels"], {"ERROR": 0, "INFO": 1, "WARNING": 0})
        self.assertEqual(summary["errors_by_service"], {})
        self.assertEqual(summary["skipped"], 5)

    def test_malformed_json_is_skipped(self):
        records = [
            valid_record(),
            '{"timestamp": "2024-01-01T00:00:00Z", "service": "api", "level": "INFO", "message": "broken"',
            '{"timestamp": "2024-01-01T00:00:00Z", "service": "api", "level": "INFO", "message": "broken"',
            '{"timestamp": "2024-01-01T00:00:00Z", "service": "api", "level": "INFO", "message": "broken"',
        ]
        self.write_records(records)
        summary = self.analyze(records)
        self.assertEqual(summary["levels"], {"ERROR": 0, "INFO": 1, "WARNING": 0})
        self.assertEqual(summary["errors_by_service"], {})
        self.assertEqual(summary["skipped"], 3)

    def test_missing_fields_are_skipped(self):
        records = [
            valid_record(),
            {"timestamp": "2024-01-01T00:00:00Z", "service": "api", "message": "missing level"},
            {"service": "api", "level": "INFO", "message": "missing timestamp"},
        ]
        self.write_records(records)
        summary = self.analyze(records)
        self.assertEqual(summary["levels"], {"ERROR": 0, "INFO": 1, "WARNING": 0})
        self.assertEqual(summary["errors_by_service"], {})
        self.assertEqual(summary["skipped"], 2)

    def test_unsupported_severity_is_skipped(self):
        records = [
            valid_record(),
            {"timestamp": "2024-01-01T00:00:00Z", "service": "api", "level": "DEBUG", "message": "debug"},
            {"timestamp": "2024-01-01T00:00:00Z", "service": "api", "level": "TRACE", "message": "trace"},
        ]
        self.write_records(records)
        summary = self.analyze(records)
        self.assertEqual(summary["levels"], {"ERROR": 0, "INFO": 1, "WARNING": 0})
        self.assertEqual(summary["errors_by_service"], {})
        self.assertEqual(summary["skipped"], 2)

    def test_wrong_field_types_are_skipped(self):
        records = [
            valid_record(),
            {"timestamp": "2024-01-01T00:00:00Z", "service": 42, "level": "INFO", "message": "bad service"},
            {"timestamp": "2024-01-01T00:00:00Z", "service": "api", "level": "INFO", "message": 42},
        ]
        self.write_records(records)
        summary = self.analyze(records)
        self.assertEqual(summary["levels"], {"ERROR": 0, "INFO": 1, "WARNING": 0})
        self.assertEqual(summary["errors_by_service"], {})
        self.assertEqual(summary["skipped"], 2)


class BlankLineTests(TempFileTestCase):
    """Empty files and blank-line handling."""

    def test_empty_file(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            pass
        summary = self.analyze([])
        self.assertEqual(summary, {
            "total": 0,
            "levels": {"ERROR": 0, "INFO": 0, "WARNING": 0},
            "errors_by_service": {},
            "skipped": 0,
        })

    def test_blank_lines_are_ignored(self):
        record = valid_record()
        with open(self.path, "w", encoding="utf-8") as handle:
            for _ in range(4):
                handle.write("\n")
            handle.write(json.dumps(record) + "\n")
        summary = self.analyze([record], blank_lines=4)
        self.assertEqual(summary["skipped"], 0)
        self.assertEqual(summary["total"], 1)

    def test_input_file_is_not_modified(self):
        records = [valid_record()]
        self.write_records(records)
        with open(self.path, "rb") as before_handle:
            before = before_handle.read()
        self.analyze(records)
        with open(self.path, "rb") as after_handle:
            after = after_handle.read()
        self.assertEqual(before, after)


class ErrorGroupingTests(TempFileTestCase):
    """ERROR grouping and alphabetical ordering."""

    def test_errors_grouped_by_service(self):
        records = [
            valid_record(service="database", level="ERROR", message="e1"),
            valid_record(service="web", level="ERROR", message="e2"),
            valid_record(service="database", level="ERROR", message="e3"),
        ]
        self.write_records(records)
        summary = self.analyze(records)
        self.assertEqual(summary["errors_by_service"], {"database": 2, "web": 1})

    def test_error_service_names_are_sorted(self):
        records = [
            valid_record(service="web", level="ERROR", message="e1"),
            valid_record(service="api", level="ERROR", message="e2"),
            valid_record(service="database", level="ERROR", message="e3"),
        ]
        self.write_records(records)
        summary = self.analyze(records)
        self.assertEqual(summary["errors_by_service"], {"api": 1, "database": 1, "web": 1})

    def test_non_error_levels_do_not_contribute_to_errors_by_service(self):
        records = [
            valid_record(service="api", level="INFO", message="ok"),
            valid_record(service="database", level="WARNING", message="slow"),
        ]
        self.write_records(records)
        summary = self.analyze(records)
        self.assertEqual(summary["errors_by_service"], {})
        self.assertEqual(summary["levels"], {"ERROR": 0, "INFO": 1, "WARNING": 1})


class InputFileErrorTests(TempFileTestCase):
    """Missing files, directories, and invalid UTF-8."""

    def test_missing_file_exits_nonzero(self):
        path = os.path.join(self.temp_dir.name, "missing.jsonl")
        result = self.run_cli(self.path, args=[path])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("error", result.stderr.lower())

    def test_missing_directory_exits_nonzero(self):
        path = os.path.join(self.temp_dir.name, "missing-dir", "logs.jsonl")
        result = self.run_cli(self.path, args=[path])
        self.assertNotEqual(result.returncode, 0)

    def test_invalid_utf8_exits_nonzero(self):
        path = os.path.join(self.temp_dir.name, "invalid.jsonl")
        with open(path, "wb") as handle:
            handle.write(
                b'{"timestamp": "2024-01-01T00:00:00Z", "service": "api", "level": "INFO", "message": "\xff\xfe"}\n'
            )
        result = self.run_cli(self.path, args=[path])
        self.assertNotEqual(result.returncode, 0)


class CliTests(TempFileTestCase):
    """CLI JSON output and exit codes."""

    def test_cli_prints_json_summary(self):
        records = [
            valid_record(service="api", level="INFO", message="ok"),
            valid_record(service="api", level="INFO", message="ok"),
            valid_record(service="database", level="WARNING", message="slow"),
            valid_record(service="database", level="ERROR", message="e1"),
            valid_record(service="database", level="ERROR", message="e2"),
            valid_record(service="web", level="ERROR", message="e3"),
        ]
        self.write_records(records)
        result = self.run_cli(self.path)
        self.assertEqual(result.returncode, 0)
        summary = json.loads(result.stdout)
        self.assertEqual(summary, {
            "total": 6,
            "levels": {"ERROR": 3, "INFO": 2, "WARNING": 1},
            "errors_by_service": {"database": 2, "web": 1},
            "skipped": 0,
        })

    def test_cli_usage_error_exits_nonzero(self):
        result = self.run_cli([], args=[])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", result.stderr)


if __name__ == "__main__":
    unittest.main()
