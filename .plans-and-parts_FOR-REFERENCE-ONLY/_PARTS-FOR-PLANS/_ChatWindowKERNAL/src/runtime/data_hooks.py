"""
Owns: registration and snapshotting of inspectable data producers.
Does not own: the underlying runtime state or UI rendering.
Collaborates with: shell snapshots, agent host, tool service, and workspace panels.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Any, Callable

from src.shell.constants import MAX_CONTENT_PREVIEW, MAX_DATA_HOOKS
from src.utils.time_utils import utc_timestamp

HookProvider = Callable[[], Any]


@dataclass
class _HookRecord:
    hook_id: str
    family: str
    producer: str
    description: str
    freshness: str
    preview_provider: HookProvider


class DataHookCatalog:
    def __init__(self, max_hooks: int = MAX_DATA_HOOKS) -> None:
        self._logger = logging.getLogger("runtime.data_hooks")
        self._max_hooks = max_hooks
        self._hooks: dict[str, _HookRecord] = {}
        self._lock = threading.Lock()

    def register_hook(
        self,
        hook_id: str,
        *,
        family: str,
        producer: str,
        description: str,
        freshness: str,
        preview_provider: HookProvider,
    ) -> None:
        with self._lock:
            if hook_id not in self._hooks and len(self._hooks) >= self._max_hooks:
                raise RuntimeError("DataHookCatalog is at capacity.")
            self._hooks[hook_id] = _HookRecord(
                hook_id=hook_id,
                family=family,
                producer=producer,
                description=description,
                freshness=freshness,
                preview_provider=preview_provider,
            )
        self._logger.debug("Data hook registered. hook_id=%s", hook_id)

    def unregister_hook(self, hook_id: str) -> None:
        with self._lock:
            self._hooks.pop(hook_id, None)
        self._logger.debug("Data hook unregistered. hook_id=%s", hook_id)

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            hooks = list(self._hooks.values())

        hooks.sort(key=lambda hook: hook.hook_id)
        return [self._snapshot_hook(hook) for hook in hooks]

    def get_hook_snapshot(self, hook_id: str) -> dict[str, Any] | None:
        with self._lock:
            hook = self._hooks.get(hook_id)
        if hook is None:
            return None
        return self._snapshot_hook(hook)

    def _snapshot_hook(self, hook: _HookRecord) -> dict[str, Any]:
        return {
            "hook_id": hook.hook_id,
            "family": hook.family,
            "producer": hook.producer,
            "description": hook.description,
            "freshness": hook.freshness,
            "preview": _safe_preview(hook.preview_provider),
            "updated_at": utc_timestamp(),
        }


def _safe_preview(provider: HookProvider) -> Any:
    try:
        value = provider()
    except Exception as exc:
        return {"error": str(exc)}

    if isinstance(value, str):
        return value if len(value) <= MAX_CONTENT_PREVIEW else f"{value[: MAX_CONTENT_PREVIEW - 3]}..."
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return value[:12]
    if isinstance(value, dict):
        return {key: value[key] for key in list(value.keys())[:12]}
    return repr(value)
