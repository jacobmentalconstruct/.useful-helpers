"""
Owns: host-facing session/model/loop state and session-management actions.
Does not own: vendored runtime imports, Tk widgets, or tool execution.
Collaborates with: the Mindshard adapter, task manager, and chat/session UI.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from src.runtime.activity_stream import ActivityStream
from src.runtime.agent_host.system_probe import collect_hardware_snapshot
from src.runtime.adapters.mindshard_adapter import MindshardAdapter
from src.runtime.contracts.session import (
    HardwareSnapshot,
    SessionController,
    SessionInfoSnapshot,
    SessionSnapshot,
)
from src.runtime.data_hooks import DataHookCatalog
from src.shell.constants import ACTIVITY_SYSTEM_ERROR, ACTIVITY_SYSTEM_STATUS
from src.shell.task_manager import TaskManager, TaskResult
from src.utils.time_utils import utc_timestamp


_PROBE_INTERVAL_SECONDS = 8.0


class HostSessionController(SessionController):
    def __init__(
        self,
        adapter: MindshardAdapter,
        task_manager: TaskManager,
        activity_stream: ActivityStream,
        data_hook_catalog: DataHookCatalog,
    ) -> None:
        self._adapter = adapter
        self._task_manager = task_manager
        self._activity_stream = activity_stream
        self._data_hook_catalog = data_hook_catalog
        self._logger = logging.getLogger("runtime.session")
        self._lock = threading.Lock()
        self._probe_task_active = False
        self._last_probe_started_at = 0.0
        self._snapshot = SessionSnapshot(
            active_session=SessionInfoSnapshot(
                session_id="",
                name="",
                created_at="",
                updated_at="",
                message_count=0,
            ),
            updated_at=utc_timestamp(),
        )

        self._refresh_session_snapshot()
        self._schedule_probe(force=True)
        self._register_data_hooks()

    def get_snapshot(self) -> SessionSnapshot:
        self._schedule_probe()
        with self._lock:
            return self._snapshot

    def refresh_snapshot(self) -> SessionSnapshot:
        self._refresh_session_snapshot()
        with self._lock:
            return self._snapshot

    def set_model(self, model_name: str) -> None:
        self._adapter.switch_model(model_name)
        self._refresh_session_snapshot()
        self._schedule_probe(force=True)
        self._activity_stream.append_event(
            ACTIVITY_SYSTEM_STATUS,
            "session_controller",
            "Model selection updated.",
            payload={"model_name": model_name},
        )

    def set_loop(self, loop_name: str) -> None:
        self._adapter.switch_loop(loop_name)
        self._refresh_session_snapshot()
        self._activity_stream.append_event(
            ACTIVITY_SYSTEM_STATUS,
            "session_controller",
            "Loop selection updated.",
            payload={"loop_name": loop_name},
        )

    def save_current_session(self, name: str = "") -> SessionInfoSnapshot:
        info = self._to_session_info(self._adapter.save_current_session(name))
        self._refresh_session_snapshot()
        return info

    def create_session(self, name: str = "") -> SessionInfoSnapshot:
        info = self._to_session_info(self._adapter.new_session(name))
        self._refresh_session_snapshot()
        return info

    def load_session(self, session_id: str) -> SessionInfoSnapshot:
        info = self._to_session_info(self._adapter.load_session(session_id))
        self._refresh_session_snapshot()
        return info

    def rename_session(self, session_id: str, new_name: str) -> SessionInfoSnapshot:
        info = self._to_session_info(self._adapter.rename_session(session_id, new_name))
        self._refresh_session_snapshot()
        return info

    def delete_session(self, session_id: str) -> int:
        removed = self._adapter.delete_session(session_id)
        self._refresh_session_snapshot()
        return removed

    def reset_current_session(self) -> SessionInfoSnapshot:
        info = self._to_session_info(self._adapter.reset_session())
        self._refresh_session_snapshot()
        return info

    def _refresh_session_snapshot(self) -> None:
        current_info = self._to_session_info(self._adapter.current_session_info())
        sessions = [self._to_session_info(item) for item in self._adapter.list_sessions()]
        runtime = self._adapter.runtime_status()

        with self._lock:
            self._snapshot = SessionSnapshot(
                active_session=current_info,
                available_sessions=sessions,
                available_models=self._adapter.list_models(),
                available_loops=self._adapter.list_loops(),
                current_model=runtime["model_name"],
                model_status=runtime["model_status"],
                current_loop=runtime["loop_name"],
                use_echo=runtime["use_echo"],
                hardware=self._snapshot.hardware,
                updated_at=utc_timestamp(),
            )

    def _schedule_probe(self, *, force: bool = False) -> None:
        with self._lock:
            if self._probe_task_active:
                return
            if not force and (time.monotonic() - self._last_probe_started_at) < _PROBE_INTERVAL_SECONDS:
                return
            self._probe_task_active = True
            self._last_probe_started_at = time.monotonic()

        self._task_manager.submit_task(
            "session_probe",
            _collect_probe_payload,
            self._adapter,
            on_success=self._apply_probe_payload,
            on_error=self._handle_probe_error,
        )

    def _apply_probe_payload(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._probe_task_active = False
            self._snapshot = SessionSnapshot(
                active_session=self._snapshot.active_session,
                available_sessions=self._snapshot.available_sessions,
                available_models=payload["available_models"],
                available_loops=self._snapshot.available_loops,
                current_model=self._snapshot.current_model,
                model_status=payload["model_status"],
                current_loop=self._snapshot.current_loop,
                use_echo=self._snapshot.use_echo,
                hardware=payload["hardware"],
                updated_at=utc_timestamp(),
            )

    def _handle_probe_error(self, task_result: TaskResult) -> None:
        with self._lock:
            self._probe_task_active = False
        self._activity_stream.append_event(
            ACTIVITY_SYSTEM_ERROR,
            "session_controller",
            "Runtime environment probe failed.",
            level="error",
            detail=task_result.error_message or "",
        )
        self._logger.error("Session probe failed: %s", task_result.error_message or "Unknown error")

    def _register_data_hooks(self) -> None:
        self._data_hook_catalog.register_hook(
            "session.snapshot",
            family="session",
            producer="session_controller",
            description="Current session, model, loop, and hardware header state.",
            freshness="live",
            preview_provider=lambda: self.get_snapshot().to_dict(),
        )
        self._data_hook_catalog.register_hook(
            "session.hardware",
            family="session",
            producer="session_controller",
            description="Latest hardware summary for the chat header.",
            freshness="live",
            preview_provider=lambda: self.get_snapshot().hardware.to_dict(),
        )

    @staticmethod
    def _to_session_info(payload: dict[str, Any] | None) -> SessionInfoSnapshot:
        payload = payload or {}
        return SessionInfoSnapshot(
            session_id=str(payload.get("session_id", "")),
            name=str(payload.get("name", "")),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", "")),
            message_count=int(payload.get("message_count", 0)),
        )


def _collect_probe_payload(adapter: MindshardAdapter) -> dict[str, Any]:
    hardware = collect_hardware_snapshot()
    status = adapter.runtime_status(refresh_models=False)
    return {
        "hardware": hardware,
        "available_models": adapter.list_models(refresh=False),
        "model_status": status["model_status"],
    }
