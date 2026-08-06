"""
Owns: the Tools tab for package catalog, execution history, and operator controls.
Does not own: tool runtime state, agent reasoning, or shell orchestration.
Collaborates with: the workspace panel and package tool service.
"""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk

from src.ui.registry_hooks import register_widget
from src.ui.workspace.base_tab import WorkspaceTabView


class ToolsTab(WorkspaceTabView):
    def __init__(self, theme_manager, *, on_run_tool, on_cancel_tool, on_ui_event=None) -> None:
        super().__init__(tab_id="tools", title="Tools", parent_widget_id="workspace.notebook")
        self._theme_manager = theme_manager
        self._on_run_tool = on_run_tool
        self._on_cancel_tool = on_cancel_tool
        self._on_ui_event = on_ui_event
        self._tools_tree = None
        self._executions_tree = None
        self._arguments_text = None
        self._detail_text = None
        self._selected_tool_id: str | None = None
        self._selected_execution_id: str | None = None
        self._tool_map: dict[str, dict] = {}
        self._execution_map: dict[str, dict] = {}

    def build(self, parent) -> None:
        self.frame = ttk.Frame(parent, style="SurfaceAlt.TFrame", padding=(14, 14))
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(3, weight=1)

        ttk.Label(self.frame, text="Tool Catalog", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        self._tools_tree = ttk.Treeview(
            self.frame,
            columns=("category", "status"),
            show="tree headings",
            height=5,
            selectmode="browse",
        )
        self._tools_tree.heading("#0", text="Tool")
        self._tools_tree.heading("category", text="Category")
        self._tools_tree.heading("status", text="Status")
        self._tools_tree.column("#0", width=200, stretch=True)
        self._tools_tree.column("category", width=90, stretch=False)
        self._tools_tree.column("status", width=90, stretch=False)
        self._tools_tree.grid(row=1, column=0, sticky="ew", pady=(10, 12))
        self._tools_tree.bind("<<TreeviewSelect>>", self._select_tool)

        controls = ttk.Frame(self.frame, style="SurfaceAlt.TFrame")
        controls.grid(row=2, column=0, sticky="ew")
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=1)

        arguments_frame = ttk.Frame(controls, style="SurfaceAlt.TFrame")
        arguments_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        arguments_frame.grid_columnconfigure(0, weight=1)
        ttk.Label(arguments_frame, text="JSON Arguments", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self._arguments_text = tk.Text(arguments_frame, wrap="word", height=4, padx=12, pady=12)
        self._arguments_text.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self._arguments_text.insert("1.0", "{}")

        action_frame = ttk.Frame(controls, style="SurfaceAlt.TFrame")
        action_frame.grid(row=0, column=1, sticky="nsew")
        action_frame.grid_columnconfigure(0, weight=1)
        ttk.Button(action_frame, text="Run Selected", style="Accent.TButton", command=self._run_selected).grid(
            row=0,
            column=0,
            sticky="ew",
        )
        ttk.Button(
            action_frame,
            text="Cancel Selected",
            style="Ghost.TButton",
            command=self._cancel_selected,
        ).grid(row=1, column=0, sticky="ew", pady=(8, 0))

        lower = ttk.Frame(self.frame, style="SurfaceAlt.TFrame")
        lower.grid(row=3, column=0, sticky="nsew", pady=(14, 0))
        lower.grid_columnconfigure(0, weight=3)
        lower.grid_columnconfigure(1, weight=2)
        lower.grid_rowconfigure(1, weight=1)

        ttk.Label(lower, text="Execution History", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(lower, text="Selection Detail", style="PanelTitle.TLabel").grid(row=0, column=1, sticky="w", padx=(12, 0))

        self._executions_tree = ttk.Treeview(
            lower,
            columns=("tool", "state", "submitted"),
            show="headings",
            selectmode="browse",
        )
        self._executions_tree.heading("tool", text="Tool")
        self._executions_tree.heading("state", text="State")
        self._executions_tree.heading("submitted", text="Submitted")
        self._executions_tree.column("tool", width=150, stretch=True)
        self._executions_tree.column("state", width=90, stretch=False)
        self._executions_tree.column("submitted", width=90, stretch=False)
        self._executions_tree.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self._executions_tree.bind("<<TreeviewSelect>>", self._select_execution)

        self._detail_text = tk.Text(lower, wrap="word", padx=12, pady=12)
        self._detail_text.grid(row=1, column=1, sticky="nsew", padx=(12, 0), pady=(10, 0))
        self._detail_text.configure(state="disabled")

        self.apply_theme()

    def register_widgets(self, registry) -> None:
        register_widget(
            registry,
            widget_id="workspace.tools.tab",
            widget=self.frame,
            role="tools_tab",
            panel_id="workspace",
            parent_id=self.parent_widget_id,
        )
        register_widget(
            registry,
            widget_id="workspace.tools.catalog",
            widget=self._tools_tree,
            role="tool_catalog_tree",
            panel_id="workspace",
            parent_id="workspace.tools.tab",
        )
        register_widget(
            registry,
            widget_id="workspace.tools.executions",
            widget=self._executions_tree,
            role="tool_execution_tree",
            panel_id="workspace",
            parent_id="workspace.tools.tab",
        )
        register_widget(
            registry,
            widget_id="workspace.tools.arguments",
            widget=self._arguments_text,
            role="tool_arguments_input",
            panel_id="workspace",
            parent_id="workspace.tools.tab",
            content_getter=lambda: self._arguments_text.get("1.0", "end-1c"),
        )
        register_widget(
            registry,
            widget_id="workspace.tools.details",
            widget=self._detail_text,
            role="tool_details",
            panel_id="workspace",
            parent_id="workspace.tools.tab",
            content_getter=lambda: self._detail_text.get("1.0", "end-1c"),
        )

    def refresh(self, *, tool_snapshot) -> None:
        tool_selection = self._selected_tool_id
        execution_selection = self._selected_execution_id
        self._tool_map = {tool.tool_id: tool.to_dict() for tool in tool_snapshot.available_tools}
        self._execution_map = {
            execution.execution_id: execution.to_dict() for execution in tool_snapshot.recent_executions
        }

        self._tools_tree.delete(*self._tools_tree.get_children())
        for tool in tool_snapshot.available_tools:
            self._tools_tree.insert(
                "",
                "end",
                iid=tool.tool_id,
                text=tool.name,
                values=(tool.category, tool.status),
            )
        if tool_selection and tool_selection in self._tool_map:
            self._tools_tree.selection_set(tool_selection)

        self._executions_tree.delete(*self._executions_tree.get_children())
        for execution in reversed(tool_snapshot.recent_executions):
            self._executions_tree.insert(
                "",
                "end",
                iid=execution.execution_id,
                values=(
                    execution.tool_id,
                    execution.state,
                    execution.submitted_at[11:19],
                ),
            )
        if execution_selection and execution_selection in self._execution_map:
            self._executions_tree.selection_set(execution_selection)

        self._render_selection_detail()

    def get_snapshot(self) -> dict:
        return {
            "selected_tool_id": self._selected_tool_id,
            "selected_execution_id": self._selected_execution_id,
        }

    def apply_theme(self) -> None:
        self._theme_manager.configure_text(self._arguments_text, variant="input")
        self._theme_manager.configure_text(self._detail_text, variant="transcript")

    def _run_selected(self) -> None:
        if self._selected_tool_id is None:
            self._write_detail({"error": "Select a tool before running it."})
            return
        try:
            arguments = json.loads(self._arguments_text.get("1.0", "end-1c") or "{}")
        except json.JSONDecodeError as exc:
            self._write_detail({"error": f"Invalid JSON arguments: {exc}"})
            return
        execution_id = self._on_run_tool(self._selected_tool_id, arguments)
        self._selected_execution_id = execution_id

    def _cancel_selected(self) -> None:
        if self._selected_execution_id is None:
            self._write_detail({"error": "Select an execution before cancelling it."})
            return
        cancelled = self._on_cancel_tool(self._selected_execution_id)
        self._write_detail({"cancel_requested": cancelled, "execution_id": self._selected_execution_id})

    def _select_tool(self, _event) -> None:
        selection = self._tools_tree.selection()
        self._selected_tool_id = selection[0] if selection else None
        self._render_selection_detail()
        if self._selected_tool_id is not None and self._on_ui_event is not None:
            self._on_ui_event(
                "workspace.tools",
                "Tool selected in Tools tab.",
                payload={"tool_id": self._selected_tool_id},
            )

    def _select_execution(self, _event) -> None:
        selection = self._executions_tree.selection()
        self._selected_execution_id = selection[0] if selection else None
        self._render_selection_detail()
        if self._selected_execution_id is not None and self._on_ui_event is not None:
            self._on_ui_event(
                "workspace.tools",
                "Tool execution selected in Tools tab.",
                payload={"execution_id": self._selected_execution_id},
            )

    def _render_selection_detail(self) -> None:
        if self._selected_execution_id and self._selected_execution_id in self._execution_map:
            self._write_detail(self._execution_map[self._selected_execution_id])
            return
        if self._selected_tool_id and self._selected_tool_id in self._tool_map:
            self._write_detail(self._tool_map[self._selected_tool_id])
            return
        self._write_detail({"hint": "Select a tool or execution to inspect it."})

    def _write_detail(self, payload: dict) -> None:
        self._detail_text.configure(state="normal")
        self._detail_text.delete("1.0", "end")
        self._detail_text.insert("1.0", json.dumps(payload, indent=2))
        self._detail_text.configure(state="disabled")
