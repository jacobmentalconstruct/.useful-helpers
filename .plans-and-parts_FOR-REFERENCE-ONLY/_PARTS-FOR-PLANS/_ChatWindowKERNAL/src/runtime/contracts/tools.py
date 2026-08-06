"""
Owns: stable host-facing tool contracts and snapshot shapes.
Does not own: tool execution plumbing, UI layout, or tool package manifests.
Collaborates with: package tool service and tools-facing panels.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolDescriptor:
    tool_id: str
    name: str
    description: str
    category: str
    manifest_path: str
    status: str = "available"
    capability_class: str = "standard"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToolExecutionSnapshot:
    execution_id: str
    tool_id: str
    state: str
    submitted_at: str
    started_at: str | None = None
    completed_at: str | None = None
    summary: str = ""
    detail: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    result_preview: Any = None
    invocation_origin: str = "user"
    requesting_turn_id: str | None = None
    capability_class: str = "standard"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToolRuntimeSnapshot:
    available_tools: list[ToolDescriptor]
    recent_executions: list[ToolExecutionSnapshot]
    active_execution_ids: list[str]
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "available_tools": [tool.to_dict() for tool in self.available_tools],
            "recent_executions": [execution.to_dict() for execution in self.recent_executions],
            "active_execution_ids": list(self.active_execution_ids),
            "updated_at": self.updated_at,
        }


class ToolService(ABC):
    @abstractmethod
    def list_tools(self) -> list[ToolDescriptor]:
        raise NotImplementedError

    @abstractmethod
    def run_tool(
        self,
        tool_id: str,
        arguments: dict[str, Any] | None = None,
        *,
        invocation_origin: str = "user",
        requesting_turn_id: str | None = None,
        capability_class: str | None = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def cancel_tool(self, execution_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_execution_snapshot(self, execution_id: str) -> ToolExecutionSnapshot | None:
        raise NotImplementedError

    @abstractmethod
    def get_snapshot(self) -> ToolRuntimeSnapshot:
        raise NotImplementedError
