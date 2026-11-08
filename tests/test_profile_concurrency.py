import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest import mock

import codex_herd


def fleet_models():
    return {
        name: {
            "name": name,
            "embedding_only": False,
            "tool_capable": True,
            "online_nodes": ["test-node"],
            "loaded": [],
            "capabilities": ["tools"],
            "model_parameters": {},
        }
        for name in ("alpha-model", "beta-model")
    }


class ConcurrentProfileGenerationTests(unittest.TestCase):
    def test_concurrent_model_launch_profiles_remain_isolated_and_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "codex-home"
            inventory = Path(tmp) / "inventory.json"
            preferences = Path(tmp) / "preferences.json"
            catalogs = Path(tmp) / "catalog.json"
            prefs = {
                "default_model": "alpha-model",
                "models": {
                    "alpha-model": {"developer_instructions": "alpha instructions"},
                    "beta-model": {"developer_instructions": "beta instructions"},
                },
            }
            start = Barrier(3)

            with (
                mock.patch.object(codex_herd, "CODEX_HOME", home),
                mock.patch.object(codex_herd, "INVENTORY", inventory),
                mock.patch.object(codex_herd, "PREFS", preferences),
                mock.patch.object(codex_herd, "CATALOG", catalogs),
            ):
                def launch(model_name):
                    start.wait()
                    codex_herd.sync_catalog(fleet_models(), prefs, model_name)

                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = [executor.submit(launch, name) for name in ("alpha-model", "beta-model")]
                    start.wait()
                    for future in futures:
                        future.result()

                alpha_name, alpha_profile, alpha_catalog = codex_herd.model_profile_paths("alpha-model")
                beta_name, beta_profile, beta_catalog = codex_herd.model_profile_paths("beta-model")
                self.assertNotEqual(alpha_name, beta_name)
                self.assertNotEqual(alpha_profile, beta_profile)
                self.assertNotEqual(alpha_catalog, beta_catalog)

                alpha_text = alpha_profile.read_text()
                beta_text = beta_profile.read_text()
                self.assertIn('model = "alpha-model"', alpha_text)
                self.assertIn('developer_instructions = "alpha instructions"', alpha_text)
                self.assertIn(str(alpha_catalog), alpha_text)
                self.assertIn('model = "beta-model"', beta_text)
                self.assertIn('developer_instructions = "beta instructions"', beta_text)
                self.assertIn(str(beta_catalog), beta_text)

                for path in (alpha_catalog, beta_catalog, inventory):
                    self.assertTrue(path.is_file())
                    json.loads(path.read_text())
