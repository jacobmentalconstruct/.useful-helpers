from __future__ import annotations

import tkinter as tk
import unittest
from tkinter import ttk

from src.runtime.contracts.agent import AgentSnapshot, AgentStepSnapshot, HITLGateSnapshot
from src.runtime.contracts.tools import ToolDescriptor, ToolExecutionSnapshot, ToolRuntimeSnapshot
from src.shell.event_bus import EventBus
from src.shell.ui_registry import UIRegistry
from src.ui.panels.workspace_panel import WorkspacePanel
from src.ui.styles import ThemeManager


def _sample_agent_snapshot() -> AgentSnapshot:
    return AgentSnapshot(
        controller_state="awaiting_hitl",
        active_turn_id="turn-1",
        last_user_message="Need approval.",
        last_agent_message="",
        current_loop="host_prep",
        current_step=AgentStepSnapshot(
            step_id="step-1",
            phase="hitl",
            summary="Waiting for human approval.",
            status="waiting",
            created_at="2026-03-15T12:00:00Z",
        ),
        pending_approvals=[
            HITLGateSnapshot(
                approval_id="approval-1",
                label="Approval required",
                prompt="Confirm this action.",
                status="waiting",
                requested_at="2026-03-15T12:00:00Z",
            )
        ],
        evidence_summary={"state": "placeholder"},
        stop_requested=False,
        updated_at="2026-03-15T12:00:01Z",
    )


def _sample_tool_snapshot() -> ToolRuntimeSnapshot:
    return ToolRuntimeSnapshot(
        available_tools=[
            ToolDescriptor(
                tool_id="echo.summary",
                name="Echo Summary",
                description="Summarize text.",
                category="utility",
                manifest_path="tool_packages/echo_summary/manifest.json",
            )
        ],
        recent_executions=[
            ToolExecutionSnapshot(
                execution_id="exec-1",
                tool_id="echo.summary",
                state="completed",
                submitted_at="2026-03-15T12:00:02Z",
                completed_at="2026-03-15T12:00:03Z",
                summary="Tool completed.",
                arguments={"text": "hello"},
                result_preview={"word_count": 1},
            )
        ],
        active_execution_ids=[],
        updated_at="2026-03-15T12:00:03Z",
    )


def _sample_activity_events() -> list[dict]:
    return [
        {
            "event_id": "event-1",
            "family": "agent.turn",
            "source": "agent_host",
            "level": "info",
            "summary": "Turn received.",
            "detail": "",
            "payload": {"turn_id": "turn-1"},
            "created_at": "2026-03-15T12:00:00Z",
        }
    ]


def _sample_data_hooks() -> list[dict]:
    return [
        {
            "hook_id": "agent.snapshot",
            "family": "agent",
            "producer": "agent_host",
            "description": "Current agent snapshot.",
            "freshness": "live",
            "preview": {"controller_state": "awaiting_hitl"},
            "updated_at": "2026-03-15T12:00:01Z",
        }
    ]


def _sample_widget_tree() -> list[dict]:
    return [
        {
            "widget_id": "main.window",
            "role": "main_window",
            "panel_id": "shell",
            "children": [
                {
                    "widget_id": "chat.input",
                    "role": "chat_input",
                    "panel_id": "chat",
                    "children": [],
                }
            ],
        }
    ]


def _sample_widget_records() -> list[dict]:
    return [
        {
            "widget_id": "main.window",
            "role": "main_window",
            "panel_id": "shell",
            "parent_id": None,
        },
        {
            "widget_id": "chat.input",
            "role": "chat_input",
            "panel_id": "chat",
            "parent_id": "main.window",
        },
    ]


