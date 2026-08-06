from __future__ import annotations

import logging
import time
import unittest
from pathlib import Path

from src.runtime.adapters.mindshard_adapter import ECHO_MODEL
from src.shell.app_context import build_app_context
from src.shell.app_kernel import AppKernel
from src.utils.paths import build_app_paths


class _FakeChatPanel:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []
        self.clear_calls = 0
        self.agent_states: list[str] = []

    def append_message(self, role: str, text: str) -> None:
        self.messages.append((role, text))

    def clear_input(self) -> None:
        self.clear_calls += 1

    def get_draft_text(self) -> str:
        return ""

    def render_agent_state(self, snapshot) -> None:
        self.agent_states.append(snapshot.controller_state if snapshot is not None else "none")

    def update_session_snapshot(self, _snapshot) -> None:
        return

    def clear_transcript(self) -> None:
        self.messages.clear()


class _FakePanelManager:
    def __init__(self, chat_panel: _FakeChatPanel) -> None:
        self._chat_panel = chat_panel

    def get_panel(self, panel_id: str):
        if panel_id != "chat":
            raise KeyError(panel_id)
        return self._chat_panel


class HostIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        paths = build_app_paths(project_root)
        context = build_app_context(paths)
        context.app_logger = logging.getLogger("app")
        self.kernel = AppKernel(context)
        self.kernel.context.session_controller.set_model(ECHO_MODEL)
        self.chat_panel = _FakeChatPanel()
        self.kernel.context.panel_manager = _FakePanelManager(self.chat_panel)

    def tearDown(self) -> None:
        self.kernel.context.task_manager.shutdown(wait=True)

    def test_chat_submission_routes_through_agent_host_and_activity_stream(self) -> None:
        self.kernel._handle_send_message("Host prep hello")

        self.assertEqual(self.chat_panel.messages[0], ("You", "Host prep hello"))
        self.assertEqual(self.chat_panel.clear_calls, 1)
        self.assertEqual(
            self.kernel.context.agent_controller.get_snapshot().controller_state,
            "processing",
        )

        snapshot = self._wait_for_agent_state("idle")

        families = {
            event["family"] for event in self.kernel.context.activity_stream.recent_events(limit=20)
        }
        self.assertIn("ui.interaction", families)
        self.assertIn("agent.turn", families)
        self.assertIn("agent.step", families)
        self.assertEqual(snapshot.controller_state, "idle")
        self.assertTrue(any(role == "Agent" for role, _ in self.chat_panel.messages))

    def test_hitl_resolution_resumes_the_placeholder_agent_turn(self) -> None:
        self.kernel._handle_send_message("Please request human approval for this turn.")
        self.kernel._sync_agent_chat_output()

        awaiting = self.kernel.context.agent_controller.get_snapshot()
        self.assertEqual(awaiting.controller_state, "awaiting_hitl")
        self.assertEqual(len(awaiting.pending_approvals), 1)
        self.assertTrue(
            any(
                role == "System" and "Human approval is required" in text
                for role, text in self.chat_panel.messages
            )
        )

        approval_id = awaiting.pending_approvals[0].approval_id
        self.kernel._resolve_hitl_gate(approval_id, True)
        completed = self._wait_for_agent_state("idle")

        families = {
            event["family"] for event in self.kernel.context.activity_stream.recent_events(limit=30)
        }
        self.assertIn("agent.hitl_wait", families)
        self.assertIn("agent.hitl_resolved", families)
        self.assertEqual(completed.controller_state, "idle")
        self.assertEqual(len(completed.pending_approvals), 0)
        self.assertTrue(any(role == "Agent" for role, _ in self.chat_panel.messages))

    def test_tool_run_updates_runtime_snapshot_and_activity_stream(self) -> None:
        execution_id = self.kernel._run_tool("echo.summary", {"text": "alpha beta gamma"})

        self._wait_for_no_active_tasks()
        snapshot = self.kernel.context.tool_service.get_execution_snapshot(execution_id)
        families = {
            event["family"] for event in self.kernel.context.activity_stream.recent_events(limit=30)
        }

        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.state, "completed")
        self.assertEqual(snapshot.result_preview["word_count"], 3)
        self.assertIn("tool.requested", families)
        self.assertIn("tool.started", families)
        self.assertIn("tool.completed", families)

    def _wait_for_agent_state(self, expected_state: str):
        deadline = time.time() + 8
        while time.time() < deadline:
            self.kernel._process_task_results()
            self.kernel._sync_agent_chat_output()
            snapshot = self.kernel.context.agent_controller.get_snapshot()
            if (
                snapshot.controller_state == expected_state
                and self.kernel.context.task_manager.active_task_count() == 0
            ):
                return snapshot
            time.sleep(0.05)
        self.fail(f"Timed out waiting for agent state: {expected_state}")

    def _wait_for_no_active_tasks(self) -> None:
        deadline = time.time() + 8
        while time.time() < deadline:
            self.kernel._process_task_results()
            self.kernel._sync_agent_chat_output()
            if self.kernel.context.task_manager.active_task_count() == 0:
                return
            time.sleep(0.05)
        self.fail("Timed out waiting for background tasks to finish.")


if __name__ == "__main__":
    unittest.main()
