"""
Owns: the chat-first paned window layout container and pane visibility mechanics.
Does not own: panel behavior, persistence files, or theme policy.
Collaborates with: the layout manager and main window.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class PanedShell(ttk.Frame):
    def __init__(self, parent) -> None:
        super().__init__(parent, style="Main.TFrame")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ttk.PanedWindow fails to remap a forgotten pane reliably on Windows/Tk,
        # so the shell uses tk.PanedWindow here and themes it explicitly.
        self.paned = tk.PanedWindow(
            self,
            orient=tk.HORIZONTAL,
            bd=0,
            relief="flat",
            sashwidth=10,
            showhandle=False,
            opaqueresize=True,
        )
        self.paned.grid(row=0, column=0, sticky="nsew")

        self.primary_host = ttk.Frame(self.paned, style="Surface.TFrame", padding=(0, 0))
        self.secondary_host = ttk.Frame(self.paned, style="SurfaceAlt.TFrame", padding=(0, 0))
        self.primary_host.grid_rowconfigure(0, weight=1)
        self.primary_host.grid_columnconfigure(0, weight=1)
        self.secondary_host.grid_rowconfigure(0, weight=1)
        self.secondary_host.grid_columnconfigure(0, weight=1)

        self.paned.add(self.primary_host, stretch="always")
        self.paned.add(self.secondary_host, minsize=240)

        self._secondary_visible = True
        self._secondary_width = 340

    def show_secondary(self) -> None:
        if self._secondary_visible:
            self._apply_secondary_width()
            return

        self.paned.add(self.secondary_host, minsize=240)
        self._secondary_visible = True
        self.after_idle(self._apply_secondary_width)

    def hide_secondary(self) -> None:
        if not self._secondary_visible:
            return
        self._secondary_width = self.get_secondary_width() or self._secondary_width
        self.paned.forget(self.secondary_host)
        self._secondary_visible = False

    def is_secondary_visible(self) -> bool:
        return self._secondary_visible

    def set_secondary_width(self, width: int) -> None:
        self._secondary_width = max(240, width)
        if self._secondary_visible:
            self.after_idle(self._apply_secondary_width)

    def get_secondary_width(self) -> int:
        if not self._secondary_visible:
            return self._secondary_width

        try:
            total_width = self.paned.winfo_width()
            sash_position = self.paned.sash_coord(0)[0]
        except Exception:
            return self._secondary_width

        width = total_width - sash_position
        if width <= 0:
            return self._secondary_width
        self._secondary_width = width
        return width

    def _apply_secondary_width(self) -> None:
        if not self._secondary_visible:
            return

        total_width = self.paned.winfo_width()
        if total_width <= 1:
            self.after(50, self._apply_secondary_width)
            return

        sash_position = max(240, total_width - self._secondary_width)
        try:
            self.paned.sash_place(0, sash_position, 1)
        except Exception:
            return

    def apply_theme(self, palette) -> None:
        self.paned.configure(bg=palette.border)
