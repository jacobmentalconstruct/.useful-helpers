"""
Owns: top-level shell orchestration for startup, runtime polling, and shutdown.
Does not own: panel rendering details, persistence schemas, or model behavior.
Collaborates with: every shell subsystem, the host runtime, and the Tkinter UI layer.
"""

from __future__ import annotations

import logging
import threading
import traceback
from pathlib import Path
import tkinter as tk

from src.runtime.activity_stream import ActivityEvent, ActivityStream
from src.runtime.agent_host.controller import HostAgentController
from src.runtime.agent_host.session_controller import HostSessionController
from src.runtime.adapters.mindshard_adapter import ECHO_MODEL, MindshardAdapter
from src.runtime.data_hooks import DataHookCatalog
from src.runtime.tools.service import PackageToolService
from src.shell.app_context import AppContext, build_app_context
from src.shell.constants import (
    ACTIVITY_UI_INTERACTION,
    PRIMARY_PANEL_ID,
    SECONDARY_PANEL_ID,
    STATUS_BUSY,
    STATUS_ERROR,
    STATUS_INFO,
    STATUS_READY,
    STATUS_SHUTTING_DOWN,
    STATUS_WARNING,
)
from src.shell.crash_handler import CrashHandler, write_crash_report
from src.shell.event_bus import EventBus
from src.shell.layout_manager import LayoutManager
from src.shell.lifecycle import LifecycleManager
from src.shell.logging_setup import configure_logging
from src.shell.panel_manager import PanelManager
from src.shell.runtime_snapshot import RuntimeSnapshotBuilder
from src.shell.state_manager import SessionState, StateManager
from src.shell.status_controller import StatusController
from src.shell.task_manager import TaskManager, TaskResult
from src.shell.ui_registry import UIRegistry
from src.ui.dialogs.session_manager_dialog import SessionDialogActions, SessionManagerDialog
from src.ui.geometry import apply_window_state, capture_window_state
from src.ui.main_window import MainWindow, WindowActions
from src.ui.panels.chat_panel import ChatPanel
from src.ui.panels.workspace_panel import WorkspacePanel
from src.ui.styles import ThemeManager
from src.utils.paths import build_app_paths


