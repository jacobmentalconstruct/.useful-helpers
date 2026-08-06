"""
Owns: normalized application config, UI defaults, and shared service references.
Does not own: service behavior, widget creation, or lifecycle sequencing.
Collaborates with: app bootstrap and the app kernel.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.shell.constants import (
    DEFAULT_QUEUE_POLL_INTERVAL_MS,
    THEME_CINDER_TIDE,
    THEME_HARBOR_MIST,
)
from src.utils.json_utils import load_json_file
from src.utils.paths import AppPaths

if TYPE_CHECKING:
    from src.runtime.activity_stream import ActivityStream
    from src.runtime.agent_host.controller import HostAgentController
    from src.runtime.agent_host.session_controller import HostSessionController
    from src.runtime.adapters.mindshard_adapter import MindshardAdapter
    from src.runtime.data_hooks import DataHookCatalog
    from src.runtime.tools.service import PackageToolService
    from src.shell.event_bus import EventBus
    from src.shell.layout_manager import LayoutManager
    from src.shell.lifecycle import LifecycleManager
    from src.shell.panel_manager import PanelManager
    from src.shell.runtime_snapshot import RuntimeSnapshotBuilder
    from src.shell.state_manager import StateManager
    from src.shell.status_controller import StatusController
    from src.shell.task_manager import TaskManager
    from src.shell.ui_registry import UIRegistry


@dataclass(frozen=True)
class AppConfig:
    app_id: str
    app_name: str
    theme: str
    dark_theme: str
    enable_inspector_panel: bool
    enable_debug_logging: bool
    queue_poll_interval_ms: int


@dataclass(frozen=True)
class UIDefaults:
    default_width: int
    default_height: int
    min_width: int
    min_height: int
    secondary_panel_visible: bool
    secondary_panel_width: int


@dataclass
class AppContext:
    paths: AppPaths
    app_config: AppConfig
    ui_defaults: UIDefaults
    app_logger: logging.Logger
    event_bus: "EventBus | None" = None
    lifecycle: "LifecycleManager | None" = None
    state_manager: "StateManager | None" = None
    task_manager: "TaskManager | None" = None
    ui_registry: "UIRegistry | None" = None
    status_controller: "StatusController | None" = None
    layout_manager: "LayoutManager | None" = None
    panel_manager: "PanelManager | None" = None
    runtime_snapshot: "RuntimeSnapshotBuilder | None" = None
    activity_stream: "ActivityStream | None" = None
    data_hook_catalog: "DataHookCatalog | None" = None
    agent_controller: "HostAgentController | None" = None
    session_controller: "HostSessionController | None" = None
    mindshard_adapter: "MindshardAdapter | None" = None
    tool_service: "PackageToolService | None" = None


def build_app_context(paths: AppPaths) -> AppContext:
    app_payload = load_json_file(paths.app_config_file, {})
    ui_payload = load_json_file(paths.ui_defaults_file, {})

    app_config = AppConfig(
        app_id=str(app_payload.get("app_id", "chat_window_kernal")),
        app_name=str(app_payload.get("app_name", "ChatWindowKERNAL")),
        theme=str(app_payload.get("theme", THEME_HARBOR_MIST)),
        dark_theme=str(app_payload.get("dark_theme", THEME_CINDER_TIDE)),
        enable_inspector_panel=bool(app_payload.get("enable_inspector_panel", True)),
        enable_debug_logging=bool(app_payload.get("enable_debug_logging", True)),
        queue_poll_interval_ms=max(
            25,
            int(app_payload.get("queue_poll_interval_ms", DEFAULT_QUEUE_POLL_INTERVAL_MS)),
        ),
    )

    ui_defaults = UIDefaults(
        default_width=max(640, int(ui_payload.get("default_width", 1200))),
        default_height=max(480, int(ui_payload.get("default_height", 800))),
        min_width=max(640, int(ui_payload.get("min_width", 900))),
        min_height=max(480, int(ui_payload.get("min_height", 600))),
        secondary_panel_visible=bool(ui_payload.get("secondary_panel_visible", True)),
        secondary_panel_width=max(240, int(ui_payload.get("secondary_panel_width", 340))),
    )

    return AppContext(
        paths=paths,
        app_config=app_config,
        ui_defaults=ui_defaults,
        app_logger=logging.getLogger("app"),
    )
