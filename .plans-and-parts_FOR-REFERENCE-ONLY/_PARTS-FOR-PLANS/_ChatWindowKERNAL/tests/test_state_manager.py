from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.shell.app_context import UIDefaults
from src.shell.state_manager import SessionState, StateManager, UIState, WindowState
from src.utils.paths import build_app_paths


class StateManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        for relative in ["config", "state", "logs", "runtime", "runtime/crash_reports", "runtime/snapshots"]:
            (root / relative).mkdir(parents=True, exist_ok=True)

        self.paths = build_app_paths(root)
        self.defaults = UIDefaults(
            default_width=1200,
            default_height=800,
            min_width=900,
            min_height=600,
            secondary_panel_visible=True,
            secondary_panel_width=340,
        )
        self.manager = StateManager(self.paths, self.defaults)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_defaults_are_used_when_state_files_are_missing(self) -> None:
        self.assertEqual(self.manager.load_window_state().width, 1200)
        self.assertEqual(self.manager.load_ui_state().theme_name, "harbor_mist")
        self.assertEqual(self.manager.load_ui_state().workspace_selected_tab, "agent_hud")
        self.assertEqual(self.manager.load_session_state().last_active_panel, "chat")

    def test_saved_state_round_trips(self) -> None:
        window_state = WindowState(x=40, y=60, width=1400, height=900, maximized=True)
        ui_state = UIState(
            theme_name="cinder_tide",
            secondary_panel_visible=False,
            secondary_panel_width=420,
            workspace_selected_tab="tools",
            inspector_selected_widget_id="chat.input",
        )
        session_state = SessionState(
            draft_text="hello",
            last_active_panel="chat",
            last_snapshot_file="snapshot.json",
        )

        self.manager.save_window_state(window_state)
        self.manager.save_ui_state(ui_state)
        self.manager.save_session_state(session_state)

        self.assertEqual(self.manager.load_window_state(), window_state)
        self.assertEqual(self.manager.load_ui_state(), ui_state)
        self.assertEqual(self.manager.load_session_state(), session_state)


if __name__ == "__main__":
    unittest.main()