class AppKernel:
    def __init__(self, context: AppContext) -> None:
        self.context = context
        self.logger = logging.getLogger("shell.kernel")

        self.root: tk.Tk | None = None
        self.theme_manager: ThemeManager | None = None
        self.main_window: MainWindow | None = None
        self.crash_handler: CrashHandler | None = None
        self.session_dialog: SessionManagerDialog | None = None

        self._shutdown_lock = threading.Lock()
        self._shutdown_requested = False
        self._shutdown_reason = "normal_exit"
        self._is_shutting_down = False
        self._workspace_dirty = True
        self._last_task_count: int | None = None
        self._theme_name = context.app_config.theme
        self._last_snapshot_file: str | None = None
        self._last_agent_message_rendered = ""
        self._last_pending_approval_count = 0

        self._window_state = None
        self._ui_state = None
        self._session_state = None

        self._build_services()
        self._load_state()
        self._build_runtime_services()

    def start(self) -> None:
        self.context.lifecycle.set_phase("starting", "Creating root window and restoring state.")
        self.context.status_controller.set_status("Loading state...", level=STATUS_BUSY)

        self.root = tk.Tk()
        self.theme_manager = ThemeManager(self.root)

        self._build_window()
        self._mount_panels()
        self._restore_panel_state()
        self._install_runtime_services()
        self._install_crash_handler()
        self._refresh_workspace()
        self._render_status()

        self.context.lifecycle.set_phase("ready", "Shell ready.")
        self.context.status_controller.set_status("Ready", level=STATUS_READY)
        self.context.status_controller.set_task_summary("Idle")
        self._render_status()

        self.root.after(self.context.app_config.queue_poll_interval_ms, self._poll_runtime)
        self.root.mainloop()

    def request_shutdown(self, reason: str) -> None:
        with self._shutdown_lock:
            self._shutdown_requested = True
            self._shutdown_reason = reason
        self.logger.info("Shutdown requested. reason=%s", reason)

    def _build_services(self) -> None:
        self.context.event_bus = EventBus()
        self.context.lifecycle = LifecycleManager(self.context.event_bus)
        self.context.state_manager = StateManager(self.context.paths, self.context.ui_defaults)
        self.context.activity_stream = ActivityStream()
        self.context.data_hook_catalog = DataHookCatalog()
        self.context.status_controller = StatusController(
            self.context.event_bus,
            self.context.activity_stream,
        )
        self.context.task_manager = TaskManager(self.context.event_bus)
        self.context.ui_registry = UIRegistry(self.context.event_bus)
        self.context.layout_manager = LayoutManager(
            self.context.event_bus,
            self.context.ui_defaults.secondary_panel_width,
        )
        self.context.panel_manager = PanelManager(self.context.event_bus)
        self.context.tool_service = PackageToolService(
            self.context.paths,
            self.context.task_manager,
            self.context.activity_stream,
            self.context.data_hook_catalog,
        )

        self.context.event_bus.subscribe("*", self._mark_workspace_dirty)
        self.context.activity_stream.subscribe(self._mark_workspace_dirty_from_activity)

    def _build_runtime_services(self) -> None:
        selected_model = self._session_state.selected_model
        if self._session_state.use_echo and not selected_model:
            selected_model = ECHO_MODEL

        self.context.mindshard_adapter = MindshardAdapter(
            self.context.paths.agent_db_file,
            initial_model=selected_model,
            initial_loop=self._session_state.selected_loop,
            initial_session_id=self._session_state.active_session_id,
            use_echo=self._session_state.use_echo,
        )
        self.context.session_controller = HostSessionController(
            self.context.mindshard_adapter,
            self.context.task_manager,
            self.context.activity_stream,
            self.context.data_hook_catalog,
        )
        self.context.agent_controller = HostAgentController(
            self.context.mindshard_adapter,
            self.context.session_controller,
            self.context.task_manager,
            self.context.activity_stream,
            self.context.data_hook_catalog,
            self.context.tool_service,
        )

    def _load_state(self) -> None:
        self._window_state = self.context.state_manager.load_window_state()
        self._ui_state = self.context.state_manager.load_ui_state()
        self._session_state = self.context.state_manager.load_session_state()
        self._theme_name = self._ui_state.theme_name or self.context.app_config.theme

    def _build_window(self) -> None:
        actions = WindowActions(
            toggle_theme=self._toggle_theme,
            toggle_workspace=self._toggle_workspace,
            save_snapshot=self._save_snapshot,
            crash_test=self._trigger_crash_test if self.context.app_config.enable_debug_logging else None,
        )
        self.main_window = MainWindow(
            self.root,
            app_name=self.context.app_config.app_name,
            theme_manager=self.theme_manager,
            actions=actions,
            show_debug_actions=self.context.app_config.enable_debug_logging,
        )
        self.main_window.build()
        self.main_window.bind_close(lambda: self.request_shutdown("window_close"))

        apply_window_state(
            self.root,
            self._window_state,
            min_width=self.context.ui_defaults.min_width,
            min_height=self.context.ui_defaults.min_height,
        )
        self.main_window.apply_theme(self._theme_name)

        self.context.layout_manager.attach(self.main_window.paned_shell)
        self.context.layout_manager.restore(self._ui_state)

        self.main_window.register_widgets(self.context.ui_registry)

    def _mount_panels(self) -> None:
        chat_panel = ChatPanel(
            self.theme_manager,
            on_send=self._handle_send_message,
            on_stop=self._handle_stop_requested,
            on_pause=self._handle_pause_requested,
            on_resume=self._handle_resume_requested,
            on_model_change=self._handle_model_selected,
            on_loop_change=self._handle_loop_selected,
            on_open_session_manager=self._open_session_manager_dialog,
        )
        self.context.panel_manager.register_panel(PRIMARY_PANEL_ID, chat_panel, region="primary")
        self.context.panel_manager.mount_panel(
            PRIMARY_PANEL_ID,
            self.main_window.primary_host,
            self.context.ui_registry,
        )

        workspace_panel = WorkspacePanel(
            self.theme_manager,
            on_resolve_hitl=self._resolve_hitl_gate,
            on_run_tool=self._run_tool,
            on_cancel_tool=self._cancel_tool,
            on_tab_selected=self._handle_workspace_tab_selected,
            on_ui_event=self._record_ui_interaction,
        )
        self.context.panel_manager.register_panel(SECONDARY_PANEL_ID, workspace_panel, region="secondary")
        self.context.panel_manager.mount_panel(
            SECONDARY_PANEL_ID,
            self.main_window.secondary_host,
            self.context.ui_registry,
        )

        chat_panel.append_message(
            "System",
            "Mindshard is mounted through the host seam. Chat, session controls, tools, events, and inspection all stay observable from this shell.",
        )

    def _restore_panel_state(self) -> None:
        chat_panel = self.context.panel_manager.get_panel(PRIMARY_PANEL_ID)
        chat_panel.restore_state({"draft_text": self._session_state.draft_text})
        chat_panel.update_session_snapshot(self.context.session_controller.get_snapshot())
        chat_panel.render_agent_state(self.context.agent_controller.get_snapshot())
        chat_panel.focus_input()

        workspace_panel = self.context.panel_manager.get_panel(SECONDARY_PANEL_ID)
        workspace_panel.restore_state(
            {
                "workspace_selected_tab": self._ui_state.workspace_selected_tab,
                "inspector_selected_widget_id": self._ui_state.inspector_selected_widget_id,
            }
        )

    def _install_runtime_services(self) -> None:
        self.context.runtime_snapshot = RuntimeSnapshotBuilder(
            self.context,
            window_state_provider=self._capture_window_state,
            ui_state_provider=self._capture_ui_state,
            session_state_provider=self._capture_session_state,
        )
        self._register_data_hooks()

    def _install_crash_handler(self) -> None:
        self.crash_handler = CrashHandler(
            self.context.paths,
            self.context.event_bus,
            self.context.status_controller,
            activity_stream=self.context.activity_stream,
            snapshot_writer=lambda label: self.context.runtime_snapshot.write_snapshot(label),
            request_shutdown=self.request_shutdown,
        )
        self.crash_handler.install(self.root)

    def _poll_runtime(self) -> None:
        if self.root is None or self._is_shutting_down:
            return

        self._process_task_results()
        self._sync_task_summary()
        self._sync_session_header()
        self._sync_agent_chat_output()
        self._render_status()

        if self._workspace_dirty:
            self._refresh_workspace()

        if self._consume_shutdown_request():
            self._shutdown()
            return

        self.root.after(self.context.app_config.queue_poll_interval_ms, self._poll_runtime)

    def _process_task_results(self) -> None:
        for task_result in self.context.task_manager.drain_completed():
            if task_result.state == "completed":
                if task_result.on_success is not None:
                    task_result.on_success(task_result.result)
            else:
                if task_result.on_error is not None:
                    task_result.on_error(task_result)
                else:
                    self._handle_task_error(task_result)

    def _sync_task_summary(self) -> None:
        count = self.context.task_manager.active_task_count()
        if count == self._last_task_count:
            return

        self._last_task_count = count
        summary = "Idle" if count == 0 else f"{count} background task(s) running"
        self.context.status_controller.set_task_summary(summary)

    def _sync_agent_chat_output(self) -> None:
        agent_snapshot = self.context.agent_controller.get_snapshot()
        chat_panel = self.context.panel_manager.get_panel(PRIMARY_PANEL_ID)
        chat_panel.render_agent_state(agent_snapshot)

        pending_count = len(agent_snapshot.pending_approvals)
        if pending_count > self._last_pending_approval_count:
            chat_panel.append_message(
                "System",
                "Human approval is required. Open the Agent HUD tab in the workspace to continue.",
            )
            self.context.status_controller.set_status(
                "Awaiting human approval in Agent HUD.",
                level=STATUS_WARNING,
            )
        self._last_pending_approval_count = pending_count

        if (
            agent_snapshot.last_agent_message
            and agent_snapshot.last_agent_message != self._last_agent_message_rendered
        ):
            chat_panel.append_message("Agent", agent_snapshot.last_agent_message)
            self._last_agent_message_rendered = agent_snapshot.last_agent_message

            if agent_snapshot.controller_state == "error":
                self.context.status_controller.set_status(
                    "Agent host reported an error.",
                    level=STATUS_ERROR,
                    detail=agent_snapshot.last_agent_message,
                )
            else:
                self.context.status_controller.set_status("Ready", level=STATUS_READY)

    def _handle_send_message(self, text: str) -> None:
        chat_panel = self.context.panel_manager.get_panel(PRIMARY_PANEL_ID)
        chat_panel.append_message("You", text)
        chat_panel.clear_input()

        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "chat_panel",
            "User submitted a chat turn.",
            payload={"text_preview": text[:120]},
        )
        self.context.agent_controller.submit_user_turn(text)
        self.context.status_controller.set_status("Agent host processing turn...", level=STATUS_BUSY)
        self._workspace_dirty = True

    def _handle_stop_requested(self) -> None:
        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "chat_panel",
            "User requested stop from the chat panel.",
        )
        self.context.agent_controller.request_stop()
        self.context.status_controller.set_status("Stop requested.", level=STATUS_WARNING)
        self._workspace_dirty = True

    def _handle_pause_requested(self) -> None:
        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "chat_panel",
            "User requested pause from the chat panel.",
        )
        self.context.agent_controller.pause_run()
        self.context.status_controller.set_status(
            "Pause requested at the next safe checkpoint.",
            level=STATUS_WARNING,
        )
        self._workspace_dirty = True

    def _handle_resume_requested(self) -> None:
        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "chat_panel",
            "User requested resume from the chat panel.",
        )
        self.context.agent_controller.resume_run()
        self.context.status_controller.set_status("Mindshard turn resumed.", level=STATUS_BUSY)
        self._workspace_dirty = True

    def _handle_model_selected(self, model_name: str) -> None:
        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "chat_panel",
            "Model selected from the session header.",
            payload={"model_name": model_name},
        )
        self.context.session_controller.set_model(model_name)
        self.context.status_controller.set_status(
            f"Model selected: {model_name}",
            level=STATUS_INFO,
        )
        self._workspace_dirty = True

    def _handle_loop_selected(self, loop_name: str) -> None:
        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "chat_panel",
            "Loop selected from the session header.",
            payload={"loop_name": loop_name},
        )
        self.context.session_controller.set_loop(loop_name)
        self.context.status_controller.set_status(
            f"Loop selected: {loop_name}",
            level=STATUS_INFO,
        )
        self._workspace_dirty = True

    def _resolve_hitl_gate(self, approval_id: str, approved: bool) -> None:
        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "workspace_panel",
            "User resolved a HITL gate.",
            payload={"approval_id": approval_id, "approved": approved},
        )
        self.context.agent_controller.resolve_hitl_gate(
            approval_id,
            approved,
            note="Resolved from Agent HUD.",
        )
        self.context.status_controller.set_status(
            "HITL gate approved. Agent resumed." if approved else "HITL gate rejected.",
            level=STATUS_BUSY if approved else STATUS_WARNING,
        )
        self._workspace_dirty = True

    def _run_tool(self, tool_id: str, arguments: dict) -> str:
        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "workspace_panel",
            "User requested tool execution.",
            payload={"tool_id": tool_id},
        )
        execution_id = self.context.tool_service.run_tool(tool_id, arguments)
        self.context.status_controller.set_status(
            f"Tool started: {tool_id}",
            level=STATUS_BUSY,
        )
        self._workspace_dirty = True
        return execution_id

    def _cancel_tool(self, execution_id: str) -> bool:
        cancelled = self.context.tool_service.cancel_tool(execution_id)
        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "workspace_panel",
            "User requested tool cancellation.",
            level="warning" if cancelled else "info",
            payload={"execution_id": execution_id, "cancel_requested": cancelled},
        )
        self.context.status_controller.set_status(
            "Tool cancellation requested." if cancelled else "Tool could not be cancelled.",
            level=STATUS_WARNING if cancelled else STATUS_INFO,
        )
        self._workspace_dirty = True
        return cancelled

    def _handle_task_error(self, task_result: TaskResult) -> None:
        chat_panel = self.context.panel_manager.get_panel(PRIMARY_PANEL_ID)
        chat_panel.append_message(
            "System",
            f"Background task failed: {task_result.error_message or 'Unknown error'}",
        )
        self.context.status_controller.set_status(
            "Task failed. See logs.",
            level=STATUS_ERROR,
            detail=task_result.error_message or "",
        )

    def _record_ui_interaction(
        self,
        source: str,
        summary: str,
        *,
        payload: dict | None = None,
        detail: str = "",
        level: str = STATUS_INFO,
    ) -> None:
        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            source,
            summary,
            detail=detail,
            level=level,
            payload=payload or {},
        )
        self._workspace_dirty = True

    def _toggle_theme(self) -> None:
        next_theme = (
            self.context.app_config.dark_theme
            if self._theme_name == self.context.app_config.theme
            else self.context.app_config.theme
        )
        self._theme_name = next_theme
        self.main_window.apply_theme(self._theme_name)

        for panel_id in [PRIMARY_PANEL_ID, SECONDARY_PANEL_ID]:
            self.context.panel_manager.get_panel(panel_id).apply_theme()

        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "main_window",
            "Theme toggled from the header.",
            payload={"theme_name": self._theme_name},
        )
        self.context.status_controller.set_status(
            f"Theme switched to {self._theme_name.replace('_', ' ')}.",
            level=STATUS_INFO,
        )

    def _toggle_workspace(self) -> None:
        visible = self.context.layout_manager.toggle_secondary_panel()
        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "main_window",
            "Workspace visibility toggled from the header.",
            payload={"visible": visible},
        )
        status_text = "Workspace shown." if visible else "Workspace hidden."
        self.context.status_controller.set_status(status_text, level=STATUS_INFO)

    def _save_snapshot(self) -> None:
        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "main_window",
            "Runtime snapshot saved from the header.",
        )
        snapshot_path = self.context.runtime_snapshot.write_snapshot("manual")
        self._last_snapshot_file = str(snapshot_path)
        self.context.status_controller.set_status(
            f"Snapshot saved: {snapshot_path.name}",
            level=STATUS_INFO,
        )

    def _trigger_crash_test(self) -> None:
        raise RuntimeError("Crash test requested from the toolbar.")

    def _handle_workspace_tab_selected(self, tab_id: str) -> None:
        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "workspace_panel",
            "Workspace tab selected.",
            payload={"tab_id": tab_id},
        )
        self._workspace_dirty = True

    def _refresh_workspace(self) -> None:
        workspace = self.context.panel_manager.get_panel(SECONDARY_PANEL_ID)
        workspace.refresh(
            agent_snapshot=self.context.agent_controller.get_snapshot(),
            tool_snapshot=self.context.tool_service.get_snapshot(),
            activity_events=self.context.activity_stream.recent_events(limit=120),
            data_hooks=self.context.data_hook_catalog.snapshot(),
            widget_tree=self.context.ui_registry.snapshot_tree(),
            widget_records=self.context.ui_registry.snapshot(),
        )
        self._workspace_dirty = False

    def _sync_session_header(self) -> None:
        chat_panel = self.context.panel_manager.get_panel(PRIMARY_PANEL_ID)
        snapshot = self.context.session_controller.get_snapshot()
        chat_panel.update_session_snapshot(snapshot)
        if self.session_dialog is not None:
            self.session_dialog.refresh(snapshot)

    def _render_status(self) -> None:
        self.main_window.render_status(self.context.status_controller.get_snapshot())

    def _capture_window_state(self):
        return capture_window_state(self.root)

    def _capture_ui_state(self):
        workspace_panel = self.context.panel_manager.get_panel(SECONDARY_PANEL_ID)
        workspace_state = workspace_panel.get_state()
        return self.context.layout_manager.capture_state(
            theme_name=self._theme_name,
            workspace_selected_tab=workspace_state.get("workspace_selected_tab"),
            inspector_selected_widget_id=workspace_state.get("inspector_selected_widget_id"),
        )

    def _capture_session_state(self):
        chat_panel = self.context.panel_manager.get_panel(PRIMARY_PANEL_ID)
        return SessionState(
            draft_text=chat_panel.get_draft_text(),
            last_active_panel=PRIMARY_PANEL_ID,
            last_snapshot_file=self._last_snapshot_file,
            active_session_id=self.context.session_controller.get_snapshot().active_session.session_id,
            selected_model=self.context.session_controller.get_snapshot().current_model,
            selected_loop=self.context.session_controller.get_snapshot().current_loop,
            use_echo=self.context.session_controller.get_snapshot().use_echo,
        )

    def _register_data_hooks(self) -> None:
        self.context.data_hook_catalog.register_hook(
            "shell.session_state",
            family="shell",
            producer="app_kernel",
            description="Current persisted session-facing shell state.",
            freshness="live",
            preview_provider=lambda: self._capture_session_state().to_dict(),
        )
        self.context.data_hook_catalog.register_hook(
            "session.header",
            family="session",
            producer="app_kernel",
            description="Current session header snapshot rendered in the chat panel.",
            freshness="live",
            preview_provider=lambda: self.context.session_controller.get_snapshot().to_dict(),
        )
        self.context.data_hook_catalog.register_hook(
            "shell.widget_registry",
            family="shell",
            producer="app_kernel",
            description="Structural widget registry snapshot summary.",
            freshness="live",
            preview_provider=lambda: {
                "widget_count": len(self.context.ui_registry.snapshot()),
                "root_count": len(self.context.ui_registry.snapshot_tree()),
            },
        )
        self.context.data_hook_catalog.register_hook(
            "shell.status",
            family="shell",
            producer="app_kernel",
            description="Current application status and task summary state.",
            freshness="live",
            preview_provider=lambda: self.context.status_controller.get_snapshot().to_dict(),
        )
        self.context.data_hook_catalog.register_hook(
            "shell.tasks",
            family="shell",
            producer="app_kernel",
            description="Recent background-task snapshot records.",
            freshness="live",
            preview_provider=lambda: self.context.task_manager.snapshot(),
        )
        self.context.data_hook_catalog.register_hook(
            "shell.panels",
            family="shell",
            producer="app_kernel",
            description="Mounted panel snapshot summary.",
            freshness="live",
            preview_provider=lambda: self.context.panel_manager.snapshot(),
        )
        self.context.data_hook_catalog.register_hook(
            "ui.chat_panel",
            family="ui",
            producer="app_kernel",
            description="Primary chat panel snapshot.",
            freshness="live",
            preview_provider=lambda: self.context.panel_manager.get_panel(PRIMARY_PANEL_ID).get_snapshot(),
        )
        self.context.data_hook_catalog.register_hook(
            "ui.workspace_panel",
            family="ui",
            producer="app_kernel",
            description="Secondary workspace snapshot across Agent HUD, Tools, Events, and Inspector.",
            freshness="live",
            preview_provider=lambda: self.context.panel_manager.get_panel(SECONDARY_PANEL_ID).get_snapshot(),
        )
        self.context.data_hook_catalog.register_hook(
            "runtime.activity_stream",
            family="runtime",
            producer="app_kernel",
            description="Recent normalized runtime activity.",
            freshness="live",
            preview_provider=lambda: self.context.activity_stream.recent_events(limit=12),
        )

    def _mark_workspace_dirty(self, _event) -> None:
        self._workspace_dirty = True

    def _mark_workspace_dirty_from_activity(self, _event: ActivityEvent) -> None:
        self._workspace_dirty = True

    def _consume_shutdown_request(self) -> bool:
        with self._shutdown_lock:
            return self._shutdown_requested

    def _shutdown(self) -> None:
        if self._is_shutting_down:
            return

        self._is_shutting_down = True
        self.context.lifecycle.set_phase("shutdown", f"Shutdown requested: {self._shutdown_reason}")
        self.context.status_controller.set_status("Shutting down...", level=STATUS_SHUTTING_DOWN)
        self._render_status()

        try:
            self._persist_state()
        except Exception:
            self.logger.exception("Failed to persist state during shutdown.")

        try:
            self.context.task_manager.shutdown(wait=False)
        except Exception:
            self.logger.exception("Failed to stop task manager cleanly.")

        try:
            self.context.panel_manager.dispose_all()
        except Exception:
            self.logger.exception("Failed to dispose panels cleanly.")

        try:
            if self.session_dialog is not None:
                self.session_dialog.close()
        except Exception:
            self.logger.exception("Failed to close session dialog cleanly.")

        try:
            if self.context.mindshard_adapter is not None:
                self.context.mindshard_adapter.close()
        except Exception:
            self.logger.exception("Failed to close Mindshard adapter cleanly.")

        if self.root is not None:
            self.root.destroy()

        self.context.lifecycle.set_phase("stopped", "Root window destroyed.")
        self.logger.info("Shutdown complete.")
        logging.shutdown()

    def _persist_state(self) -> None:
        window_state = self._capture_window_state()
        ui_state = self._capture_ui_state()
        session_state = self._capture_session_state()

        self.context.state_manager.save_window_state(window_state)
        self.context.state_manager.save_ui_state(ui_state)
        self.context.state_manager.save_session_state(session_state)

        snapshot_path = self.context.runtime_snapshot.write_snapshot("shutdown")
        self._last_snapshot_file = str(snapshot_path)

    def _open_session_manager_dialog(self) -> None:
        if self.session_dialog is None:
            self.session_dialog = SessionManagerDialog(
                self.root,
                self.theme_manager,
                actions=SessionDialogActions(
                    refresh_snapshot=self._dialog_refresh_session_snapshot,
                    save_current=self._dialog_save_current_session,
                    create_session=self._dialog_create_session,
                    load_session=self._dialog_load_session,
                    rename_session=self._dialog_rename_session,
                    delete_session=self._dialog_delete_session,
                    reset_current=self._dialog_reset_current_session,
                ),
                ui_registry=self.context.ui_registry,
            )
        self.context.activity_stream.append_event(
            ACTIVITY_UI_INTERACTION,
            "chat_panel",
            "Session manager opened from the chat header.",
        )
        self.session_dialog.open(self.context.session_controller.get_snapshot())
        self._workspace_dirty = True

    def _dialog_refresh_session_snapshot(self):
        return self.context.session_controller.refresh_snapshot()

    def _dialog_save_current_session(self, name: str):
        self.context.session_controller.save_current_session(name)
        self.context.status_controller.set_status("Current session saved.", level=STATUS_INFO)
        return self.context.session_controller.refresh_snapshot()

    def _dialog_create_session(self, name: str):
        self.context.session_controller.create_session(name)
        self._handle_session_switched("New session created.")
        return self.context.session_controller.refresh_snapshot()

    def _dialog_load_session(self, session_id: str):
        self.context.session_controller.load_session(session_id)
        self._handle_session_switched("Session loaded.")
        return self.context.session_controller.refresh_snapshot()

    def _dialog_rename_session(self, session_id: str, new_name: str):
        self.context.session_controller.rename_session(session_id, new_name)
        self.context.status_controller.set_status("Session renamed.", level=STATUS_INFO)
        return self.context.session_controller.refresh_snapshot()

    def _dialog_delete_session(self, session_id: str):
        active_id = self.context.session_controller.get_snapshot().active_session.session_id
        self.context.session_controller.delete_session(session_id)
        if session_id == active_id:
            self._handle_session_switched("Active session deleted. New session started.")
        else:
            self.context.status_controller.set_status("Session deleted.", level=STATUS_INFO)
        return self.context.session_controller.refresh_snapshot()

    def _dialog_reset_current_session(self):
        self.context.session_controller.reset_current_session()
        self._handle_session_switched("Current session reset.")
        return self.context.session_controller.refresh_snapshot()

    def _handle_session_switched(self, status_text: str) -> None:
        chat_panel = self.context.panel_manager.get_panel(PRIMARY_PANEL_ID)
        chat_panel.clear_transcript()
        chat_panel.append_message("System", status_text)
        self._last_agent_message_rendered = ""
        self._last_pending_approval_count = 0
        self.context.status_controller.set_status(status_text, level=STATUS_INFO)
        self._workspace_dirty = True


def launch(project_root: Path) -> None:
    paths = build_app_paths(project_root)
    logger = configure_logging(paths)
    context = build_app_context(paths)
    context.app_logger = logger

    try:
        kernel = AppKernel(context)
        kernel.start()
    except Exception as exc:
        logger.exception("Fatal startup failure.")
        write_crash_report(
            paths.crash_reports_dir,
            origin="startup",
            error_message=str(exc),
            traceback_text=traceback.format_exc(),
            snapshot_path=None,
        )
        raise
