"""
Owns: registry visualization and widget-detail rendering for live introspection.
Does not own: registry state, snapshot composition, or layout persistence.
Collaborates with: the app kernel and UI registry.
"""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk

from src.ui.panels.base_panel import BasePanel
from src.ui.registry_hooks import register_widget


class InspectorPanel(BasePanel):
    def __init__(self, theme_manager, *, on_refresh_requested) -> None:
        super().__init__(
            panel_id="inspector",
            title="Inspector",
            parent_widget_id="main.secondary_host",
        )
        self._theme_manager = theme_manager
        self._on_refresh_requested = on_refresh_requested
        self._tree = None
        self._details = None
        self._refresh_button = None
        self._records: dict[str, dict] = {}
        self._selected_widget_id: str | None = None

    def build(self, parent) -> None:
        self.frame = ttk.Frame(parent, style="SurfaceAlt.TFrame", padding=(16, 16))
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)

        header = ttk.Frame(self.frame, style="SurfaceAlt.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_label = ttk.Label(header, text=self.title, style="PanelTitle.TLabel")
        title_label.grid(row=0, column=0, sticky="w")

        self._refresh_button = ttk.Button(
            header,
            text="Refresh",
            style="Ghost.TButton",
            command=self._on_refresh_requested,
        )
        self._refresh_button.grid(row=0, column=1, sticky="e")

        self._tree = ttk.Treeview(
            self.frame,
            columns=("role", "panel"),
            show="tree headings",
            selectmode="browse",
            height=10,
        )
        self._tree.heading("#0", text="Widget")
        self._tree.heading("role", text="Role")
        self._tree.heading("panel", text="Panel")
        self._tree.column("#0", width=170, stretch=True)
        self._tree.column("role", width=110, stretch=True)
        self._tree.column("panel", width=70, stretch=False)
        self._tree.grid(row=1, column=0, sticky="nsew", pady=(12, 12))
        self._tree.bind("<<TreeviewSelect>>", self._handle_selection)

        self._details = tk.Text(self.frame, wrap="word", padx=12, pady=12, height=12)
        self._details.grid(row=2, column=0, sticky="nsew")
        self._details.configure(state="disabled")

        self.apply_theme()

    def register_widgets(self, registry) -> None:
        register_widget(
            registry,
            widget_id="inspector.panel",
            widget=self.frame,
            role="inspector_panel",
            panel_id=self.panel_id,
            parent_id=self.parent_widget_id,
        )
        register_widget(
            registry,
            widget_id="inspector.tree",
            widget=self._tree,
            role="inspector_tree",
            panel_id=self.panel_id,
            parent_id="inspector.panel",
        )
        register_widget(
            registry,
            widget_id="inspector.details",
            widget=self._details,
            role="inspector_details",
            panel_id=self.panel_id,
            parent_id="inspector.panel",
            content_getter=self._get_detail_text,
        )

    def render_registry(self, tree_snapshot: list[dict], records: list[dict]) -> None:
        self._records = {record["widget_id"]: record for record in records}
        self._tree.delete(*self._tree.get_children())

        for node in tree_snapshot:
            self._insert_node("", node)

        if self._selected_widget_id and self._selected_widget_id in self._records:
            self._tree.selection_set(self._selected_widget_id)
            self._tree.see(self._selected_widget_id)
            self._render_details(self._selected_widget_id)

    def get_selected_widget_id(self) -> str | None:
        return self._selected_widget_id

    def get_state(self) -> dict:
        return {"inspector_selected_widget_id": self._selected_widget_id}

    def restore_state(self, state: dict) -> None:
        self._selected_widget_id = state.get("inspector_selected_widget_id")

    def get_snapshot(self) -> dict:
        return {
            "panel_id": self.panel_id,
            "selected_widget_id": self._selected_widget_id,
            "widget_count": len(self._records),
        }

    def apply_theme(self) -> None:
        self._theme_manager.configure_text(self._details, variant="transcript")

    def _insert_node(self, parent_id: str, node: dict) -> None:
        widget_id = node["widget_id"]
        self._tree.insert(
            parent_id,
            "end",
            iid=widget_id,
            text=widget_id,
            values=(node.get("role", ""), node.get("panel_id", "")),
        )
        for child in node.get("children", []):
            self._insert_node(widget_id, child)

    def _handle_selection(self, _event) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        self._selected_widget_id = selection[0]
        self._render_details(self._selected_widget_id)

    def _render_details(self, widget_id: str) -> None:
        payload = self._records.get(widget_id, {})
        text = json.dumps(payload, indent=2)
        self._details.configure(state="normal")
        self._details.delete("1.0", "end")
        self._details.insert("1.0", text)
        self._details.configure(state="disabled")

    def _get_detail_text(self) -> str:
        return self._details.get("1.0", "end-1c")
