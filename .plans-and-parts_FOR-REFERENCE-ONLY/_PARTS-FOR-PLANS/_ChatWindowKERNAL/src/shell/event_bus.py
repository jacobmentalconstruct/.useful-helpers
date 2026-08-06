"""
Owns: internal event publication, subscription, and recent event history.
Does not own: lifecycle decisions, UI mutation, or task execution.
Collaborates with: shell and UI components that need observable activity.
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from typing import Any, Callable

from src.shell.constants import MAX_RECENT_EVENTS
from src.utils.time_utils import utc_timestamp

EventHandler = Callable[["AppEvent"], None]


@dataclass(frozen=True)
class AppEvent:
    event_type: str
    payload: dict[str, Any]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventBus:
    def __init__(self, max_history: int = MAX_RECENT_EVENTS) -> None:
        self._logger = logging.getLogger("shell.events")
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._history: deque[AppEvent] = deque(maxlen=max_history)
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        with self._lock:
            self._subscribers[event_type].append(handler)
        self._logger.debug("Subscriber added. event_type=%s", event_type)

    def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> AppEvent:
        event = AppEvent(
            event_type=event_type,
            payload=payload or {},
            created_at=utc_timestamp(),
        )

        with self._lock:
            self._history.append(event)
            handlers = list(self._subscribers.get(event_type, []))
            wildcard_handlers = list(self._subscribers.get("*", []))

        self._logger.debug("Publishing event. event_type=%s", event_type)

        for handler in [*handlers, *wildcard_handlers]:
            try:
                handler(event)
            except Exception:
                self._logger.exception(
                    "Subscriber raised during event dispatch. event_type=%s",
                    event_type,
                )

        return event

    def recent_events(self, limit: int | None = None) -> list[dict[str, Any]]:
        with self._lock:
            history = list(self._history)

        if limit is not None:
            history = history[-limit:]

        return [event.to_dict() for event in history]
