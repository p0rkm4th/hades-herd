import io
import json
import re
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import codex_herd


def model(name):
    return {
        "name": name,
        "embedding_only": False,
        "tool_capable": True,
        "capabilities": ["tools"],
        "loaded": [],
        "online_nodes": ["test-node"],
        "model_context_window": 131072,
        "model_parameters": {},
    }


def models():
    return {"available-model": model("available-model")}


def read_profile(path):
    """Read the generated string field without requiring Python 3.11 tomllib."""
    text = path.read_text()
    match = re.search(r'^developer_instructions\s*=\s*(".*")$', text, re.MULTILINE)
    return {"developer_instructions": json.loads(match.group(1))} if match else {}


class SyncCatalogDefaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        codex_herd.CODEX_HOME = root / "codex-home"
        codex_herd.CATALOG = root / "catalog.json"
        codex_herd.PROFILE = root / "herd.config.toml"
        codex_herd.INVENTORY = root / "inventory.json"
        codex_herd.PREFS = root / "preferences.json"
        codex_herd.CODEX_HOME.mkdir()
        self.old = {
            codex_herd.CATALOG: b"old catalog\n",
            codex_herd.PROFILE: b"old profile\n",
            codex_herd.INVENTORY: b"old inventory\n",
        }
        for path, data in self.old.items():
            path.write_bytes(data)

    def tearDown(self):
        self.temp.cleanup()

    def test_removed_saved_default_is_reported_without_overwriting_profile(self):
        prefs = {"default_model": "removed-model", "models": {}}
        with self.assertRaisesRegex(
            codex_herd.HerdError,
            "Saved default_model 'removed-model' is no longer selectable",
        ) as ctx:
            codex_herd.sync_catalog(models(), prefs)
        self.assertIn("available-model", str(ctx.exception))
        self.assertIn("codex-herd config <live-model>", str(ctx.exception))
        for path, data in self.old.items():
            self.assertEqual(path.read_bytes(), data, str(path))
        self.assertEqual(
            prefs,
            {"default_model": "removed-model", "models": {}},
            "preferences were mutated",
        )

    def test_explicit_model_can_be_used_despite_removed_saved_default(self):
        prefs = {"default_model": "removed-model", "models": {}}
        codex_herd.sync_catalog(models(), prefs, "available-model")
        self.assertIn('model = "available-model"', codex_herd.PROFILE.read_text())

    def test_initial_catalog_without_saved_default_uses_first_available_model(self):
        prefs = {"models": {}}
        codex_herd.sync_catalog(models(), prefs)
        self.assertIn('model = "available-model"', codex_herd.PROFILE.read_text())

    def test_model_guidance_is_toml_encoded_and_follows_explicit_session_model(self):
        fleet_models = models()
        fleet_models["second-model"] = model("second-model")
        prefs = {
            "default_model": "available-model",
            "models": {
                "available-model": {"developer_instructions": 'Use `exec_command`; say "done". ☃'},
                "second-model": {"developer_instructions": "Inspect once, then implement."},
            },
        }

        codex_herd.sync_catalog(fleet_models, prefs)
        config = read_profile(codex_herd.PROFILE)
        self.assertEqual(config["developer_instructions"], 'Use `exec_command`; say "done". ☃')

        codex_herd.sync_catalog(fleet_models, prefs, "second-model")
        config = read_profile(codex_herd.PROFILE)
        self.assertEqual(config["developer_instructions"], "Inspect once, then implement.")
        self.assertEqual(prefs["default_model"], "available-model")

    def test_guidance_is_omitted_when_unset_and_invalid_value_preserves_generated_files(self):
        prefs = {"default_model": "available-model", "models": {}}
        codex_herd.sync_catalog(models(), prefs)
        config = read_profile(codex_herd.PROFILE)
        self.assertNotIn("developer_instructions", config)

        generated = {
            path: path.read_bytes()
            for path in (codex_herd.CATALOG, codex_herd.PROFILE, codex_herd.INVENTORY)
        }
        prefs["models"]["available-model"] = {"developer_instructions": ["wrong type"]}
        with self.assertRaisesRegex(codex_herd.HerdError, "must be text"):
            codex_herd.sync_catalog(models(), prefs)
        for path, content in generated.items():
            self.assertEqual(path.read_bytes(), content, str(path))

    def test_interactive_guidance_persists_and_can_be_cleared(self):
        class TerminalInput(io.StringIO):
            def isatty(self):
                return True

        prefs = {"default_model": "available-model", "models": {}}
        inputs = TerminalInput("\n\nUse only exec_command; implement and verify.\n\nn\n")
        with mock.patch.object(codex_herd.sys, "stdin", inputs):
            codex_herd.configure("available-model", models(), prefs)

        self.assertEqual(
            codex_herd.read_prefs()["models"]["available-model"]["developer_instructions"],
            "Use only exec_command; implement and verify.",
        )
        saved = read_profile(codex_herd.PROFILE)
        self.assertEqual(
            saved["developer_instructions"],
            "Use only exec_command; implement and verify.",
        )

        inputs = TerminalInput("\n\n!clear\n\nn\n")
        with mock.patch.object(codex_herd.sys, "stdin", inputs):
            codex_herd.configure("available-model", models(), prefs)
        self.assertNotIn("developer_instructions", codex_herd.read_prefs()["models"]["available-model"])
        self.assertNotIn("developer_instructions", read_profile(codex_herd.PROFILE))


if __name__ == "__main__":
    unittest.main(verbosity=2)
