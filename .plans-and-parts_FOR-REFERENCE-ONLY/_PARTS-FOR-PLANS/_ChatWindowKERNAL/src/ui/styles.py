"""
Owns: theme palettes and ttk/tk styling for the installed shell.
Does not own: layout state, panel behavior, or persistence decisions.
Collaborates with: the main window and panels that need themed widgets.
"""

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk

from src.shell.constants import THEME_CINDER_TIDE, THEME_HARBOR_MIST


@dataclass(frozen=True)
class ThemePalette:
    name: str
    background: str
    surface: str
    surface_alt: str
    header: str
    status: str
    border: str
    text: str
    muted_text: str
    accent: str
    accent_strong: str
    accent_text: str
    input_bg: str
    transcript_bg: str
    selection: str
    success: str
    warning: str
    error: str


PALETTES: dict[str, ThemePalette] = {
    THEME_HARBOR_MIST: ThemePalette(
        name=THEME_HARBOR_MIST,
        background="#ECF0EB",
        surface="#F7F4EE",
        surface_alt="#E2EAE6",
        header="#DDE7E2",
        status="#D9E2DC",
        border="#C7D2CC",
        text="#24313A",
        muted_text="#5C6A72",
        accent="#4C7C74",
        accent_strong="#D08A4E",
        accent_text="#F7F4EE",
        input_bg="#FBFAF7",
        transcript_bg="#F4F7F5",
        selection="#B8D3CB",
        success="#4F7A5C",
        warning="#B07A3C",
        error="#A85757",
    ),
    THEME_CINDER_TIDE: ThemePalette(
        name=THEME_CINDER_TIDE,
        background="#161C22",
        surface="#1F2830",
        surface_alt="#28333C",
        header="#11171C",
        status="#13191F",
        border="#36424C",
        text="#E6E2D9",
        muted_text="#9CA8B2",
        accent="#59B0A7",
        accent_strong="#D68A5D",
        accent_text="#10161B",
        input_bg="#202A31",
        transcript_bg="#1B232A",
        selection="#355057",
        success="#6AB07A",
        warning="#D7A55A",
        error="#D17373",
    ),
}


class ThemeManager:
    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._style = ttk.Style(root)
        self._style.theme_use("clam")
        self._current = PALETTES[THEME_HARBOR_MIST]

    def apply(self, theme_name: str) -> ThemePalette:
        palette = PALETTES.get(theme_name, PALETTES[THEME_HARBOR_MIST])
        self._current = palette

        self._root.configure(background=palette.background)
        self._configure_base_styles(palette)
        self._configure_button_styles(palette)
        self._configure_tree_styles(palette)
        self._configure_option_database(palette)
        return palette

    def current_palette(self) -> ThemePalette:
        return self._current

    def configure_text(self, widget: tk.Text, *, variant: str) -> None:
        palette = self._current
        background = palette.input_bg if variant == "input" else palette.transcript_bg
        widget.configure(
            background=background,
            foreground=palette.text,
            insertbackground=palette.accent,
            selectbackground=palette.selection,
            selectforeground=palette.text,
            highlightthickness=1,
            highlightbackground=palette.border,
            highlightcolor=palette.accent,
            relief="flat",
            borderwidth=0,
        )

    def _configure_base_styles(self, palette: ThemePalette) -> None:
        self._style.configure(".", background=palette.background, foreground=palette.text)
        self._style.configure("TFrame", background=palette.background)
        self._style.configure("Main.TFrame", background=palette.background)
        self._style.configure("Surface.TFrame", background=palette.surface)
        self._style.configure("SurfaceAlt.TFrame", background=palette.surface_alt)
        self._style.configure("Header.TFrame", background=palette.header)
        self._style.configure("Status.TFrame", background=palette.status)

        self._style.configure(
            "TLabel",
            background=palette.background,
            foreground=palette.text,
            font=("Segoe UI", 10),
        )
        self._style.configure(
            "HeaderTitle.TLabel",
            background=palette.header,
            foreground=palette.text,
            font=("Segoe UI Semibold", 15),
        )
        self._style.configure(
            "HeaderMeta.TLabel",
            background=palette.header,
            foreground=palette.muted_text,
            font=("Segoe UI", 9),
        )
        self._style.configure(
            "PanelTitle.TLabel",
            background=palette.surface,
            foreground=palette.text,
            font=("Segoe UI Semibold", 12),
        )
        self._style.configure(
            "Muted.TLabel",
            background=palette.surface,
            foreground=palette.muted_text,
            font=("Segoe UI", 9),
        )
        self._style.configure(
            "Status.Info.TLabel",
            background=palette.status,
            foreground=palette.text,
            font=("Segoe UI Semibold", 9),
        )
        self._style.configure(
            "Status.Busy.TLabel",
            background=palette.status,
            foreground=palette.accent,
            font=("Segoe UI Semibold", 9),
        )
        self._style.configure(
            "Status.Warning.TLabel",
            background=palette.status,
            foreground=palette.warning,
            font=("Segoe UI Semibold", 9),
        )
        self._style.configure(
            "Status.Error.TLabel",
            background=palette.status,
            foreground=palette.error,
            font=("Segoe UI Semibold", 9),
        )
        self._style.configure(
            "StatusMeta.TLabel",
            background=palette.status,
            foreground=palette.muted_text,
            font=("Segoe UI", 9),
        )

    def _configure_button_styles(self, palette: ThemePalette) -> None:
        self._style.configure(
            "Accent.TButton",
            background=palette.accent,
            foreground=palette.accent_text,
            bordercolor=palette.accent,
            focuscolor=palette.accent,
            padding=(12, 8),
            font=("Segoe UI Semibold", 10),
        )
        self._style.map(
            "Accent.TButton",
            background=[("active", palette.accent_strong), ("pressed", palette.accent_strong)],
            foreground=[("disabled", palette.muted_text)],
        )
        self._style.configure(
            "Ghost.TButton",
            background=palette.surface_alt,
            foreground=palette.text,
            bordercolor=palette.border,
            focuscolor=palette.accent,
            padding=(12, 8),
            font=("Segoe UI", 10),
        )
        self._style.map(
            "Ghost.TButton",
            background=[("active", palette.header), ("pressed", palette.header)],
            foreground=[("disabled", palette.muted_text)],
        )

    def _configure_tree_styles(self, palette: ThemePalette) -> None:
        self._style.configure(
            "Treeview",
            background=palette.surface,
            fieldbackground=palette.surface,
            foreground=palette.text,
            bordercolor=palette.border,
            rowheight=24,
        )
        self._style.map("Treeview", background=[("selected", palette.selection)])
        self._style.configure(
            "Treeview.Heading",
            background=palette.surface_alt,
            foreground=palette.text,
            bordercolor=palette.border,
            font=("Segoe UI Semibold", 9),
        )

    def _configure_option_database(self, palette: ThemePalette) -> None:
        self._root.option_add("*Text.font", ("Cascadia Mono", 10))
        self._root.option_add("*Text.Background", palette.input_bg)
        self._root.option_add("*Text.Foreground", palette.text)
