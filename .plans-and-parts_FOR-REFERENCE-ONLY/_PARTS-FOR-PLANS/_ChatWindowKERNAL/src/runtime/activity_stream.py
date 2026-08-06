"""
Owns: normalized runtime activity records and subscription history.
Does not own: UI widgets, task execution, or event-bus coordination.
Collaborates with: agent host, tool service, and observability panels.
"""

from __future__ import annotations

import logging
import threading
import uuid
from collections import deque
from dataclasses import asdict, dataclass
from typing import Any, Callable

from src.shell.constants import MAX_ACTIVITY_EVENTS
from src.utils.time_utils import utc_timestamp

ActivityHandler = Callable[["ActivityEvent"], None]


@dataclass(frozen=True)
class ActivityEvent:
    event_id: str
    family: str
    source: str
    level: str
    summary: str
    detail: str
    payload: dict[str, Any]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ActivityStream:
    def __init__(self, max_history: int = MAX_ACTIVITY_EVENTS) -> None:
        self._logger = logging.getLogger("runtime.activity")
        self._history: deque[ActivityEvent] = deque(maxlen=max_history)
        self._subscribers: list[ActivityHandler] = []
        self._lock = threading.Lock()

    def append_event(
        self,
        family: str,
        source: str,
        summary: str,
        *,
        detail: str = "",
        level: str = "info",
        payload: dict[str, Any] | None = None,
    ) -> ActivityEvent:
        event = ActivityEvent(
            event_id=str(uuid.uuid4()),
            family=family,
            source=source,
            level=level,
            summary=summary,
            detail=detail,
            payload=payload or {},
            created_at=utc_timestamp(),
        )

        with self._lock:
            self._history.append(event)
            handlers = list(self._subscribers)

        self._logger.debug("Activity appended. family=%s source=%s", family, source)
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                self._logger.exception("Activity subscriber failed. family=%s", family)

        return event

    def subscribe(self, handler: ActivityHandler) -> None:
        with self._lock:
            self._subscribers.append(handler)

    def recent_events(
        self,
        *,
        limit: int | None = None,
        families: list[str] | None = None,
        levels: list[str] | None = None,
        sources: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            events = list(self._history)

        filtered = [
            event
            for event in events
            if _match_filters(event, families=families, levels=levels, sources=sources)
        ]
        if limit is not None:
            filtered = filtered[-limit:]
        return [event.to_dict() for event in filtered]


def _match_filters(
    event: ActivityEvent,
    *,
    families: list[str] | None,
    levels: list[str] | None,
    sources: list[str] | None,
) -> bool:
    if families and not any(event.family == family or event.family.startswith(f"{family}.") for family in families):
        return False
    if levels and event.level not in levels:
        return False
    if sources and event.source not in sources:
        return False
    return True
