from __future__ import annotations

import unittest

from src.runtime.data_hooks import DataHookCatalog


class DataHookCatalogTests(unittest.TestCase):
    def test_register_hook_produces_snapshot_with_preview(self) -> None:
        catalog = DataHookCatalog()
        catalog.register_hook(
            "agent.snapshot",
            family="agent",
            producer="agent_host",
            description="Current agent snapshot.",
            freshness="live",
            preview_provider=lambda: "x" * 400,
        )

        snapshot = catalog.get_hook_snapshot("agent.snapshot")

        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot["family"], "agent")
        self.assertEqual(snapshot["producer"], "agent_host")
        self.assertTrue(str(snapshot["preview"]).endswith("..."))

    def test_unregister_and_provider_errors_are_handled_gracefully(self) -> None:
        catalog = DataHookCatalog()
        catalog.register_hook(
            "broken.preview",
            family="runtime",
            producer="test",
            description="Broken provider.",
            freshness="live",
            preview_provider=lambda: (_ for _ in ()).throw(RuntimeError("preview failed")),
        )

        snapshot = catalog.get_hook_snapshot("broken.preview")
        self.assertEqual(snapshot["preview"]["error"], "preview failed")

        catalog.unregister_hook("broken.preview")
        self.assertIsNone(catalog.get_hook_snapshot("broken.preview"))


if __name__ == "__main__":
    unittest.main()