class WorkspacePanelTests(unittest.TestCase):
    def test_workspace_panel_mounts_tabs_and_aggregates_snapshots(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk unavailable: {exc}")

        try:
            theme_manager = ThemeManager(root)
            theme_manager.apply("harbor_mist")

            host = ttk.Frame(root)
            host.grid(row=0, column=0, sticky="nsew")
            registry = UIRegistry(EventBus())
            panel = WorkspacePanel(
                theme_manager,
                on_resolve_hitl=lambda *_args: None,
                on_run_tool=lambda *_args: "exec-1",
                on_cancel_tool=lambda *_args: True,
                on_tab_selected=lambda *_args: None,
            )
            panel.build(host)
            panel.register_widgets(registry)
            panel.restore_state(
                {
                    "workspace_selected_tab": "tools",
                    "inspector_selected_widget_id": "chat.input",
                }
            )
            panel.refresh(
                agent_snapshot=_sample_agent_snapshot(),
                tool_snapshot=_sample_tool_snapshot(),
                activity_events=_sample_activity_events(),
                data_hooks=_sample_data_hooks(),
                widget_tree=_sample_widget_tree(),
                widget_records=_sample_widget_records(),
            )
            root.update_idletasks()

            snapshot = panel.get_snapshot()
            widget_ids = {record["widget_id"] for record in registry.snapshot()}

            self.assertEqual(panel.get_selected_tab_id(), "tools")
            self.assertEqual(panel.get_selected_widget_id(), "chat.input")
            self.assertEqual(snapshot["selected_tab"], "tools")
            self.assertEqual(
                set(snapshot["tabs"].keys()),
                {"agent_hud", "tools", "events", "inspector"},
            )
            self.assertEqual(snapshot["tabs"]["agent_hud"]["pending_approval_count"], 1)
            self.assertEqual(snapshot["tabs"]["inspector"]["widget_count"], 2)
            self.assertIn("workspace.notebook", widget_ids)
            self.assertIn("workspace.tools.catalog", widget_ids)
            self.assertIn("workspace.events.tree", widget_ids)
        finally:
            root.destroy()

    def test_workspace_interactions_emit_ui_callbacks(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk unavailable: {exc}")

        try:
            interactions: list[tuple[str, str, dict]] = []
            theme_manager = ThemeManager(root)
            theme_manager.apply("harbor_mist")

            host = ttk.Frame(root)
            host.grid(row=0, column=0, sticky="nsew")
            panel = WorkspacePanel(
                theme_manager,
                on_resolve_hitl=lambda *_args: None,
                on_run_tool=lambda *_args: "exec-1",
                on_cancel_tool=lambda *_args: True,
                on_tab_selected=lambda *_args: None,
                on_ui_event=lambda source, summary, payload=None: interactions.append(
                    (source, summary, payload or {})
                ),
            )
            panel.build(host)
            panel.refresh(
                agent_snapshot=_sample_agent_snapshot(),
                tool_snapshot=_sample_tool_snapshot(),
                activity_events=_sample_activity_events(),
                data_hooks=_sample_data_hooks(),
                widget_tree=_sample_widget_tree(),
                widget_records=_sample_widget_records(),
            )
            root.update_idletasks()

            tools_tab = panel._tabs["tools"]
            tools_tab._tools_tree.selection_set("echo.summary")
            tools_tab._select_tool(None)

            events_tab = panel._tabs["events"]
            events_tab._family_filter.set("agent")
            events_tab._handle_family_filter_changed()
            events_tab._tree.selection_set("event-1")
            events_tab._render_selected_detail()

            inspector_tab = panel._tabs["inspector"]
            inspector_tab._tree.selection_set("chat.input")
            inspector_tab._handle_selection(None)

            agent_tab = panel._tabs["agent_hud"]
            agent_tab._approvals_tree.selection_set("approval-1")
            agent_tab._on_approval_selected(None)

            summaries = {(source, summary) for source, summary, _payload in interactions}
            payloads = [payload for _source, _summary, payload in interactions]

            self.assertIn(("workspace.tools", "Tool selected in Tools tab."), summaries)
            self.assertIn(("workspace.events", "Events family filter changed."), summaries)
            self.assertIn(("workspace.events", "Runtime event selected in Events tab."), summaries)
            self.assertIn(("workspace.inspector", "Widget selected in Inspector tab."), summaries)
            self.assertIn(("workspace.agent_hud", "Agent HUD approval selected."), summaries)
            self.assertTrue(any(payload.get("tool_id") == "echo.summary" for payload in payloads))
            self.assertTrue(any(payload.get("widget_id") == "chat.input" for payload in payloads))
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
