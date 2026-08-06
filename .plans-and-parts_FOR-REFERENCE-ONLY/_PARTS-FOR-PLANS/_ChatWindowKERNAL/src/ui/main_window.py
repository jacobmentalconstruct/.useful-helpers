"""
Owns: root-window composition for header, paned shell, and status bar surfaces.
Does not own: task execution, persistence files, or panel behavior.
Collaborates with: the app kernel, theme manager, and layout manager.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from tkinter import ttk

from src.ui.paned_shell import PanedShell
from src.ui.registry_hooks import register_widget
from src.ui.status_bar import StatusBar


@dataclass(frozen=True)
class WindowActions:
    toggle_theme: Callable[[], None]
    toggle_workspace: Callable[[], None]
    save_snapshot: Callable[[], None]
    crash_test: Callable[[], None] | None = None


class MainWindow:
    def __init__(
        self,
        root,
        *,
        app_name: str,
        theme_manager,
        actions: WindowActions,
        show_debug_actions: bool,
    ) -> None:
        self.root = root
        self._app_name = app_name
        self._theme_manager = theme_manager
        self._actions = actions
        self._show_debug_actions = show_debug_actions

        self._header = None
        self._theme_badge = None
        self._paned_shell = None
        self._status_bar = None
        self._workspace_button = None
        self._snapshot_button = None
        self._theme_button = None
        self._crash_button = None

    def build(self) -> None:
        self.root.title(self._app_name)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._header = ttk.Frame(self.root, style="Header.TFrame", padding=(18, 14))
        self._header.grid(row=0, column=0, sticky="ew")
        self._header.grid_columnconfigure(0, weight=1)

        heading = ttk.Frame(self._header, style="Header.TFrame")
        heading.grid(row=0, column=0, sticky="w")

        title_label = ttk.Label(heading, text=self._app_name, style="HeaderTitle.TLabel")
        title_label.grid(row=0, column=0, sticky="w")

        subtitle_label = ttk.Label(
            heading,
            text="Observable chat shell with persistent state and safe background work.",
            style="HeaderMeta.TLabel",
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(3, 0))

        controls = ttk.Frame(self._header, style="Header.TFrame")
        controls.grid(row=0, column=1, sticky="e")

        self._workspace_button = ttk.Button(
            controls,
            text="Workspace",
            style="Ghost.TButton",
            command=self._actions.toggle_workspace,
        )
        self._workspace_button.grid(row=0, column=0, padx=(0, 8))

        self._snapshot_button = ttk.Button(
            controls,
            text="Snapshot",
            style="Ghost.TButton",
            command=self._actions.save_snapshot,
        )
        self._snapshot_button.grid(row=0, column=1, padx=(0, 8))

        self._theme_button = ttk.Button(
            controls,
            text="Toggle Theme",
            style="Ghost.TButton",
            command=self._actions.toggle_theme,
        )
        self._theme_button.grid(row=0, column=2, padx=(0, 8))

        self._theme_badge = ttk.Label(controls, text="", style="HeaderMeta.TLabel")
        self._theme_badge.grid(row=0, column=3, padx=(0, 8))

        if self._show_debug_actions and self._actions.crash_test is not None:
            self._crash_button = ttk.Button(
                controls,
                text="Crash Test",
                style="Ghost.TButton",
                command=self._actions.crash_test,
            )
            self._crash_button.grid(row=0, column=4)

        self._paned_shell = PanedShell(self.root)
        self._paned_shell.grid(row=1, column=0, sticky="nsew")

        self._status_bar = StatusBar(self.root)
        self._status_bar.grid(row=2, column=0, sticky="ew")

    def register_widgets(self, registry) -> None:
        register_widget(
            registry,
            widget_id="main.window",
            widget=self.root,
            role="main_window",
            panel_id="shell",
        )
        register_widget(
            registry,
            widget_id="main.header",
            widget=self._header,
            role="header",
            panel_id="shell",
            parent_id="main.window",
        )
        register_widget(
            registry,
            widget_id="main.paned_shell",
            widget=self._paned_shell.paned,
            role="main_paned_shell",
            panel_id="shell",
            parent_id="main.window",
        )
        register_widget(
            registry,
            widget_id="main.primary_host",
            widget=self._paned_shell.primary_host,
            role="primary_panel_host",
            panel_id="shell",
            parent_id="main.paned_shell",
        )
        register_widget(
            registry,
            widget_id="main.secondary_host",
            widget=self._paned_shell.secondary_host,
            role="secondary_panel_host",
            panel_id="shell",
            parent_id="main.paned_shell",
        )
        register_widget(
            registry,
            widget_id="main.status_bar",
            widget=self._status_bar,
            role="status_bar",
            panel_id="shell",
            parent_id="main.window",
        )
        register_widget(
            registry,
            widget_id="main.status_label",
            widget=self._status_bar.status_label,
            role="status_label",
            panel_id="shell",
            parent_id="main.status_bar",
            content_getter=lambda: self._status_bar.status_label.cget("text"),
        )
        register_widget(
            registry,
            widget_id="main.task_label",
            widget=self._status_bar.task_label,
            role="task_status_label",
            panel_id="shell",
            parent_id="main.status_bar",
            content_getter=lambda: self._status_bar.task_label.cget("text"),
        )
        register_widget(
            registry,
            widget_id="main.meta_label",
            widget=self._status_bar.meta_label,
            role="status_meta_label",
            panel_id="shell",
            parent_id="main.status_bar",
            content_getter=lambda: self._status_bar.meta_label.cget("text"),
        )
        register_widget(
            registry,
            widget_id="main.workspace_button",
            widget=self._workspace_button,
            role="workspace_toggle_button",
            panel_id="shell",
            parent_id="main.header",
        )
        register_widget(
            registry,
            widget_id="main.snapshot_button",
            widget=self._snapshot_button,
            role="snapshot_button",
            panel_id="shell",
            parent_id="main.header",
        )
        register_widget(
            registry,
            widget_id="main.theme_button",
            widget=self._theme_button,
            role="theme_toggle_button",
            panel_id="shell",
            parent_id="main.header",
        )
        if self._crash_button is not None:
            register_widget(
                registry,
                widget_id="main.crash_button",
                widget=self._crash_button,
                role="crash_test_button",
                panel_id="shell",
                parent_id="main.header",
            )

    def bind_close(self, callback) -> None:
        self.root.protocol("WM_DELETE_WINDOW", callback)

    def render_status(self, snapshot) -> None:
        self._status_bar.render(snapshot)

    def apply_theme(self, theme_name: str) -> None:
        palette = self._theme_manager.apply(theme_name)
        self._paned_shell.apply_theme(palette)
        self._theme_badge.configure(text=theme_name.replace("_", " "))

    @property
    def primary_host(self):
        return self._paned_shell.primary_host

    @property
    def secondary_host(self):
        return self._paned_shell.secondary_host

    @property
    def paned_shell(self) -> PanedShell:
        return self._paned_shell
