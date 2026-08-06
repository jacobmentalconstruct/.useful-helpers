"""
Owns: persisted layout intent such as secondary pane visibility and width.
Does not own: pane widget creation, panel logic, or theme selection.
Collaborates with: the app kernel and paned shell UI adapter.
"""

from __future__ import annotations

import logging

from src.shell.state_manager import UIState


class LayoutManager:
    def __init__(self, event_bus, default_secondary_width: int) -> None:
        self._event_bus = event_bus
        self._default_secondary_width = default_secondary_width
        self._paned_shell = None
        self._logger = logging.getLogger("shell.layout")

    def attach(self, paned_shell) -> None:
        self._paned_shell = paned_shell
        self._logger.debug("Paned shell attached to layout manager.")

    def restore(self, ui_state: UIState) -> None:
        paned_shell = self._require_shell()
        paned_shell.set_secondary_width(ui_state.secondary_panel_width)
        if ui_state.secondary_panel_visible:
            paned_shell.show_secondary()
        else:
            paned_shell.hide_secondary()
        self._logger.info(
            "Layout restored. secondary_visible=%s secondary_width=%s",
            ui_state.secondary_panel_visible,
            ui_state.secondary_panel_width,
        )

    def toggle_secondary_panel(self) -> bool:
        paned_shell = self._require_shell()
        if paned_shell.is_secondary_visible():
            paned_shell.hide_secondary()
        else:
            paned_shell.show_secondary()
        visible = paned_shell.is_secondary_visible()
        self._event_bus.publish("layout_changed", self.snapshot())
        self._logger.info("Secondary panel visibility toggled. visible=%s", visible)
        return visible

    def capture_state(
        self,
        *,
        theme_name: str,
        workspace_selected_tab: str | None,
        inspector_selected_widget_id: str | None,
    ) -> UIState:
        paned_shell = self._require_shell()
        return UIState(
            theme_name=theme_name,
            secondary_panel_visible=paned_shell.is_secondary_visible(),
            secondary_panel_width=paned_shell.get_secondary_width()
            or self._default_secondary_width,
            workspace_selected_tab=workspace_selected_tab,
            inspector_selected_widget_id=inspector_selected_widget_id,
        )

    def snapshot(self) -> dict[str, int | bool]:
        paned_shell = self._require_shell()
        return {
            "secondary_panel_visible": paned_shell.is_secondary_visible(),
            "secondary_panel_width": paned_shell.get_secondary_width()
            or self._default_secondary_width,
        }

    def _require_shell(self):
        if self._paned_shell is None:
            raise RuntimeError("LayoutManager has no paned shell attached.")
        return self._paned_shell
