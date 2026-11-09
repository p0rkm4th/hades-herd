"""Unit tests for log_analyzer.py."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

import log_analyzer
from log_analyzer import analyze_file, main

VALID = [
    {"timestamp": "2024-01-01T00:00:00Z", "service": "api", "level": "INFO", "message": "ok"},
    {"timestamp": "2024-01-01T00:00:01Z", "service": "api", "level": "INFO", "message": "ok"},
    {"timestamp": "2024-01-01T00:00:02+02:00", "service": "database", "level": "WARNING", "message": "warn"},
    {"timestamp": "2024-01-01T00:00:03Z", "service": "database", "level": "ERROR", "message": "err"},
    {"timestamp": "2024-01-01T00:00:04Z", "service": "database", "level": "ERROR", "message": "err"},
    {"timestamp": "2024-01-01T00:00:05-05:00", "service": "web", "level": "error", "message": "lowercase"},
]


class AnalyzerTests(unittest.TestCase):
    """Core counting behaviour."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "log.jsonl")

    def write(self, lines):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines))

    def run_analysis(self):
        return analyze_file(self.path)

    def test_example_output_counts(self):
        self.write([json.dumps(rec) for rec in VALID])
        total, levels, errors_by_service, skipped = self.run_analysis()
        self.assertEqual(
            (total, levels, errors_by_service, skipped),
            (6, {"INFO": 2, "WARNING": 1, "ERROR": 3}, {"database": 2, "web": 1}, 0),
        )

    def test_lowercase_levels_are_normalized(self):
        self.write(
            [
                json.dumps({"timestamp": "2024-01-01T00:00:00Z", "service": "a", "level": "info", "message": "x"}),
                json.dumps({"timestamp": "2024-01-01T00:00:00Z", "service": "b", "level": "warning", "message": "x"}),
                json.dumps({"timestamp": "2024-01-01T00:00:00Z", "service": "c", "level": "error", "message": "x"}),
            ]
        )
        total, levels, _, skipped = self.run_analysis()
        self.assertEqual(levels, {"INFO": 1, "WARNING": 1, "ERROR": 1})
        self.assertEqual(total, 3)

    def test_error_counts_grouped_and_sorted(self):
        records = [
            {"timestamp": "2024-01-01T00:00:00Z", "service": "zeta", "level": "ERROR", "message": "x"},
            {"timestamp": "2024-01-01T00:00:00Z", "service": "alpha", "level": "ERROR", "message": "x"},
            {"timestamp": "2024-01-01T00:00:00Z", "service": "mid", "level": "ERROR", "message": "x"},
        ]
        self.write([json.dumps(rec) for rec in records])
        _, _, errors_by_service, _ = self.run_analysis()
        self.assertEqual(errors_by_service, {"alpha": 1, "mid": 1, "zeta": 1})

    def test_invalid_records_are_skipped(self):
        bad = [
            json.dumps({"timestamp": "not-a-date", "service": "a", "level": "INFO", "message": "x"}),
            json.dumps({"service": "a", "level": "INFO", "message": "x"}),
            json.dumps({"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "x"}),
            json.dumps({"timestamp": "2024-01-01T00:00:00Z", "service": "a", "message": "x"}),
            json.dumps({"timestamp": "2024-01-01T00:00:00Z", "service": "a", "level": "DEBUG", "message": "x"}),
            json.dumps({"timestamp": "2024-01-01T00:00:00Z", "service": "a", "level": "INFO", "message": 7}),
            json.dumps({"timestamp": "2024-01-01T00:00:00Z", "service": "a", "level": "INFO", "message": None}),
            json.dumps({"timestamp": "2024-01-01T00:00:00Z", "service": "a", "level": "INFO"}),
        ]
        self.write(bad)
        total, _, _, skipped = self.run_analysis()
        self.assertEqual((total, skipped), (0, len(bad)))

    def test_bad_json_is_skipped(self):
        self.write(["not json", json.dumps(VALID[0])])
        total, _, _, skipped = self.run_analysis()
        self.assertEqual((total, skipped), (1, 1))

    def test_empty_file(self):
        self.write([])
        total, levels, _, skipped = self.run_analysis()
        self.assertEqual(total, 0)
        self.assertEqual(levels, {"INFO": 0, "WARNING": 0, "ERROR": 0})
        self.assertEqual(skipped, 0)

    def test_blank_lines_are_ignored(self):
        self.write(["", " ", json.dumps(VALID[0]), "\t", json.dumps(VALID[1])])
        total, _, _, skipped = self.run_analysis()
        self.assertEqual((total, skipped), (2, 0))

    def test_invalid_timezones_are_rejected(self):
        bad = [
            "2024-01-01T00:00:00+25:00",
            "2024-01-01T00:00:00+90",
            "2024-01-01T00:00:00Z1",
            "2024-01-01T00:00:00",
            "2024-01-01T25:00:00Z",
            "2024-01-01T00:60:00Z",
            "2024-01-01 00:00:00Z",
        ]
        for stamp in bad:
            with self.subTest(timestamp=stamp):
                self.write([json.dumps({"timestamp": stamp, "service": "a", "level": "INFO", "message": "x"})])
                total, _, _, skipped = self.run_analysis()
                self.assertEqual((total, skipped), (0, 1))


class CliTests(unittest.TestCase):
    """CLI entry point, stdout shape, and input-file immutability."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "log.jsonl")
        self.before = None

    def write(self, lines):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines))
        with open(self.path, "rb") as handle:
            self.before = handle.read()

    def run_cli(self, args):
        return subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "log_analyzer.py")]
            + args,
            capture_output=True,
            text=True,
        )

    def read_back(self):
        from pathlib import Path

        return Path(self.path).read_bytes()

    def test_cli_emits_json(self):
        self.write([json.dumps(rec) for rec in VALID])
        result = self.run_cli([self.path])
        self.assertEqual(result.returncode, 0)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["total"], 6)
        self.assertEqual(parsed["levels"], {"INFO": 2, "WARNING": 1, "ERROR": 3})
        self.assertEqual(parsed["errors_by_service"], {"database": 2, "web": 1})
        self.assertEqual(parsed["skipped"], 0)

    def test_cli_output_keys(self):
        self.write([json.dumps(rec) for rec in VALID])
        result = self.run_cli([self.path])
        parsed = json.loads(result.stdout)
        self.assertEqual(sorted(parsed), ["errors_by_service", "levels", "skipped", "total"])

    def test_cli_missing_file(self):
        result = self.run_cli([os.path.join(self.tmp.name, "nope.jsonl")])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("nope.jsonl", result.stderr)

    def test_cli_invalid_utf8(self):
        with open(self.path, "wb") as handle:
            handle.write(b'{"timestamp": "2024-01-01T00:00:00Z", "service": "a", "level": "INFO", "message": "\xff\xfe"}')
        result = self.run_cli([self.path])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not valid UTF-8", result.stderr)

    def test_cli_input_file_unmodified(self):
        self.write([json.dumps(rec) for rec in VALID])
        result = self.run_cli([self.path])
        self.assertEqual(self.read_back(), self.before)
        self.assertEqual(result.returncode, 0)

    def test_cli_usage(self):
        result = self.run_cli([])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)