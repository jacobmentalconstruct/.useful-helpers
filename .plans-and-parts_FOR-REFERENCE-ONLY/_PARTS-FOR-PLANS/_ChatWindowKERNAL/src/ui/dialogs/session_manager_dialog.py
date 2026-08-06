"""
Owns: the session manager modal for session CRUD and current-session controls.
Does not own: session persistence internals, vendored runtime imports, or shell orchestration.
Collaborates with: the app kernel, session controller, and UI registry.
"""

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk

from src.ui.registry_hooks import register_widget


@dataclass(frozen=True)
class SessionDialogActions:
    refresh_snapshot: callable
    save_current: callable
    create_session: callable
    load_session: callable
    rename_session: callable
    delete_session: callable
    reset_current: callable


class SessionManagerDialog:
    def __init__(self, root, theme_manager, *, actions: SessionDialogActions, ui_registry=None) -> None:
        self._root = root
        self._theme_manager = theme_manager
        self._actions = actions
        self._ui_registry = ui_registry
        self._window = None
        self._sessions_tree = None
        self._name_entry = None
        self._summary_label = None
        self._selected_session_id: str | None = None
        self._registered_ids: list[str] = []

    def open(self, snapshot) -> None:
        if self._window is not None and self._window.winfo_exists():
            self._window.deiconify()
            self._window.lift()
            self.refresh(snapshot)
            return

        self._window = tk.Toplevel(self._root)
        self._window.title("Session Manager")
        self._window.transient(self._root)
        self._window.grab_set()
        self._window.geometry("760x420")
        self._window.minsize(680, 360)
        self._window.protocol("WM_DELETE_WINDOW", self.close)
        self._window.grid_columnconfigure(0, weight=1)
        self._window.grid_rowconfigure(1, weight=1)

        shell = ttk.Frame(self._window, style="Surface.TFrame", padding=(18, 18))
        shell.grid(row=0, column=0, sticky="nsew")
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(shell, style="Surface.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ttk.Label(header, text="Session Manager", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        self._summary_label = ttk.Label(
            header,
            text="Manage sessions, naming, and current session reset controls.",
            style="Muted.TLabel",
        )
        self._summary_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        body = ttk.Frame(shell, style="Surface.TFrame")
        body.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        sessions_frame = ttk.Frame(body, style="Surface.TFrame")
        sessions_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        sessions_frame.grid_columnconfigure(0, weight=1)
        sessions_frame.grid_rowconfigure(1, weight=1)
        ttk.Label(sessions_frame, text="Available Sessions", style="Muted.TLabel").grid(row=0, column=0, sticky="w")

        self._sessions_tree = ttk.Treeview(
            sessions_frame,
            columns=("updated", "count"),
            show="tree headings",
            selectmode="browse",
        )
        self._sessions_tree.heading("#0", text="Session")
        self._sessions_tree.heading("updated", text="Updated")
        self._sessions_tree.heading("count", text="Memories")
        self._sessions_tree.column("#0", width=280, stretch=True)
        self._sessions_tree.column("updated", width=140, stretch=False)
        self._sessions_tree.column("count", width=90, stretch=False)
        self._sessions_tree.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self._sessions_tree.bind("<<TreeviewSelect>>", self._handle_selection)

        controls = ttk.Frame(body, style="Surface.TFrame")
        controls.grid(row=0, column=1, sticky="nsew")
        controls.grid_columnconfigure(0, weight=1)

        ttk.Label(controls, text="Session Name", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self._name_entry = ttk.Entry(controls)
        self._name_entry.grid(row=1, column=0, sticky="ew", pady=(8, 12))

        ttk.Button(controls, text="Save Current", style="Accent.TButton", command=self._save_current).grid(
            row=2,
            column=0,
            sticky="ew",
        )
        ttk.Button(controls, text="New Session", style="Ghost.TButton", command=self._create_session).grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )
        ttk.Button(controls, text="Load Selected", style="Ghost.TButton", command=self._load_selected).grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )
        ttk.Button(controls, text="Rename Selected", style="Ghost.TButton", command=self._rename_selected).grid(
            row=5,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )
        ttk.Button(controls, text="Delete Selected", style="Ghost.TButton", command=self._delete_selected).grid(
            row=6,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )
        ttk.Button(controls, text="Reset Current", style="Ghost.TButton", command=self._reset_current).grid(
            row=7,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )
        ttk.Button(controls, text="Close", style="Ghost.TButton", command=self.close).grid(
            row=8,
            column=0,
            sticky="ew",
            pady=(18, 0),
        )

        self._register_widgets()
        self.refresh(snapshot)

    def refresh(self, snapshot) -> None:
        if self._window is None or not self._window.winfo_exists():
            return

        active = snapshot.active_session
        active_name = active.name or "Untitled Session"
        self._summary_label.configure(
            text=(
                f"Active: {active_name}  |  "
                f"{active.session_id or 'pending'}  |  "
                f"{snapshot.current_model or 'No model'}  |  "
                f"Loop {snapshot.current_loop or '--'}"
            )
        )

        existing_selection = self._selected_session_id or active.session_id
        self._sessions_tree.delete(*self._sessions_tree.get_children())
        for item in snapshot.available_sessions:
            label = item.name or item.session_id or "(unnamed)"
            self._sessions_tree.insert(
                "",
                "end",
                iid=item.session_id,
                text=label,
                values=(item.updated_at or "--", item.message_count),
            )

        if existing_selection and existing_selection in self._sessions_tree.get_children():
            self._sessions_tree.selection_set(existing_selection)
            self._selected_session_id = existing_selection
        elif active.session_id and active.session_id in self._sessions_tree.get_children():
            self._sessions_tree.selection_set(active.session_id)
            self._selected_session_id = active.session_id
        else:
            self._selected_session_id = None

        self._name_entry.delete(0, "end")
        self._name_entry.insert(0, active.name or "")

    def close(self) -> None:
        if self._ui_registry is not None:
            for widget_id in reversed(self._registered_ids):
                self._ui_registry.unregister_widget(widget_id)
            self._registered_ids.clear()
        if self._window is not None and self._window.winfo_exists():
            self._window.grab_release()
            self._window.destroy()
        self._window = None
        self._selected_session_id = None

    def _save_current(self) -> None:
        snapshot = self._actions.save_current(self._name_entry.get().strip())
        self.refresh(snapshot)

    def _create_session(self) -> None:
        snapshot = self._actions.create_session(self._name_entry.get().strip())
        self.refresh(snapshot)

    def _load_selected(self) -> None:
        if self._selected_session_id is None:
            return
        snapshot = self._actions.load_session(self._selected_session_id)
        self.refresh(snapshot)

    def _rename_selected(self) -> None:
        if self._selected_session_id is None:
            return
        snapshot = self._actions.rename_session(self._selected_session_id, self._name_entry.get().strip())
        self.refresh(snapshot)

    def _delete_selected(self) -> None:
        if self._selected_session_id is None:
            return
        snapshot = self._actions.delete_session(self._selected_session_id)
        self.refresh(snapshot)

    def _reset_current(self) -> None:
        snapshot = self._actions.reset_current()
        self.refresh(snapshot)

    def _handle_selection(self, _event) -> None:
        selection = self._sessions_tree.selection()
        self._selected_session_id = selection[0] if selection else None
        if self._selected_session_id is None:
            return
        item = self._sessions_tree.item(self._selected_session_id)
        self._name_entry.delete(0, "end")
        self._name_entry.insert(0, item.get("text", ""))

    def _register_widgets(self) -> None:
        if self._ui_registry is None or self._window is None:
            return
        specs = [
            (
                "dialog.session_manager",
                self._window,
                "session_manager_dialog",
                "shell",
                "main.window",
                None,
            ),
            (
                "dialog.session_manager.sessions",
                self._sessions_tree,
                "session_manager_tree",
                "shell",
                "dialog.session_manager",
                None,
            ),
            (
                "dialog.session_manager.name",
                self._name_entry,
                "session_manager_name_input",
                "shell",
                "dialog.session_manager",
                lambda: self._name_entry.get(),
            ),
            (
                "dialog.session_manager.summary",
                self._summary_label,
                "session_manager_summary",
                "shell",
                "dialog.session_manager",
                lambda: self._summary_label.cget("text"),
            ),
        ]
        for widget_id, widget, role, panel_id, parent_id, content_getter in specs:
            register_widget(
                self._ui_registry,
                widget_id=widget_id,
                widget=widget,
                role=role,
                panel_id=panel_id,
                parent_id=parent_id,
                content_getter=content_getter,
            )
            self._registered_ids.append(widget_id)
