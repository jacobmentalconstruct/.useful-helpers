"""
FILE:       src/lib/theme.py
ROLE:       Suite visual identity for the human entrance.
DOMAIN:     lib
DOES:       Expose the palette + fonts and apply_style(): a ttk.Style (clam base) implementing
            the suite dark theme on a Tk root, per THEME_SPEC ("Midnight Blue").
DEPENDS ON: (stdlib) tkinter, tkinter.ttk
WIRES TO:   used by ui.app_ui, ui.registry_view
NOTES:      Palette re-homed from the legacy suite THEME_SPEC v1.0. Widget rules honored:
            clam base, hover maps to the accent, insertbackground white so the caret is
            visible on dark fields, listbox/canvas backgrounds set explicitly.
"""
from __future__ import annotations

# Ratified palette (THEME_SPEC v1.0).
PALETTE = {
    "bg_primary": "#1e1e2f",     # main window / modal background
    "bg_secondary": "#151521",   # listboxes, text areas, inset regions
    "widget_surface": "#2a2a3f", # buttons, toolbars (pre-interaction)
    "accent": "#007ACC",         # selection, hover, create actions
    "status": "#00FF00",         # terminal/success text
    "text": "#E7EDF4",
    "muted": "#97A4B3",
    "border": "#333333",
    "danger": "#C23621",
}

FONT_UI = ("Segoe UI", 9)
FONT_UI_BOLD = ("Segoe UI", 10, "bold")
FONT_MONO = ("Consolas", 9)

# Authority badge colors (Observe calm, Sandbox caution, Apply hot).
AUTHORITY_COLORS = {"Observe": "#89D6A0", "Sandbox": "#f1c40f", "Apply": "#e67e22"}


def apply_style(root) -> None:
    """Apply the suite dark theme to a Tk root + ttk.Style (clam base)."""
    from tkinter import ttk

    p = PALETTE
    root.configure(bg=p["bg_primary"])
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=p["bg_primary"], foreground=p["text"],
                    fieldbackground=p["bg_secondary"], font=FONT_UI)
    style.configure("TFrame", background=p["bg_primary"])
    style.configure("TLabel", background=p["bg_primary"], foreground=p["text"])
    style.configure("Muted.TLabel", foreground=p["muted"])
    style.configure("Heading.TLabel", font=FONT_UI_BOLD)
    style.configure("TButton", background=p["widget_surface"], foreground=p["text"],
                    borderwidth=0, padding=(10, 5))
    style.map("TButton",
              background=[("active", p["accent"]), ("disabled", p["bg_secondary"])],
              foreground=[("disabled", p["muted"])])
    style.configure("Accent.TButton", background=p["accent"], foreground="#ffffff")
    style.map("Accent.TButton", background=[("active", "#1a8ad4")])
    style.configure("TEntry", fieldbackground=p["bg_secondary"], foreground=p["text"],
                    insertcolor="#ffffff", bordercolor=p["border"])
    style.configure("TCheckbutton", background=p["bg_primary"], foreground=p["text"])
    style.map("TCheckbutton", background=[("active", p["bg_primary"])])
    style.configure("TCombobox", fieldbackground=p["bg_secondary"], foreground=p["text"],
                    background=p["widget_surface"], arrowcolor=p["text"])
    style.configure("Treeview", background=p["bg_secondary"], foreground=p["text"],
                    fieldbackground=p["bg_secondary"], borderwidth=0, rowheight=22)
    style.map("Treeview",
              background=[("selected", p["accent"])], foreground=[("selected", "#ffffff")])
    style.configure("Treeview.Heading", background=p["widget_surface"], foreground=p["text"])
    style.configure("TPanedwindow", background=p["bg_primary"])
    style.configure("Vertical.TScrollbar", background=p["widget_surface"],
                    troughcolor=p["bg_secondary"], arrowcolor=p["text"])
