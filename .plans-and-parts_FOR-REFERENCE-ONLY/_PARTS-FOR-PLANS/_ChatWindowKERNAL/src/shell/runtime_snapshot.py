"""
Owns: normalized runtime snapshot composition and snapshot file emission.
Does not own: widget mutation, task execution, or crash policy.
Collaborates with: the app kernel, registry, task manager, and crash handler.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable

from src.shell.app_context import AppContext
from src.utils.json_utils import write_json_file
from src.utils.time_utils import compact_timestamp, utc_timestamp

StateProvider = Callable[[], Any]


class RuntimeSnapshotBuilder:
    def __init__(
        self,
        context: AppContext,
        *,
        window_state_provider: StateProvider,
        ui_state_provider: StateProvider,
        session_state_provider: StateProvider,
    ) -> None:
        self._context = context
        self._window_state_provider = window_state_provider
        self._ui_state_provider = ui_state_provider
        self._session_state_provider = session_state_provider
        self._logger = logging.getLogger("shell.snapshot")

    def build_snapshot(self) -> dict[str, Any]:
        event_bus = self._require("event_bus", self._context.event_bus)
        status_controller = self._require("status_controller", self._context.status_controller)
        task_manager = self._require("task_manager", self._context.task_manager)
        ui_registry = self._require("ui_registry", self._context.ui_registry)
        panel_manager = self._require("panel_manager", self._context.panel_manager)
        lifecycle = self._require("lifecycle", self._context.lifecycle)
        activity_stream = self._require("activity_stream", self._context.activity_stream)
        data_hook_catalog = self._require("data_hook_catalog", self._context.data_hook_catalog)
        agent_controller = self._require("agent_controller", self._context.agent_controller)
        session_controller = self._require("session_controller", self._context.session_controller)
        tool_service = self._require("tool_service", self._context.tool_service)
        agent_snapshot = agent_controller.get_snapshot()
        session_snapshot = session_controller.get_snapshot()
        tool_snapshot = tool_service.get_snapshot()

        snapshot = {
            "captured_at": utc_timestamp(),
            "app": {
                "app_id": self._context.app_config.app_id,
                "app_name": self._context.app_config.app_name,
            },
            "lifecycle": lifecycle.get_snapshot().to_dict(),
            "window_state": _serialize(self._window_state_provider()),
            "ui_state": _serialize(self._ui_state_provider()),
            "session_state": _serialize(self._session_state_provider()),
            "session_snapshot": session_snapshot.to_dict(),
            "status": status_controller.get_snapshot().to_dict(),
            "panels": panel_manager.snapshot(),
            "active_tasks": task_manager.snapshot(),
            "shell_events": event_bus.recent_events(limit=25),
            "activity_stream": activity_stream.recent_events(limit=100),
            "data_hooks": data_hook_catalog.snapshot(),
            "agent_snapshot": agent_snapshot.to_dict(),
            "tool_snapshot": tool_snapshot.to_dict(),
            "pending_hitl": [gate.to_dict() for gate in agent_snapshot.pending_approvals],
            "recent_errors": [
                event
                for event in activity_stream.recent_events(limit=100)
                if event["family"] in {"system.error", "tool.failed"}
            ],
            "widget_registry": {
                "records": ui_registry.snapshot(),
                "tree": ui_registry.snapshot_tree(),
            },
        }
        self._logger.debug("Runtime snapshot composed.")
        return snapshot

    def write_snapshot(self, label: str = "runtime") -> Path:
        snapshot = self.build_snapshot()
        output_path = self._context.paths.snapshots_dir / f"{label}_{compact_timestamp()}.json"
        write_json_file(output_path, snapshot)
        self._logger.info("Runtime snapshot written. path=%s", output_path)
        return output_path

    @staticmethod
    def _require(name: str, value: Any) -> Any:
        if value is None:
            raise RuntimeError(f"RuntimeSnapshotBuilder missing dependency: {name}")
        return value


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value
