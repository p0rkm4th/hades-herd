import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import codex_herd


def candidate(name="local-model", online=True):
    return {
        "name": name,
        "embedding_only": False,
        "tool_capable": True,
        "online_nodes": ["local-node"] if online else [],
    }


class RoleMappingTests(unittest.TestCase):
    def test_unconfigured_role_has_actionable_no_fallback_error(self):
        with self.assertRaisesRegex(codex_herd.HerdError, "No hosted fallback"):
            codex_herd.resolve_role("complex", {})

    def test_role_names_are_case_insensitive(self):
        self.assertEqual(codex_herd.resolve_role("FAST", {"roles": {"fast": "m"}}), "m")

    def test_unknown_role_is_rejected(self):
        with self.assertRaisesRegex(codex_herd.HerdError, "fast, balanced, complex"):
            codex_herd.resolve_role("creative", {})

    def test_assignment_persists_without_changing_saved_default(self):
        with tempfile.TemporaryDirectory() as directory:
            prefs_path = Path(directory) / "preferences.json"
            prefs = {"default_model": "existing-default", "models": {}}
            with mock.patch.object(codex_herd, "PREFS", prefs_path):
                codex_herd.assign_role("balanced", "local-model", {"local-model": candidate()}, prefs)
            saved = json.loads(prefs_path.read_text())
            self.assertEqual(saved["roles"], {"balanced": "local-model"})
            self.assertEqual(saved["default_model"], "existing-default")

    def test_offline_model_cannot_be_assigned(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(codex_herd, "PREFS", Path(directory) / "preferences.json"):
                with self.assertRaisesRegex(codex_herd.HerdError, "unavailable"):
                    codex_herd.assign_role("fast", "local-model", {"local-model": candidate(online=False)}, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
