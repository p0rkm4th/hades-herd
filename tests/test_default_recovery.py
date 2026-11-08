import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
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
        self.original_paths = {
            name: getattr(codex_herd, name)
            for name in ("CODEX_HOME", "CATALOG", "PROFILE", "INVENTORY", "PREFS")
        }
        codex_herd.CODEX_HOME = root / "codex-home"
        codex_herd.CATALOG = root / "catalog.json"
        codex_herd.PROFILE = root / "herd.config.toml"
        codex_herd.INVENTORY = root / "inventory.json"
        codex_herd.PREFS = root / "preferences.json"
        codex_herd.CODEX_HOME.mkdir()
        self.old = {
            codex_herd.model_profile_paths("available-model")[2]: b"old catalog\n",
            codex_herd.model_profile_paths("available-model")[1]: b"old profile\n",
            codex_herd.INVENTORY: b"old inventory\n",
        }
        for path, data in self.old.items():
            path.write_bytes(data)

    def tearDown(self):
        for name, value in self.original_paths.items():
            setattr(codex_herd, name, value)
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
        self.assertIn('model = "available-model"', codex_herd.model_profile_paths("available-model")[1].read_text())

    def test_explicit_model_takes_precedence_over_saved_default(self):
        fleet_models = models()
        fleet_models["second-model"] = model("second-model")
        codex_herd.sync_catalog(fleet_models, {"default_model": "available-model", "models": {}}, "second-model")
        self.assertIn('model = "second-model"', codex_herd.model_profile_paths("second-model")[1].read_text())

    def test_initial_catalog_without_saved_default_uses_first_available_model(self):
        prefs = {"models": {}}
        codex_herd.sync_catalog(models(), prefs)
        self.assertIn('model = "available-model"', codex_herd.model_profile_paths("available-model")[1].read_text())
        self.assertEqual(prefs["default_model"], "available-model")

    def test_initial_default_prefers_online_model_over_sorted_offline_model(self):
        offline = model("aaa-offline")
        offline["online_nodes"] = []
        online = model("z-online")
        fleet_models = {"aaa-offline": offline, "z-online": online}
        prefs = {"models": {}}
        codex_herd.sync_catalog(fleet_models, prefs)
        self.assertEqual(prefs["default_model"], "z-online")
        self.assertIn('model = "z-online"', codex_herd.model_profile_paths("z-online")[1].read_text())

    def test_unloaded_catalog_uses_reported_ollama_context_not_architecture_limit(self):
        item = model("configured-model")
        item["online_nodes"] = ["node-a", "node-b"]
        item["model_context_window"] = 131072
        item["model_parameters"] = {"node-a": "temperature 0.6\nnum_ctx 16384", "node-b": "num_ctx 8192"}
        entry = codex_herd.codex_entry(item, {"models": {}})
        self.assertEqual(entry["context_window"], 8192)
        self.assertEqual(entry["context_source"], "Ollama configured num_ctx on all online nodes")
        item["model_parameters"] = {"node-a": "num_ctx 16384"}
        entry = codex_herd.codex_entry(item, {"models": {}})
        self.assertEqual(entry["context_window"], 4096)
        self.assertEqual(entry["context_source"], "unverified safe fallback")

    def test_config_show_matches_catalog_context_when_only_one_duplicate_host_is_loaded(self):
        item = model("configured-model")
        item["online_nodes"] = ["node-a", "node-b"]
        item["loaded"] = [{"node": "node-a", "context_length": 16384}]
        item["model_parameters"] = {
            "node-a": "num_ctx 16384",
            "node-b": "num_ctx 8192",
        }
        prefs = {"models": {}}

        catalog_entry = codex_herd.codex_entry(item, prefs)
        output = io.StringIO()
        with redirect_stdout(output):
            codex_herd.config_show("configured-model", {"configured-model": item}, prefs)

        self.assertEqual(catalog_entry["context_window"], 8192)
        self.assertIn(
            "Codex catalog context: 8,192 (Ollama configured num_ctx)",
            output.getvalue(),
        )
        self.assertIn("Backend allocated context: node-a=16,384", output.getvalue())

        prefs["models"]["configured-model"] = {"codex_context_window": 16384}
        output = io.StringIO()
        with redirect_stdout(output):
            codex_herd.config_show("configured-model", {"configured-model": item}, prefs)
        self.assertIn(
            "Codex catalog context: 16,384 (saved local Codex preference)",
            output.getvalue(),
        )
        self.assertIn(
            "Context warning: saved Codex budget 16,384 exceeds the lowest Ollama configured num_ctx 8,192",
            output.getvalue(),
        )

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
        config = read_profile(codex_herd.model_profile_paths("available-model")[1])
        self.assertEqual(config["developer_instructions"], 'Use `exec_command`; say "done". ☃')

        codex_herd.sync_catalog(fleet_models, prefs, "second-model")
        config = read_profile(codex_herd.model_profile_paths("second-model")[1])
        self.assertEqual(config["developer_instructions"], "Inspect once, then implement.")
        self.assertEqual(
            read_profile(codex_herd.model_profile_paths("available-model")[1])["developer_instructions"],
            'Use `exec_command`; say "done". ☃',
        )
        self.assertEqual(prefs["default_model"], "available-model")

    def test_guidance_is_omitted_when_unset_and_invalid_value_preserves_generated_files(self):
        prefs = {"default_model": "available-model", "models": {}}
        codex_herd.sync_catalog(models(), prefs)
        config = read_profile(codex_herd.model_profile_paths("available-model")[1])
        self.assertNotIn("developer_instructions", config)

        generated = {
            path: path.read_bytes()
            for path in (codex_herd.model_profile_paths("available-model")[2], codex_herd.model_profile_paths("available-model")[1], codex_herd.INVENTORY)
        }
        prefs["models"]["available-model"] = {"developer_instructions": ["wrong type"]}
        with self.assertRaisesRegex(codex_herd.HerdError, "must be text"):
            codex_herd.sync_catalog(models(), prefs)
        for path, content in generated.items():
            self.assertEqual(path.read_bytes(), content, str(path))

    def test_atomic_profile_replace_preserves_previous_file_on_replace_error(self):
        target = codex_herd.model_profile_paths("available-model")[1]
        target.write_text("previous complete profile\n")
        existing_paths = set(target.parent.iterdir())
        with mock.patch.object(codex_herd.os, "replace", side_effect=OSError("simulated replace failure")):
            with self.assertRaisesRegex(OSError, "simulated replace failure"):
                codex_herd.atomic_write_text(target, "new profile\n")
        self.assertEqual(target.read_text(), "previous complete profile\n")
        self.assertEqual(set(target.parent.iterdir()), existing_paths)

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
        saved = read_profile(codex_herd.model_profile_paths("available-model")[1])
        self.assertEqual(
            saved["developer_instructions"],
            "Use only exec_command; implement and verify.",
        )

        inputs = TerminalInput("\n\n!clear\n\nn\n")
        with mock.patch.object(codex_herd.sys, "stdin", inputs):
            codex_herd.configure("available-model", models(), prefs)
        self.assertNotIn("developer_instructions", codex_herd.read_prefs()["models"]["available-model"])
        self.assertNotIn("developer_instructions", read_profile(codex_herd.model_profile_paths("available-model")[1]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
