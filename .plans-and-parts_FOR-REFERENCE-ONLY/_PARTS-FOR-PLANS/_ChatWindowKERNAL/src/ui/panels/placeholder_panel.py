"""
Owns: a simple secondary panel surface when the inspector is disabled.
Does not own: registry logic, persistence behavior, or task execution.
Collaborates with: the panel manager and UI registry.
"""

from __future__ import annotations

from tkinter import ttk

from src.ui.panels.base_panel import BasePanel
from src.ui.registry_hooks import register_widget


class PlaceholderPanel(BasePanel):
    def __init__(self) -> None:
        super().__init__(
            panel_id="placeholder",
            title="Extension Rail",
            parent_widget_id="main.secondary_host",
        )
        self._message_label = None

    def build(self, parent) -> None:
        self.frame = ttk.Frame(parent, style="SurfaceAlt.TFrame", padding=(16, 16))
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)

        title_label = ttk.Label(self.frame, text=self.title, style="PanelTitle.TLabel")
        title_label.grid(row=0, column=0, sticky="w")

        self._message_label = ttk.Label(
            self.frame,
            text="The side rail is ready for future tools, logs, or memory panels.",
            style="Muted.TLabel",
            wraplength=260,
            justify="left",
        )
        self._message_label.grid(row=1, column=0, sticky="nw", pady=(12, 0))

    def register_widgets(self, registry) -> None:
        register_widget(
            registry,
            widget_id="placeholder.panel",
            widget=self.frame,
            role="placeholder_panel",
            panel_id=self.panel_id,
            parent_id=self.parent_widget_id,
        )
        register_widget(
            registry,
            widget_id="placeholder.message",
            widget=self._message_label,
            role="placeholder_message",
            panel_id=self.panel_id,
            parent_id="placeholder.panel",
            content_getter=lambda: self._message_label.cget("text"),
        )

    def get_state(self) -> dict:
        return {}

    def restore_state(self, state: dict) -> None:
        return

    def get_snapshot(self) -> dict:
        return {"panel_id": self.panel_id, "message": self._message_label.cget("text")}
