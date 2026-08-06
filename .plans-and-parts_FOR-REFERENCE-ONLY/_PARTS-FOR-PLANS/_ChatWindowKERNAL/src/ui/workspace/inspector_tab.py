"""
Owns: the Inspector tab for structural widget-registry inspection inside the workspace.
Does not own: registry state, shell snapshots, or workspace orchestration.
Collaborates with: the workspace panel and UI registry.
"""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk

from src.ui.registry_hooks import register_widget
from src.ui.workspace.base_tab import WorkspaceTabView


class InspectorTab(WorkspaceTabView):
    def __init__(self, theme_manager, on_ui_event=None) -> None:
        super().__init__(tab_id="inspector", title="Inspector", parent_widget_id="workspace.notebook")
        self._theme_manager = theme_manager
        self._on_ui_event = on_ui_event
        self._tree = None
        self._details = None
        self._records: dict[str, dict] = {}
        self._selected_widget_id: str | None = None

    def build(self, parent) -> None:
        self.frame = ttk.Frame(parent, style="SurfaceAlt.TFrame", padding=(14, 14))
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        self._tree = ttk.Treeview(
            self.frame,
            columns=("role", "panel"),
            show="tree headings",
            selectmode="browse",
        )
        self._tree.heading("#0", text="Widget")
        self._tree.heading("role", text="Role")
        self._tree.heading("panel", text="Panel")
        self._tree.column("#0", width=180, stretch=True)
        self._tree.column("role", width=110, stretch=True)
        self._tree.column("panel", width=90, stretch=False)
        self._tree.grid(row=0, column=0, sticky="nsew")
        self._tree.bind("<<TreeviewSelect>>", self._handle_selection)

        self._details = tk.Text(self.frame, wrap="word", padx=12, pady=12)
        self._details.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        self._details.configure(state="disabled")

        self.apply_theme()

    def register_widgets(self, registry) -> None:
        register_widget(
            registry,
            widget_id="workspace.inspector.tab",
            widget=self.frame,
            role="inspector_tab",
            panel_id="workspace",
            parent_id=self.parent_widget_id,
        )
        register_widget(
            registry,
            widget_id="workspace.inspector.tree",
            widget=self._tree,
            role="inspector_tree",
            panel_id="workspace",
            parent_id="workspace.inspector.tab",
        )
        register_widget(
            registry,
            widget_id="workspace.inspector.details",
            widget=self._details,
            role="inspector_detail",
            panel_id="workspace",
            parent_id="workspace.inspector.tab",
            content_getter=lambda: self._details.get("1.0", "end-1c"),
        )

    def refresh(self, *, widget_tree: list[dict], widget_records: list[dict]) -> None:
        self._records = {record["widget_id"]: record for record in widget_records}
        self._tree.delete(*self._tree.get_children())
        for node in widget_tree:
            self._insert_node("", node)

        if self._selected_widget_id and self._selected_widget_id in self._records:
            self._tree.selection_set(self._selected_widget_id)
            self._tree.see(self._selected_widget_id)
            self._render_detail(self._selected_widget_id)

    def restore_state(self, state: dict) -> None:
        self._selected_widget_id = state.get("inspector_selected_widget_id")

    def get_state(self) -> dict:
        return {"inspector_selected_widget_id": self._selected_widget_id}

    def get_snapshot(self) -> dict:
        return {
            "selected_widget_id": self._selected_widget_id,
            "widget_count": len(self._records),
        }

    def get_selected_widget_id(self) -> str | None:
        return self._selected_widget_id

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
        if self._on_ui_event is not None:
            self._on_ui_event(
                "workspace.inspector",
                "Widget selected in Inspector tab.",
                payload={"widget_id": self._selected_widget_id},
            )
        self._render_detail(self._selected_widget_id)

    def _render_detail(self, widget_id: str) -> None:
        payload = self._records.get(widget_id, {})
        self._details.configure(state="normal")
        self._details.delete("1.0", "end")
        self._details.insert("1.0", json.dumps(payload, indent=2))
        self._details.configure(state="disabled")
