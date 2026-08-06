"""
Owns: app-wide status text, severity, and task summary state.
Does not own: status bar widgets, task execution, or shutdown behavior.
Collaborates with: the app kernel, task manager, and status bar.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import asdict, dataclass

from src.runtime.activity_stream import ActivityStream
from src.shell.constants import ACTIVITY_SYSTEM_STATUS
from src.shell.constants import STATUS_INFO
from src.utils.time_utils import utc_timestamp


@dataclass(frozen=True)
class StatusSnapshot:
    text: str
    level: str
    task_text: str
    detail: str
    updated_at: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class StatusController:
    def __init__(self, event_bus, activity_stream: ActivityStream | None = None) -> None:
        self._event_bus = event_bus
        self._activity_stream = activity_stream
        self._logger = logging.getLogger("shell.status")
        self._lock = threading.Lock()
        self._snapshot = StatusSnapshot(
            text="Bootstrapping...",
            level=STATUS_INFO,
            task_text="",
            detail="",
            updated_at=utc_timestamp(),
        )

    def set_status(self, text: str, level: str = STATUS_INFO, detail: str = "") -> StatusSnapshot:
        with self._lock:
            self._snapshot = StatusSnapshot(
                text=text,
                level=level,
                task_text=self._snapshot.task_text,
                detail=detail,
                updated_at=utc_timestamp(),
            )
            snapshot = self._snapshot

        self._logger.info("Status updated. level=%s text=%s", level, text)
        self._event_bus.publish("status_changed", snapshot.to_dict())
        if self._activity_stream is not None:
            self._activity_stream.append_event(
                ACTIVITY_SYSTEM_STATUS,
                "status_controller",
                text,
                detail=detail,
                level=level,
                payload=snapshot.to_dict(),
            )
        return snapshot

    def set_task_summary(self, task_text: str) -> StatusSnapshot:
        with self._lock:
            self._snapshot = StatusSnapshot(
                text=self._snapshot.text,
                level=self._snapshot.level,
                task_text=task_text,
                detail=self._snapshot.detail,
                updated_at=utc_timestamp(),
            )
            snapshot = self._snapshot

        self._logger.debug("Task summary updated. task_text=%s", task_text)
        self._event_bus.publish("status_changed", snapshot.to_dict())
        return snapshot

    def get_snapshot(self) -> StatusSnapshot:
        with self._lock:
            return self._snapshot
