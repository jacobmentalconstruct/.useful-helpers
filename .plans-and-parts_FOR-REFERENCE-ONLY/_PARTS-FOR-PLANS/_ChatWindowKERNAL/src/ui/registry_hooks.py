"""
Owns: consistent UI-to-registry registration calls for semantic widget records.
Does not own: registry storage, panel behavior, or widget creation.
Collaborates with: panels, the main window, and the UI registry.
"""

from __future__ import annotations


def register_widget(
    registry,
    *,
    widget_id: str,
    widget,
    role: str,
    panel_id: str,
    parent_id: str | None = None,
    content_getter=None,
) -> None:
    registry.register_widget(
        widget_id,
        widget,
        role=role,
        panel_id=panel_id,
        parent_id=parent_id,
        content_getter=content_getter,
    )
