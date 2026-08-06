"""
Owns: the secondary tabbed workspace host for agent, tools, events, and inspector views.
Does not own: runtime state, shell persistence, or task execution.
Collaborates with: the app kernel, workspace tab views, and UI registry.
"""

from __future__ import annotations

from tkinter import ttk

from src.shell.constants import (
    WORKSPACE_TAB_AGENT,
    WORKSPACE_TAB_EVENTS,
    WORKSPACE_TAB_INSPECTOR,
    WORKSPACE_TAB_TOOLS,
)
from src.ui.panels.base_panel import BasePanel
from src.ui.registry_hooks import register_widget
from src.ui.workspace.agent_hud_tab import AgentHudTab
from src.ui.workspace.events_tab import EventsTab
from src.ui.workspace.inspector_tab import InspectorTab
from src.ui.workspace.tools_tab import ToolsTab


class WorkspacePanel(BasePanel):
    def __init__(
        self,
        theme_manager,
        *,
        on_resolve_hitl,
        on_run_tool,
        on_cancel_tool,
        on_tab_selected,
        on_ui_event=None,
    ) -> None:
        super().__init__(panel_id="workspace", title="Workspace", parent_widget_id="main.secondary_host")
        self._theme_manager = theme_manager
        self._on_tab_selected = on_tab_selected
        self._notebook = None
        self._tabs: dict[str, object] = {
            WORKSPACE_TAB_AGENT: AgentHudTab(
                theme_manager,
                on_resolve_hitl=on_resolve_hitl,
                on_ui_event=on_ui_event,
            ),
            WORKSPACE_TAB_TOOLS: ToolsTab(
                theme_manager,
                on_run_tool=on_run_tool,
                on_cancel_tool=on_cancel_tool,
                on_ui_event=on_ui_event,
            ),
            WORKSPACE_TAB_EVENTS: EventsTab(theme_manager, on_ui_event=on_ui_event),
            WORKSPACE_TAB_INSPECTOR: InspectorTab(theme_manager, on_ui_event=on_ui_event),
        }
        self._tab_frames: dict[str, object] = {}

    def build(self, parent) -> None:
        self.frame = ttk.Frame(parent, style="SurfaceAlt.TFrame", padding=(0, 0))
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self._notebook = ttk.Notebook(self.frame)
        self._notebook.grid(row=0, column=0, sticky="nsew")
        self._notebook.bind("<<NotebookTabChanged>>", self._handle_tab_changed)

        for tab_id, tab in self._tabs.items():
            tab.build(self._notebook)
            self._tab_frames[tab_id] = tab.frame
            self._notebook.add(tab.frame, text=tab.title)

    def register_widgets(self, registry) -> None:
        register_widget(
            registry,
            widget_id="workspace.panel",
            widget=self.frame,
            role="workspace_panel",
            panel_id=self.panel_id,
            parent_id=self.parent_widget_id,
        )
        register_widget(
            registry,
            widget_id="workspace.notebook",
            widget=self._notebook,
            role="workspace_notebook",
            panel_id=self.panel_id,
            parent_id="workspace.panel",
        )
        for tab in self._tabs.values():
            tab.register_widgets(registry)

    def refresh(
        self,
        *,
        agent_snapshot,
        tool_snapshot,
        activity_events: list[dict],
        data_hooks: list[dict],
        widget_tree: list[dict],
        widget_records: list[dict],
    ) -> None:
        self._tabs[WORKSPACE_TAB_AGENT].refresh(agent_snapshot=agent_snapshot, data_hooks=data_hooks)
        self._tabs[WORKSPACE_TAB_TOOLS].refresh(tool_snapshot=tool_snapshot)
        self._tabs[WORKSPACE_TAB_EVENTS].refresh(activity_events=activity_events)
        self._tabs[WORKSPACE_TAB_INSPECTOR].refresh(
            widget_tree=widget_tree,
            widget_records=widget_records,
        )

    def restore_state(self, state: dict) -> None:
        selected_tab = state.get("workspace_selected_tab")
        if selected_tab in self._tab_frames:
            self._notebook.select(self._tab_frames[selected_tab])
        self._tabs[WORKSPACE_TAB_INSPECTOR].restore_state(state)

    def get_state(self) -> dict:
        state = {"workspace_selected_tab": self.get_selected_tab_id()}
        state.update(self._tabs[WORKSPACE_TAB_INSPECTOR].get_state())
        return state

    def get_snapshot(self) -> dict:
        return {
            "panel_id": self.panel_id,
            "selected_tab": self.get_selected_tab_id(),
            "tabs": {tab_id: tab.get_snapshot() for tab_id, tab in self._tabs.items()},
        }

    def get_selected_tab_id(self) -> str:
        current = self._notebook.select()
        for tab_id, frame in self._tab_frames.items():
            if str(frame) == current:
                return tab_id
        return WORKSPACE_TAB_AGENT

    def get_selected_widget_id(self) -> str | None:
        return self._tabs[WORKSPACE_TAB_INSPECTOR].get_selected_widget_id()

    def apply_theme(self) -> None:
        for tab in self._tabs.values():
            tab.apply_theme()

    def _handle_tab_changed(self, _event) -> None:
        self._on_tab_selected(self.get_selected_tab_id())
