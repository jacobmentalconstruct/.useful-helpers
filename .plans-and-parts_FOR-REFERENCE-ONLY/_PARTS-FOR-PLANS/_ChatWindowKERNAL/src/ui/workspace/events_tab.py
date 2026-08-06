"""
Owns: the Events tab for filtered runtime activity visibility.
Does not own: event production, task execution, or structural UI inspection.
Collaborates with: the workspace panel and activity stream.
"""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk

from src.ui.registry_hooks import register_widget
from src.ui.workspace.base_tab import WorkspaceTabView


class EventsTab(WorkspaceTabView):
    def __init__(self, theme_manager, on_ui_event=None) -> None:
        super().__init__(tab_id="events", title="Events", parent_widget_id="workspace.notebook")
        self._theme_manager = theme_manager
        self._on_ui_event = on_ui_event
        self._family_filter = None
        self._level_filter = None
        self._tree = None
        self._details = None
        self._records: dict[str, dict] = {}
        self._all_events: list[dict] = []

    def build(self, parent) -> None:
        self.frame = ttk.Frame(parent, style="SurfaceAlt.TFrame", padding=(14, 14))
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        controls = ttk.Frame(self.frame, style="SurfaceAlt.TFrame")
        controls.grid(row=0, column=0, sticky="ew")
        ttk.Label(controls, text="Family", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self._family_filter = ttk.Combobox(
            controls,
            values=["All", "agent", "tool", "system", "ui"],
            state="readonly",
            width=12,
        )
        self._family_filter.grid(row=0, column=1, padx=(8, 16))
        self._family_filter.set("All")
        self._family_filter.bind("<<ComboboxSelected>>", self._handle_family_filter_changed)

        ttk.Label(controls, text="Level", style="Muted.TLabel").grid(row=0, column=2, sticky="w")
        self._level_filter = ttk.Combobox(
            controls,
            values=["All", "info", "warning", "error"],
            state="readonly",
            width=12,
        )
        self._level_filter.grid(row=0, column=3, padx=(8, 0))
        self._level_filter.set("All")
        self._level_filter.bind("<<ComboboxSelected>>", self._handle_level_filter_changed)

        split = ttk.Frame(self.frame, style="SurfaceAlt.TFrame")
        split.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        split.grid_columnconfigure(0, weight=3)
        split.grid_columnconfigure(1, weight=2)
        split.grid_rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(
            split,
            columns=("family", "source", "level", "time"),
            show="tree headings",
            selectmode="browse",
        )
        self._tree.heading("#0", text="Summary")
        self._tree.heading("family", text="Family")
        self._tree.heading("source", text="Source")
        self._tree.heading("level", text="Level")
        self._tree.heading("time", text="Time")
        self._tree.column("#0", width=280, stretch=True)
        self._tree.column("family", width=100, stretch=False)
        self._tree.column("source", width=100, stretch=False)
        self._tree.column("level", width=70, stretch=False)
        self._tree.column("time", width=80, stretch=False)
        self._tree.grid(row=0, column=0, sticky="nsew")
        self._tree.bind("<<TreeviewSelect>>", self._render_selected_detail)

        self._details = tk.Text(split, wrap="word", padx=12, pady=12)
        self._details.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        self._details.configure(state="disabled")

        self.apply_theme()

    def register_widgets(self, registry) -> None:
        register_widget(
            registry,
            widget_id="workspace.events.tab",
            widget=self.frame,
            role="events_tab",
            panel_id="workspace",
            parent_id=self.parent_widget_id,
        )
        register_widget(
            registry,
            widget_id="workspace.events.tree",
            widget=self._tree,
            role="events_tree",
            panel_id="workspace",
            parent_id="workspace.events.tab",
        )
        register_widget(
            registry,
            widget_id="workspace.events.details",
            widget=self._details,
            role="events_detail",
            panel_id="workspace",
            parent_id="workspace.events.tab",
            content_getter=lambda: self._details.get("1.0", "end-1c"),
        )

    def refresh(self, *, activity_events: list[dict]) -> None:
        self._all_events = activity_events
        self._render_filtered_events()

    def get_snapshot(self) -> dict:
        return {
            "family_filter": self._family_filter.get(),
            "level_filter": self._level_filter.get(),
            "visible_event_count": len(self._tree.get_children()),
        }

    def apply_theme(self) -> None:
        self._theme_manager.configure_text(self._details, variant="transcript")

    def _render_filtered_events(self, _event=None) -> None:
        family = self._family_filter.get()
        level = self._level_filter.get()
        filtered = []
        for item in self._all_events:
            if family != "All" and not item["family"].startswith(family):
                continue
            if level != "All" and item["level"] != level:
                continue
            filtered.append(item)

        self._records = {item["event_id"]: item for item in filtered}
        selection = self._tree.selection()
        selected_id = selection[0] if selection else None
        self._tree.delete(*self._tree.get_children())
        for item in filtered:
            self._tree.insert(
                "",
                "end",
                iid=item["event_id"],
                text=item["summary"],
                values=(item["family"], item["source"], item["level"], item["created_at"][11:19]),
            )
        if selected_id and selected_id in self._records:
            self._tree.selection_set(selected_id)
            self._render_selected_detail(emit_ui_event=False)
        elif filtered:
            self._tree.selection_set(filtered[-1]["event_id"])
            self._render_selected_detail(emit_ui_event=False)
        else:
            self._write_detail({"hint": "No events match the current filters."})

    def _render_selected_detail(self, _event=None, *, emit_ui_event: bool = True) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        if emit_ui_event and self._on_ui_event is not None:
            self._on_ui_event(
                "workspace.events",
                "Runtime event selected in Events tab.",
                payload={"event_id": selection[0]},
            )
        self._write_detail(self._records.get(selection[0], {}))

    def _handle_family_filter_changed(self, _event=None) -> None:
        if self._on_ui_event is not None:
            self._on_ui_event(
                "workspace.events",
                "Events family filter changed.",
                payload={"family_filter": self._family_filter.get()},
            )
        self._render_filtered_events()

    def _handle_level_filter_changed(self, _event=None) -> None:
        if self._on_ui_event is not None:
            self._on_ui_event(
                "workspace.events",
                "Events level filter changed.",
                payload={"level_filter": self._level_filter.get()},
            )
        self._render_filtered_events()

    def _write_detail(self, payload: dict) -> None:
        self._details.configure(state="normal")
        self._details.delete("1.0", "end")
        self._details.insert("1.0", json.dumps(payload, indent=2))
        self._details.configure(state="disabled")
