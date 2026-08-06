"""
Owns: normalized widget registration records and live UI introspection snapshots.
Does not own: widget creation, panel mounting, or layout policy.
Collaborates with: panels, the app kernel, and the inspector panel.
"""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from dataclasses import dataclass, field
from typing import Any, Callable

from src.shell.constants import MAX_CONTENT_PREVIEW
from src.utils.time_utils import utc_timestamp

ContentGetter = Callable[[], str | None]


@dataclass
class RegisteredWidget:
    widget_id: str
    widget: tk.Misc
    role: str
    panel_id: str
    parent_id: str | None
    content_getter: ContentGetter | None = field(default=None, repr=False)
    children_ids: set[str] = field(default_factory=set)


class UIRegistry:
    def __init__(self, event_bus) -> None:
        self._logger = logging.getLogger("shell.registry")
        self._event_bus = event_bus
        self._lock = threading.Lock()
        self._records: dict[str, RegisteredWidget] = {}

    def register_widget(
        self,
        widget_id: str,
        widget: tk.Misc,
        *,
        role: str,
        panel_id: str,
        parent_id: str | None = None,
        content_getter: ContentGetter | None = None,
    ) -> None:
        with self._lock:
            if widget_id in self._records:
                raise ValueError(f"Widget id already registered: {widget_id}")

            entry = RegisteredWidget(
                widget_id=widget_id,
                widget=widget,
                role=role,
                panel_id=panel_id,
                parent_id=parent_id,
                content_getter=content_getter,
            )
            self._records[widget_id] = entry

            if parent_id and parent_id in self._records:
                self._records[parent_id].children_ids.add(widget_id)

        snapshot = self.get_widget_record(widget_id)
        self._logger.info("Widget registered. widget_id=%s role=%s", widget_id, role)
        self._event_bus.publish("widget_registered", snapshot or {"widget_id": widget_id})

    def unregister_widget(self, widget_id: str) -> None:
        with self._lock:
            entry = self._records.pop(widget_id, None)
            if entry is None:
                return
            if entry.parent_id and entry.parent_id in self._records:
                self._records[entry.parent_id].children_ids.discard(widget_id)

        self._logger.info("Widget unregistered. widget_id=%s", widget_id)
        self._event_bus.publish("widget_unregistered", {"widget_id": widget_id})

    def get_widget_record(self, widget_id: str) -> dict[str, Any] | None:
        with self._lock:
            entry = self._records.get(widget_id)
        if entry is None:
            return None
        return self._snapshot_entry(entry)

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            entries = list(self._records.values())

        entries.sort(key=lambda entry: entry.widget_id)
        return [self._snapshot_entry(entry) for entry in entries]

    def snapshot_tree(self) -> list[dict[str, Any]]:
        records = self.snapshot()
        by_id: dict[str, dict[str, Any]] = {}
        roots: list[dict[str, Any]] = []

        for record in records:
            node = dict(record)
            node["children"] = []
            by_id[record["widget_id"]] = node

        for record in records:
            node = by_id[record["widget_id"]]
            parent_id = record["parent_id"]
            if parent_id and parent_id in by_id:
                by_id[parent_id]["children"].append(node)
            else:
                roots.append(node)

        return roots

    def _snapshot_entry(self, entry: RegisteredWidget) -> dict[str, Any]:
        widget = entry.widget
        layout_manager = _safe_call(widget.winfo_manager, default="")
        return {
            "widget_id": entry.widget_id,
            "class": _safe_call(widget.winfo_class, default=widget.__class__.__name__),
            "role": entry.role,
            "panel_id": entry.panel_id,
            "parent_id": entry.parent_id,
            "children_ids": sorted(entry.children_ids),
            "layout_manager": layout_manager,
            "layout_info": _safe_layout_info(widget, layout_manager),
            "visible": bool(_safe_call(widget.winfo_ismapped, default=False)),
            "state": _safe_widget_state(widget),
            "content_preview": _safe_content_preview(entry.content_getter),
            "geometry": {
                "x": int(_safe_call(widget.winfo_x, default=0)),
                "y": int(_safe_call(widget.winfo_y, default=0)),
                "width": int(_safe_call(widget.winfo_width, default=0)),
                "height": int(_safe_call(widget.winfo_height, default=0)),
            },
            "updated_at": utc_timestamp(),
        }


def _safe_layout_info(widget: tk.Misc, layout_manager: str) -> dict[str, str]:
    try:
        if layout_manager == "grid":
            payload = widget.grid_info()
        elif layout_manager == "pack":
            payload = widget.pack_info()
        elif layout_manager == "place":
            payload = widget.place_info()
        else:
            payload = {}
    except tk.TclError:
        return {}

    return {str(key): str(value) for key, value in payload.items()}


def _safe_widget_state(widget: tk.Misc) -> str | None:
    try:
        return str(widget.cget("state"))
    except Exception:
        return None


def _safe_content_preview(content_getter: ContentGetter | None) -> str | None:
    if content_getter is None:
        return None

    try:
        content = content_getter() or ""
    except Exception:
        return "<unavailable>"

    if len(content) > MAX_CONTENT_PREVIEW:
        return f"{content[: MAX_CONTENT_PREVIEW - 3]}..."
    return content


def _safe_call(callback: Callable[[], Any], default: Any) -> Any:
    try:
        return callback()
    except Exception:
        return default
