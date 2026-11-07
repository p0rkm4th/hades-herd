import json
import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import codex_herd


class HerdEndpointConfigTests(unittest.TestCase):
    def test_ollama_thinking_controls_require_advertised_values(self):
        self.assertEqual(
            codex_herd.ollama_thinking_controls({
                "thinking": {"values": [False, "low", "high"], "default": "low"},
            }),
            {"values": [False, "low", "high"], "default": "low"},
        )
        self.assertEqual(
            codex_herd.ollama_thinking_controls({
                "thinking": {"values": [False, True], "default": True},
            }),
            {"values": [False, True], "default": True},
        )

    def test_ollama_thinking_controls_reject_missing_or_invalid_metadata(self):
        for shown in (
            {},
            {"thinking": {"values": []}},
            {"thinking": {"values": [1], "default": 1}},
            {"thinking": {"values": ["low"], "default": "high"}},
        ):
            with self.subTest(shown=shown):
                self.assertIsNone(codex_herd.ollama_thinking_controls(shown))

    def test_digest_evidence_is_local_and_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "model-digests.json"
            with mock.patch.object(codex_herd, "DIGEST_EVIDENCE", evidence):
                self.assertEqual(codex_herd.read_digest_evidence(), ({}, {}))
                evidence.write_text(json.dumps({
                    "verified_tool_digests": {"model": "A" * 64},
                    "inconsistent_tool_digests": {},
                }))
                self.assertEqual(
                    codex_herd.read_digest_evidence(),
                    ({"model": "a" * 64}, {}),
                )
                evidence.write_text('{"verified_tool_digests":{"model":"not-a-digest"}}')
                with self.assertRaisesRegex(codex_herd.HerdError, "64-character"):
                    codex_herd.read_digest_evidence()

    def test_first_run_has_no_deployment_specific_default(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(codex_herd, "PREFS", Path(directory) / "preferences.json"):
                self.assertIsNone(codex_herd.read_prefs()["default_model"])

    def test_default_is_loopback_and_has_no_private_network_dependency(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(codex_herd.herd_base_url(), "http://127.0.0.1:11435")

    def test_explicit_endpoint_is_normalized(self):
        with mock.patch.dict(os.environ, {"CODEX_HERD_URL": "https://herd.example.test:11435/"}, clear=True):
            self.assertEqual(codex_herd.herd_base_url(), "https://herd.example.test:11435")

    def test_rejects_credentials_and_non_http_urls(self):
        for value in ("ftp://herd.example.test", "http://user:password@herd.example.test", "", "http://herd.example.test?token=x"):
            with self.subTest(value=value), mock.patch.dict(os.environ, {"CODEX_HERD_URL": value}, clear=True):
                with self.assertRaises(codex_herd.HerdError):
                    codex_herd.herd_base_url()


if __name__ == "__main__":
    unittest.main(verbosity=2)
