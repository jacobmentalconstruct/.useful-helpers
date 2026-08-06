"""
Owns: stable host-facing agent contracts and snapshot shapes.
Does not own: runtime orchestration, UI layout, or external agent adapters.
Collaborates with: host agent controller and chat-facing panels.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class AgentStepSnapshot:
    step_id: str
    phase: str
    summary: str
    status: str
    created_at: str
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HITLGateSnapshot:
    approval_id: str
    label: str
    prompt: str
    status: str
    requested_at: str
    resolved_at: str | None = None
    note: str = ""
    capability_class: str = "manual"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentSnapshot:
    controller_state: str
    active_turn_id: str | None
    last_user_message: str
    last_agent_message: str
    current_loop: str
    current_step: AgentStepSnapshot | None
    pending_approvals: list[HITLGateSnapshot] = field(default_factory=list)
    evidence_summary: dict[str, Any] = field(default_factory=dict)
    stop_requested: bool = False
    pause_requested: bool = False
    current_turn_mode: str = "chat"
    last_completed_turn_id: str | None = None
    recent_steps: list[AgentStepSnapshot] = field(default_factory=list)
    current_model: str = ""
    model_status: str = ""
    session_id: str = ""
    session_name: str = ""
    can_pause: bool = False
    can_resume: bool = False
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


class AgentController(ABC):
    @abstractmethod
    def submit_user_turn(self, text: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def request_stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def pause_run(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def resume_run(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def resolve_hitl_gate(self, approval_id: str, approved: bool, note: str = "") -> None:
        raise NotImplementedError

    @abstractmethod
    def get_snapshot(self) -> AgentSnapshot:
        raise NotImplementedError

    @abstractmethod
    def recent_activity(
        self,
        *,
        limit: int = 50,
        families: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def subscribe_activity(self, handler: Callable[[dict[str, Any]], None]) -> None:
        raise NotImplementedError
