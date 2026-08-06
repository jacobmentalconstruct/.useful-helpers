"""
Owns: the shared installable panel contract.
Does not own: shell orchestration, persistence files, or global status state.
Collaborates with: the panel manager and UI registry.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod


class BasePanel(ABC):
    def __init__(self, *, panel_id: str, title: str, parent_widget_id: str) -> None:
        self.panel_id = panel_id
        self.title = title
        self.parent_widget_id = parent_widget_id
        self.logger = logging.getLogger(f"ui.panels.{panel_id}")
        self.frame = None

    @abstractmethod
    def build(self, parent) -> None:
        raise NotImplementedError

    @abstractmethod
    def register_widgets(self, registry) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_state(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def restore_state(self, state: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_snapshot(self) -> dict:
        raise NotImplementedError

    def apply_theme(self) -> None:
        return

    def dispose(self) -> None:
        if self.frame is not None:
            self.frame.destroy()
            self.frame = None
