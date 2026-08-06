"""
Owns: panel registration, mounting, disposal, and panel-level snapshots.
Does not own: layout widgets, persistence files, or task execution.
Collaborates with: the app kernel, panels, and UI registry.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.ui.panels.base_panel import BasePanel


@dataclass
class MountedPanel:
    panel_id: str
    panel: "BasePanel"
    region: str
    mounted: bool = False


class PanelManager:
    def __init__(self, event_bus) -> None:
        self._event_bus = event_bus
        self._logger = logging.getLogger("shell.panels")
        self._panels: dict[str, MountedPanel] = {}

    def register_panel(self, panel_id: str, panel: "BasePanel", *, region: str) -> None:
        if panel_id in self._panels:
            raise ValueError(f"Panel already registered: {panel_id}")
        self._panels[panel_id] = MountedPanel(panel_id=panel_id, panel=panel, region=region)
        self._logger.info("Panel registered. panel_id=%s region=%s", panel_id, region)
        self._event_bus.publish("panel_registered", {"panel_id": panel_id, "region": region})

    def mount_panel(self, panel_id: str, parent, registry) -> None:
        mounted_panel = self._require(panel_id)
        if mounted_panel.mounted:
            return

        mounted_panel.panel.build(parent)
        mounted_panel.panel.register_widgets(registry)
        mounted_panel.mounted = True
        self._logger.info("Panel mounted. panel_id=%s", panel_id)
        self._event_bus.publish(
            "panel_mounted",
            {"panel_id": panel_id, "region": mounted_panel.region},
        )

    def get_panel(self, panel_id: str) -> "BasePanel":
        return self._require(panel_id).panel

    def snapshot(self) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for mounted_panel in self._panels.values():
            payload.append(
                {
                    "panel_id": mounted_panel.panel_id,
                    "region": mounted_panel.region,
                    "mounted": mounted_panel.mounted,
                    "state": mounted_panel.panel.get_snapshot(),
                }
            )
        return payload

    def dispose_all(self) -> None:
        for mounted_panel in self._panels.values():
            mounted_panel.panel.dispose()
            self._event_bus.publish("panel_disposed", {"panel_id": mounted_panel.panel_id})
        self._logger.info("All panels disposed.")

    def _require(self, panel_id: str) -> MountedPanel:
        try:
            return self._panels[panel_id]
        except KeyError as exc:
            raise KeyError(f"Unknown panel id: {panel_id}") from exc
