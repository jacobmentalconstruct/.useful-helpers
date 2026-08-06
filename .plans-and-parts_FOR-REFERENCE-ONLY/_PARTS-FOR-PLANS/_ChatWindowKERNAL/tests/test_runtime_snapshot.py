from __future__ import annotations

import logging
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from src.runtime.activity_stream import ActivityStream
from src.runtime.contracts.agent import AgentSnapshot, AgentStepSnapshot
from src.runtime.contracts.session import HardwareSnapshot, SessionInfoSnapshot, SessionSnapshot
from src.runtime.contracts.tools import ToolDescriptor, ToolExecutionSnapshot, ToolRuntimeSnapshot
from src.runtime.data_hooks import DataHookCatalog
from src.shell.app_context import AppConfig, AppContext, UIDefaults
from src.shell.event_bus import EventBus
from src.shell.lifecycle import LifecycleManager
from src.shell.runtime_snapshot import RuntimeSnapshotBuilder
from src.shell.state_manager import SessionState, UIState, WindowState
from src.shell.status_controller import StatusController
from src.utils.paths import build_app_paths


@dataclass(frozen=True)
class _FakeLifecycleSnapshot:
    phase: str
    detail: str
    updated_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "phase": self.phase,
            "detail": self.detail,
            "updated_at": self.updated_at,
        }


class _FakeTaskManager:
    def snapshot(self):
        return [{"task_id": "1", "name": "demo", "state": "completed"}]


class _FakeRegistry:
    def snapshot(self):
        return [{"widget_id": "chat.input", "role": "chat_input"}]

    def snapshot_tree(self):
        return [{"widget_id": "chat.input", "role": "chat_input", "children": []}]


class _FakePanelManager:
    def snapshot(self):
        return [{"panel_id": "chat", "mounted": True, "region": "primary", "state": {}}]


class _FakeAgentController:
    def get_snapshot(self) -> AgentSnapshot:
        return AgentSnapshot(
            controller_state="idle",
            active_turn_id=None,
            last_user_message="hello",
            last_agent_message="host response",
            current_loop="host_prep",
            current_step=AgentStepSnapshot(
                step_id="step-1",
                phase="respond",
                summary="Placeholder response complete.",
                status="completed",
                created_at="2026-03-15T12:00:00Z",
            ),
            pending_approvals=[],
            evidence_summary={"state": "placeholder"},
            stop_requested=False,
            updated_at="2026-03-15T12:00:01Z",
        )


class _FakeToolService:
    def get_execution_snapshot(self, execution_id: str) -> ToolExecutionSnapshot | None:
        if execution_id != "exec-1":
            return None
        return ToolExecutionSnapshot(
            execution_id="exec-1",
            tool_id="echo.summary",
            state="completed",
            submitted_at="2026-03-15T12:00:02Z",
            completed_at="2026-03-15T12:00:03Z",
            summary="Tool completed.",
            arguments={"text": "hello"},
            result_preview={"word_count": 1},
        )

    def get_snapshot(self) -> ToolRuntimeSnapshot:
        return ToolRuntimeSnapshot(
            available_tools=[
                ToolDescriptor(
                    tool_id="echo.summary",
                    name="Echo Summary",
                    description="Summarize user text.",
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


class _FakeSessionController:
    def get_snapshot(self) -> SessionSnapshot:
        return SessionSnapshot(
            active_session=SessionInfoSnapshot(
                session_id="sess-test",
                name="Snapshot Session",
                created_at="2026-03-15T12:00:00Z",
                updated_at="2026-03-15T12:00:03Z",
                message_count=2,
            ),
            available_sessions=[],
            available_models=["echo/test"],
            available_loops=["plan_act_observe"],
            current_model="echo/test",
            model_status="Echo/test ready",
            current_loop="plan_act_observe",
            use_echo=True,
            hardware=HardwareSnapshot(
                cpu_label="CPU 8 threads",
                ram_summary="RAM 4.0/8.0 GB",
                gpu_label="GPU unavailable",
                vram_summary="VRAM unavailable",
                updated_at="2026-03-15T12:00:03Z",
            ),
            updated_at="2026-03-15T12:00:03Z",
        )


class RuntimeSnapshotTests(unittest.TestCase):
    def test_runtime_snapshot_contains_core_sections_and_writes_to_disk(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in ["config", "state", "logs", "runtime", "runtime/crash_reports", "runtime/snapshots"]:
                (root / relative).mkdir(parents=True, exist_ok=True)

            paths = build_app_paths(root)
            event_bus = EventBus()
            lifecycle = LifecycleManager(event_bus)
            lifecycle.set_phase("ready", "Snapshot test")
            activity_stream = ActivityStream()
            data_hook_catalog = DataHookCatalog()
            activity_stream.append_event(
                "system.status",
                "status_controller",
                "Ready",
            )
            data_hook_catalog.register_hook(
                "shell.session_state",
                family="shell",
                producer="test",
                description="Session state preview.",
                freshness="live",
                preview_provider=lambda: {"draft_text": "draft"},
            )
            status = StatusController(event_bus, activity_stream)
            status.set_status("Ready")

            context = AppContext(
                paths=paths,
                app_config=AppConfig(
                    app_id="chat_window_kernal",
                    app_name="ChatWindowKERNAL",
                    theme="harbor_mist",
                    dark_theme="cinder_tide",
                    enable_inspector_panel=True,
                    enable_debug_logging=True,
                    queue_poll_interval_ms=75,
                ),
                ui_defaults=UIDefaults(
                    default_width=1200,
                    default_height=800,
                    min_width=900,
                    min_height=600,
                    secondary_panel_visible=True,
                    secondary_panel_width=340,
                ),
                app_logger=logging.getLogger("app"),
                event_bus=event_bus,
                lifecycle=lifecycle,
                task_manager=_FakeTaskManager(),
                ui_registry=_FakeRegistry(),
                status_controller=status,
                panel_manager=_FakePanelManager(),
                activity_stream=activity_stream,
                data_hook_catalog=data_hook_catalog,
                agent_controller=_FakeAgentController(),
                session_controller=_FakeSessionController(),
                tool_service=_FakeToolService(),
            )

            builder = RuntimeSnapshotBuilder(
                context,
                window_state_provider=lambda: WindowState(10, 20, 1200, 800, False),
                ui_state_provider=lambda: UIState("harbor_mist", True, 340, "agent_hud", None),
                session_state_provider=lambda: SessionState("draft", "chat", None),
            )

            snapshot = builder.build_snapshot()
            written_path = builder.write_snapshot("test")

            self.assertEqual(snapshot["app"]["app_name"], "ChatWindowKERNAL")
            self.assertIn("widget_registry", snapshot)
            self.assertIn("activity_stream", snapshot)
            self.assertIn("data_hooks", snapshot)
            self.assertIn("agent_snapshot", snapshot)
            self.assertIn("session_snapshot", snapshot)
            self.assertIn("tool_snapshot", snapshot)
            self.assertIn("pending_hitl", snapshot)
            self.assertEqual(snapshot["agent_snapshot"]["controller_state"], "idle")
            self.assertEqual(snapshot["tool_snapshot"]["available_tools"][0]["tool_id"], "echo.summary")
            self.assertTrue(written_path.exists())


if __name__ == "__main__":
    unittest.main()
