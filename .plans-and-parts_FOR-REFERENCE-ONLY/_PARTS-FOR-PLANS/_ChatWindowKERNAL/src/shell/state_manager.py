"""
Owns: persistent window, layout, and session state load/save behavior.
Does not own: widget creation, live layout mutation, or task execution.
Collaborates with: the app kernel, layout manager, and panels.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

from src.shell.app_context import UIDefaults
from src.shell.constants import THEME_HARBOR_MIST
from src.utils.json_utils import load_json_file, write_json_file
from src.utils.paths import AppPaths


@dataclass(frozen=True)
class WindowState:
    x: int | None
    y: int | None
    width: int
    height: int
    maximized: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UIState:
    theme_name: str
    secondary_panel_visible: bool
    secondary_panel_width: int
    workspace_selected_tab: str | None
    inspector_selected_widget_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SessionState:
    draft_text: str
    last_active_panel: str
    last_snapshot_file: str | None
    active_session_id: str | None = None
    selected_model: str | None = None
    selected_loop: str | None = None
    use_echo: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StateManager:
    def __init__(self, paths: AppPaths, ui_defaults: UIDefaults) -> None:
        self._paths = paths
        self._ui_defaults = ui_defaults
        self._logger = logging.getLogger("shell.state")

    def load_window_state(self) -> WindowState:
        payload = load_json_file(self._paths.window_state_file, {})
        state = self._normalize_window_state(payload)
        self._logger.info("Window state loaded.")
        return state

    def save_window_state(self, state: WindowState) -> None:
        write_json_file(self._paths.window_state_file, state.to_dict())
        self._logger.info("Window state saved.")

    def load_ui_state(self) -> UIState:
        payload = load_json_file(self._paths.ui_state_file, {})
        state = self._normalize_ui_state(payload)
        self._logger.info("UI state loaded.")
        return state

    def save_ui_state(self, state: UIState) -> None:
        write_json_file(self._paths.ui_state_file, state.to_dict())
        self._logger.info("UI state saved.")

    def load_session_state(self) -> SessionState:
        payload = load_json_file(self._paths.session_state_file, {})
        state = self._normalize_session_state(payload)
        self._logger.info("Session state loaded.")
        return state

    def save_session_state(self, state: SessionState) -> None:
        write_json_file(self._paths.session_state_file, state.to_dict())
        self._logger.info("Session state saved.")

    def default_window_state(self) -> WindowState:
        return WindowState(
            x=None,
            y=None,
            width=self._ui_defaults.default_width,
            height=self._ui_defaults.default_height,
            maximized=False,
        )

    def default_ui_state(self, theme_name: str = THEME_HARBOR_MIST) -> UIState:
        return UIState(
            theme_name=theme_name,
            secondary_panel_visible=self._ui_defaults.secondary_panel_visible,
            secondary_panel_width=self._ui_defaults.secondary_panel_width,
            workspace_selected_tab="agent_hud",
            inspector_selected_widget_id=None,
        )

    @staticmethod
    def default_session_state() -> SessionState:
        return SessionState(
            draft_text="",
            last_active_panel="chat",
            last_snapshot_file=None,
            active_session_id=None,
            selected_model=None,
            selected_loop=None,
            use_echo=False,
        )

    def _normalize_window_state(self, payload: dict[str, Any]) -> WindowState:
        default = self.default_window_state()
        width = max(self._ui_defaults.min_width, int(payload.get("width", default.width)))
        height = max(self._ui_defaults.min_height, int(payload.get("height", default.height)))
        x = payload.get("x")
        y = payload.get("y")
        return WindowState(
            x=int(x) if isinstance(x, int) else None,
            y=int(y) if isinstance(y, int) else None,
            width=width,
            height=height,
            maximized=bool(payload.get("maximized", default.maximized)),
        )

    def _normalize_ui_state(self, payload: dict[str, Any]) -> UIState:
        default = self.default_ui_state()
        return UIState(
            theme_name=str(payload.get("theme_name", default.theme_name)),
            secondary_panel_visible=bool(
                payload.get("secondary_panel_visible", default.secondary_panel_visible)
            ),
            secondary_panel_width=max(
                240,
                int(payload.get("secondary_panel_width", default.secondary_panel_width)),
            ),
            workspace_selected_tab=_optional_string(payload.get("workspace_selected_tab"))
            or default.workspace_selected_tab,
            inspector_selected_widget_id=_optional_string(
                payload.get("inspector_selected_widget_id")
            ),
        )

    def _normalize_session_state(self, payload: dict[str, Any]) -> SessionState:
        default = self.default_session_state()
        return SessionState(
            draft_text=str(payload.get("draft_text", default.draft_text)),
            last_active_panel=str(payload.get("last_active_panel", default.last_active_panel)),
            last_snapshot_file=_optional_string(payload.get("last_snapshot_file")),
            active_session_id=_optional_string(payload.get("active_session_id")),
            selected_model=_optional_string(payload.get("selected_model")),
            selected_loop=_optional_string(payload.get("selected_loop")),
            use_echo=bool(payload.get("use_echo", default.use_echo)),
        )


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
