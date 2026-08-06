"""
Owns: root-window geometry application and capture helpers.
Does not own: persistence files, layout decisions, or lifecycle orchestration.
Collaborates with: the app kernel and state manager.
"""

from __future__ import annotations

import tkinter as tk

from src.shell.state_manager import WindowState


def apply_window_state(
    root: tk.Tk,
    state: WindowState,
    *,
    min_width: int,
    min_height: int,
) -> None:
    root.minsize(min_width, min_height)

    geometry = f"{state.width}x{state.height}"
    if state.x is not None and state.y is not None:
        geometry = f"{geometry}+{state.x}+{state.y}"
    root.geometry(geometry)
    root.update_idletasks()

    if state.maximized:
        try:
            root.state("zoomed")
        except tk.TclError:
            pass


def capture_window_state(root: tk.Tk) -> WindowState:
    maximized = root.state() == "zoomed"
    return WindowState(
        x=root.winfo_x(),
        y=root.winfo_y(),
        width=max(root.winfo_width(), root.winfo_reqwidth()),
        height=max(root.winfo_height(), root.winfo_reqheight()),
        maximized=maximized,
    )
