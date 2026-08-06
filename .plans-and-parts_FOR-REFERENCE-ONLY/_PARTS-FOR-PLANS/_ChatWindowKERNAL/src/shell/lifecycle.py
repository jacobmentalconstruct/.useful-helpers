"""
Owns: lifecycle phase tracking for startup, ready, shutdown, and crash transitions.
Does not own: actual startup work, widget creation, or persistence details.
Collaborates with: the app kernel, status controller, and runtime snapshots.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass

from src.utils.time_utils import utc_timestamp


@dataclass(frozen=True)
class LifecycleSnapshot:
    phase: str
    detail: str
    updated_at: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class LifecycleManager:
    def __init__(self, event_bus) -> None:
        self._event_bus = event_bus
        self._logger = logging.getLogger("shell.lifecycle")
        self._snapshot = LifecycleSnapshot(
            phase="created",
            detail="Kernel constructed.",
            updated_at=utc_timestamp(),
        )

    def set_phase(self, phase: str, detail: str) -> LifecycleSnapshot:
        self._snapshot = LifecycleSnapshot(
            phase=phase,
            detail=detail,
            updated_at=utc_timestamp(),
        )
        self._logger.info("Lifecycle phase changed. phase=%s", phase)
        self._event_bus.publish("lifecycle_changed", self._snapshot.to_dict())
        return self._snapshot

    def get_snapshot(self) -> LifecycleSnapshot:
        return self._snapshot
