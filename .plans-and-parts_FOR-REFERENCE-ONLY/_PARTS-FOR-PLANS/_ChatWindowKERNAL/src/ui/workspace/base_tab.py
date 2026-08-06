"""
Owns: the shared interface for workspace tab views.
Does not own: runtime state, panel orchestration, or persistence files.
Collaborates with: the workspace panel and UI registry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class WorkspaceTabView(ABC):
    def __init__(self, *, tab_id: str, title: str, parent_widget_id: str) -> None:
        self.tab_id = tab_id
        self.title = title
        self.parent_widget_id = parent_widget_id
        self.frame = None

    @abstractmethod
    def build(self, parent) -> None:
        raise NotImplementedError

    @abstractmethod
    def register_widgets(self, registry) -> None:
        raise NotImplementedError

    def refresh(self, **_kwargs) -> None:
        return

    def restore_state(self, _state: dict) -> None:
        return

    def get_state(self) -> dict:
        return {}

    def get_snapshot(self) -> dict:
        return {}

    def apply_theme(self) -> None:
        return
