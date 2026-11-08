import contextlib
import copy
import io
import unittest

import codex_herd


class ContextMetadataTests(unittest.TestCase):
    def setUp(self):
        self.model = {
            "name": "model",
            "capabilities": ["tools"],
            "loaded": [],
            "configured_context_window": 16384,
        }

    def test_unloaded_model_uses_configured_num_ctx_without_claiming_allocation(self):
        self.assertEqual(
            codex_herd.effective_context(self.model, {"models": {}}),
            (16384, "model-configured num_ctx"),
        )
        entry = codex_herd.codex_entry(self.model, {"models": {}})
        self.assertEqual(entry["context_window"], 16384)

    def test_loaded_allocation_takes_precedence_over_model_configuration(self):
        self.model["loaded"] = [{"node": "node-a", "context_length": 8192}]
        self.assertEqual(
            codex_herd.effective_context(self.model, {"models": {}}),
            (8192, "live backend allocation"),
        )

    def test_saved_preference_takes_precedence_and_invalid_values_are_rejected(self):
        prefs = {"models": {"model": {"codex_context_window": 32768}}}
        self.assertEqual(codex_herd.effective_context(self.model, prefs), (32768, "saved Codex preference"))
        for value in (True, "16384", 512, 262145):
            with self.subTest(value=value):
                prefs["models"]["model"]["codex_context_window"] = value
                with self.assertRaises(codex_herd.HerdError):
                    codex_herd.codex_entry(self.model, prefs)

    def test_unknown_unloaded_context_is_labeled_as_safe_fallback(self):
        self.model.pop("configured_context_window")
        self.assertEqual(
            codex_herd.effective_context(self.model, {"models": {}}),
            (4096, "safe fallback; configured allocation unknown"),
        )

    def test_config_show_uses_the_same_context_as_generated_catalog(self):
        self.model.update({
            "embedding_only": False,
            "tool_capable": True,
            "online_nodes": ["node-a"],
            "model_context_window": 131072,
            "model_parameters": {},
        })
        configured = copy.deepcopy(self.model)
        loaded = copy.deepcopy(self.model)
        loaded["loaded"] = [{"node": "node-a", "context_length": 8192}]
        unknown = copy.deepcopy(self.model)
        unknown.pop("configured_context_window")
        cases = [
            (configured, {"models": {}}, "model-configured num_ctx; backend allocation unobserved"),
            (configured, {"models": {"model": {"codex_context_window": 32768}}}, "saved local Codex preference"),
            (loaded, {"models": {}}, "derived from live loaded backend; not saved"),
            (unknown, {"models": {}}, "safe fallback; configured value and backend allocation unknown; not saved"),
        ]

        for model, prefs, label in cases:
            with self.subTest(label=label):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    codex_herd.config_show("model", {"model": model}, prefs)
                catalog_entry = codex_herd.codex_entry(model, prefs)
                rendered = output.getvalue()
                self.assertIn(f"Codex catalog context: {catalog_entry['context_window']:,} ({label})", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
