"""
Owns: stable host-facing session and runtime metadata contracts.
Does not own: UI layout, vendored agent imports, or task orchestration.
Collaborates with: session controller, chat header UI, and session-management dialogs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SessionInfoSnapshot:
    session_id: str
    name: str
    created_at: str
    updated_at: str
    message_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HardwareSnapshot:
    cpu_label: str = ""
    ram_summary: str = ""
    gpu_label: str = ""
    vram_summary: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SessionSnapshot:
    active_session: SessionInfoSnapshot
    available_sessions: list[SessionInfoSnapshot] = field(default_factory=list)
    available_models: list[str] = field(default_factory=list)
    available_loops: list[str] = field(default_factory=list)
    current_model: str = ""
    model_status: str = ""
    current_loop: str = ""
    use_echo: bool = False
    hardware: HardwareSnapshot = field(default_factory=HardwareSnapshot)
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_session": self.active_session.to_dict(),
            "available_sessions": [item.to_dict() for item in self.available_sessions],
            "available_models": list(self.available_models),
            "available_loops": list(self.available_loops),
            "current_model": self.current_model,
            "model_status": self.model_status,
            "current_loop": self.current_loop,
            "use_echo": self.use_echo,
            "hardware": self.hardware.to_dict(),
            "updated_at": self.updated_at,
        }


class SessionController(ABC):
    @abstractmethod
    def get_snapshot(self) -> SessionSnapshot:
        raise NotImplementedError

    @abstractmethod
    def set_model(self, model_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_loop(self, loop_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_current_session(self, name: str = "") -> SessionInfoSnapshot:
        raise NotImplementedError

    @abstractmethod
    def create_session(self, name: str = "") -> SessionInfoSnapshot:
        raise NotImplementedError

    @abstractmethod
    def load_session(self, session_id: str) -> SessionInfoSnapshot:
        raise NotImplementedError

    @abstractmethod
    def rename_session(self, session_id: str, new_name: str) -> SessionInfoSnapshot:
        raise NotImplementedError

    @abstractmethod
    def delete_session(self, session_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def reset_current_session(self) -> SessionInfoSnapshot:
        raise NotImplementedError
