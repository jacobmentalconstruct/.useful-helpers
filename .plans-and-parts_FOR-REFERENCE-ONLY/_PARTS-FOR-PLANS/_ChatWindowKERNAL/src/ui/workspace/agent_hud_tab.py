"""
Owns: the Agent HUD tab for current state, HITL actions, and data-hook visibility.
Does not own: agent execution, tool runtime, or shell persistence.
Collaborates with: the workspace panel and host agent controller.
"""

from __future__ import annotations

import json
from tkinter import ttk

from src.ui.registry_hooks import register_widget
from src.ui.workspace.base_tab import WorkspaceTabView


class AgentHudTab(WorkspaceTabView):
    def __init__(self, theme_manager, *, on_resolve_hitl, on_ui_event=None) -> None:
        super().__init__(tab_id="agent_hud", title="Agent HUD", parent_widget_id="workspace.notebook")
        self._theme_manager = theme_manager
        self._on_resolve_hitl = on_resolve_hitl
        self._on_ui_event = on_ui_event
        self._snapshot = None
        self._state_value = None
        self._loop_value = None
        self._step_value = None
        self._updated_value = None
        self._approvals_tree = None
        self._details_text = None
        self._hooks_tree = None
        self._selected_approval_id: str | None = None
        self._selected_hook_id: str | None = None
        self._hook_map: dict[str, dict] = {}

    def build(self, parent) -> None:
        self.frame = ttk.Frame(parent, style="SurfaceAlt.TFrame", padding=(14, 14))
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)

        summary = ttk.Frame(self.frame, style="SurfaceAlt.TFrame")
        summary.grid(row=0, column=0, sticky="ew")
        for column in range(4):
            summary.grid_columnconfigure(column, weight=1)

        self._state_value = self._build_kv(summary, 0, "State")
        self._loop_value = self._build_kv(summary, 1, "Loop")
        self._step_value = self._build_kv(summary, 2, "Step")
        self._updated_value = self._build_kv(summary, 3, "Updated")

        approvals_frame = ttk.Frame(self.frame, style="SurfaceAlt.TFrame")
        approvals_frame.grid(row=1, column=0, sticky="nsew", pady=(14, 12))
        approvals_frame.grid_columnconfigure(0, weight=1)

        approvals_header = ttk.Frame(approvals_frame, style="SurfaceAlt.TFrame")
        approvals_header.grid(row=0, column=0, sticky="ew")
        approvals_header.grid_columnconfigure(0, weight=1)
        ttk.Label(approvals_header, text="Pending HITL", style="PanelTitle.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )

        buttons = ttk.Frame(approvals_header, style="SurfaceAlt.TFrame")
        buttons.grid(row=0, column=1, sticky="e")
        ttk.Button(
            buttons,
            text="Approve",
            style="Accent.TButton",
            command=lambda: self._resolve_selected(True),
        ).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(
            buttons,
            text="Reject",
            style="Ghost.TButton",
            command=lambda: self._resolve_selected(False),
        ).grid(row=0, column=1)

        self._approvals_tree = ttk.Treeview(
            approvals_frame,
            columns=("status", "prompt"),
            show="headings",
            height=4,
            selectmode="browse",
        )
        self._approvals_tree.heading("status", text="Status")
        self._approvals_tree.heading("prompt", text="Prompt")
        self._approvals_tree.column("status", width=90, stretch=False)
        self._approvals_tree.column("prompt", width=420, stretch=True)
        self._approvals_tree.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self._approvals_tree.bind("<<TreeviewSelect>>", self._on_approval_selected)

        lower = ttk.Frame(self.frame, style="SurfaceAlt.TFrame")
        lower.grid(row=2, column=0, sticky="nsew")
        lower.grid_columnconfigure(0, weight=3)
        lower.grid_columnconfigure(1, weight=2)
        lower.grid_rowconfigure(0, weight=1)

        self._details_text = self._build_text_panel(lower, column=0, title="Agent Detail")

        hooks_frame = ttk.Frame(lower, style="SurfaceAlt.TFrame")
        hooks_frame.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        hooks_frame.grid_columnconfigure(0, weight=1)
        hooks_frame.grid_rowconfigure(1, weight=1)
        ttk.Label(hooks_frame, text="Data Hooks", style="PanelTitle.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        self._hooks_tree = ttk.Treeview(
            hooks_frame,
            columns=("family", "producer"),
            show="headings",
            height=10,
            selectmode="browse",
        )
        self._hooks_tree.heading("family", text="Family")
        self._hooks_tree.heading("producer", text="Producer")
        self._hooks_tree.column("family", width=90, stretch=False)
        self._hooks_tree.column("producer", width=120, stretch=True)
        self._hooks_tree.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self._hooks_tree.bind("<<TreeviewSelect>>", self._on_hook_selected)

        self.apply_theme()

    def register_widgets(self, registry) -> None:
        register_widget(
            registry,
            widget_id="workspace.agent_hud.tab",
            widget=self.frame,
            role="agent_hud_tab",
            panel_id="workspace",
            parent_id=self.parent_widget_id,
        )
        register_widget(
            registry,
            widget_id="workspace.agent_hud.approvals",
            widget=self._approvals_tree,
            role="agent_hud_approvals",
            panel_id="workspace",
            parent_id="workspace.agent_hud.tab",
        )
        register_widget(
            registry,
            widget_id="workspace.agent_hud.details",
            widget=self._details_text,
            role="agent_hud_details",
            panel_id="workspace",
            parent_id="workspace.agent_hud.tab",
            content_getter=lambda: self._details_text.get("1.0", "end-1c"),
        )
        register_widget(
            registry,
            widget_id="workspace.agent_hud.hooks",
            widget=self._hooks_tree,
            role="agent_hud_hooks",
            panel_id="workspace",
            parent_id="workspace.agent_hud.tab",
        )

    def refresh(self, *, agent_snapshot, data_hooks: list[dict]) -> None:
        self._snapshot = agent_snapshot
        self._state_value.configure(text=agent_snapshot.controller_state)
        self._loop_value.configure(text=agent_snapshot.current_loop)
        self._step_value.configure(
            text=agent_snapshot.current_step.summary if agent_snapshot.current_step else "Idle"
        )
        self._updated_value.configure(text=agent_snapshot.updated_at[11:19] if agent_snapshot.updated_at else "--")

        selection = self._selected_approval_id
        self._approvals_tree.delete(*self._approvals_tree.get_children())
        for gate in agent_snapshot.pending_approvals:
            self._approvals_tree.insert(
                "",
                "end",
                iid=gate.approval_id,
                values=(gate.status, gate.prompt),
            )

        if selection and selection in self._approvals_tree.get_children():
            self._approvals_tree.selection_set(selection)

        self._hooks_tree.delete(*self._hooks_tree.get_children())
        self._hook_map = {hook["hook_id"]: hook for hook in data_hooks}
        for hook in data_hooks:
            self._hooks_tree.insert(
                "",
                "end",
                iid=hook["hook_id"],
                values=(hook["family"], hook["producer"]),
                text=hook["hook_id"],
            )

        if self._selected_hook_id and self._selected_hook_id in self._hook_map:
            self._hooks_tree.selection_set(self._selected_hook_id)
            self._write_details(
                {
                    "agent": {
                        "controller_state": agent_snapshot.controller_state,
                        "current_loop": agent_snapshot.current_loop,
                    },
                    "selected_hook": self._hook_map[self._selected_hook_id],
                }
            )
            return

        self._write_details(
            {
            "controller_state": agent_snapshot.controller_state,
            "last_user_message": agent_snapshot.last_user_message,
            "last_agent_message": agent_snapshot.last_agent_message,
            "evidence_summary": agent_snapshot.evidence_summary,
            "pending_approvals": [gate.to_dict() for gate in agent_snapshot.pending_approvals],
            }
        )

    def get_snapshot(self) -> dict:
        return {
            "selected_approval_id": self._selected_approval_id,
            "selected_hook_id": self._selected_hook_id,
            "pending_approval_count": len(self._snapshot.pending_approvals) if self._snapshot else 0,
        }

    def apply_theme(self) -> None:
        self._theme_manager.configure_text(self._details_text, variant="transcript")

    def _resolve_selected(self, approved: bool) -> None:
        if self._selected_approval_id is not None:
            self._on_resolve_hitl(self._selected_approval_id, approved)

    def _on_approval_selected(self, _event) -> None:
        selection = self._approvals_tree.selection()
        self._selected_approval_id = selection[0] if selection else None
        if self._selected_approval_id is not None and self._on_ui_event is not None:
            self._on_ui_event(
                "workspace.agent_hud",
                "Agent HUD approval selected.",
                payload={"approval_id": self._selected_approval_id},
            )

    def _on_hook_selected(self, _event) -> None:
        selection = self._hooks_tree.selection()
        self._selected_hook_id = selection[0] if selection else None
        if self._selected_hook_id is None:
            return

        hook = self._hook_map.get(self._selected_hook_id, {})
        self._write_details(
            {
                "agent": {
                    "controller_state": self._snapshot.controller_state if self._snapshot else "idle",
                    "current_loop": self._snapshot.current_loop if self._snapshot else "",
                },
                "selected_hook": hook,
            }
        )
        if self._on_ui_event is not None:
            self._on_ui_event(
                "workspace.agent_hud",
                "Agent HUD data hook selected.",
                payload={"hook_id": self._selected_hook_id},
            )

    def _write_details(self, payload: dict) -> None:
        self._details_text.configure(state="normal")
        self._details_text.delete("1.0", "end")
        self._details_text.insert("1.0", json.dumps(payload, indent=2))
        self._details_text.configure(state="disabled")

    @staticmethod
    def _build_kv(parent, column: int, label_text: str):
        block = ttk.Frame(parent, style="SurfaceAlt.TFrame")
        block.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
        ttk.Label(block, text=label_text, style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        value = ttk.Label(block, text="--", style="PanelTitle.TLabel")
        value.grid(row=1, column=0, sticky="w")
        return value

    @staticmethod
    def _build_text_panel(parent, *, column: int, title: str):
        frame = ttk.Frame(parent, style="SurfaceAlt.TFrame")
        frame.grid(row=0, column=column, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        ttk.Label(frame, text=title, style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        import tkinter as tk

        text = tk.Text(frame, wrap="word", padx=12, pady=12)
        text.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        text.configure(state="disabled")
        return text
