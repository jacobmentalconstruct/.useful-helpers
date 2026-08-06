"""
Owns: visual status-bar composition and rendering.
Does not own: global status state, task execution, or lifecycle rules.
Collaborates with: the main window and status controller.
"""

from __future__ import annotations

from tkinter import ttk


class StatusBar(ttk.Frame):
    def __init__(self, parent) -> None:
        super().__init__(parent, style="Status.TFrame", padding=(16, 8))
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=1)

        self.status_label = ttk.Label(self, style="Status.Info.TLabel")
        self.status_label.grid(row=0, column=0, sticky="w")

        self.task_label = ttk.Label(self, style="StatusMeta.TLabel")
        self.task_label.grid(row=0, column=1, sticky="w", padx=(12, 0))

        self.meta_label = ttk.Label(self, style="StatusMeta.TLabel")
        self.meta_label.grid(row=0, column=2, sticky="e")

    def render(self, snapshot) -> None:
        style = {
            "busy": "Status.Busy.TLabel",
            "warning": "Status.Warning.TLabel",
            "error": "Status.Error.TLabel",
        }.get(snapshot.level, "Status.Info.TLabel")

        self.status_label.configure(text=snapshot.text, style=style)
        self.task_label.configure(text=snapshot.task_text or "Idle")
        self.meta_label.configure(text=snapshot.updated_at[11:19])
