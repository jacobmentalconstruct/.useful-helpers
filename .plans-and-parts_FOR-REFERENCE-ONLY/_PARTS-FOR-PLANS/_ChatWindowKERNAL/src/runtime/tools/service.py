"""
Owns: portable tool discovery, execution tracking, and runtime snapshots.
Does not own: UI widgets, agent reasoning, or shell orchestration.
Collaborates with: task manager, activity stream, and tools-facing panels.
"""

from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass
from typing import Any

from src.runtime.activity_stream import ActivityStream
from src.runtime.contracts.tools import ToolDescriptor, ToolExecutionSnapshot, ToolRuntimeSnapshot, ToolService
from src.runtime.data_hooks import DataHookCatalog
from src.runtime.tools.manifests import ToolPackageDefinition, discover_tool_packages, invoke_tool
from src.shell.constants import (
    ACTIVITY_TOOL_COMPLETED,
    ACTIVITY_TOOL_FAILED,
    ACTIVITY_TOOL_REQUESTED,
    ACTIVITY_TOOL_STARTED,
    MAX_RECENT_TASKS,
)
from src.shell.task_manager import TaskManager, TaskResult
from src.utils.paths import AppPaths
from src.utils.time_utils import utc_timestamp


@dataclass
class _ExecutionRecord:
    execution_id: str
    tool_id: str
    state: str
    submitted_at: str
    started_at: str | None = None
    completed_at: str | None = None
    summary: str = ""
    detail: str = ""
    arguments: dict[str, Any] | None = None
    result_preview: Any = None
    task_id: str | None = None
    invocation_origin: str = "user"
    requesting_turn_id: str | None = None
    capability_class: str = "standard"

    def to_snapshot(self) -> ToolExecutionSnapshot:
        return ToolExecutionSnapshot(
            execution_id=self.execution_id,
            tool_id=self.tool_id,
            state=self.state,
            submitted_at=self.submitted_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            summary=self.summary,
            detail=self.detail,
            arguments=self.arguments or {},
            result_preview=self.result_preview,
            invocation_origin=self.invocation_origin,
            requesting_turn_id=self.requesting_turn_id,
            capability_class=self.capability_class,
        )


class PackageToolService(ToolService):
    def __init__(
        self,
        paths: AppPaths,
        task_manager: TaskManager,
        activity_stream: ActivityStream,
        data_hook_catalog: DataHookCatalog,
    ) -> None:
        self._paths = paths
        self._task_manager = task_manager
        self._activity_stream = activity_stream
        self._data_hook_catalog = data_hook_catalog
        self._logger = logging.getLogger("runtime.tools")
        self._lock = threading.Lock()
        self._definitions: dict[str, ToolPackageDefinition] = discover_tool_packages(paths.tool_packages_dir)
        self._executions: dict[str, _ExecutionRecord] = {}

        self._register_data_hooks()

    def list_tools(self) -> list[ToolDescriptor]:
        return [definition.descriptor for definition in self._definitions.values()]

    def run_tool(
        self,
        tool_id: str,
        arguments: dict[str, Any] | None = None,
        *,
        invocation_origin: str = "user",
        requesting_turn_id: str | None = None,
        capability_class: str | None = None,
    ) -> str:
        try:
            definition = self._definitions[tool_id]
        except KeyError as exc:
            raise KeyError(f"Unknown tool id: {tool_id}") from exc

        execution_id = str(uuid.uuid4())
        now = utc_timestamp()
        record = _ExecutionRecord(
            execution_id=execution_id,
            tool_id=tool_id,
            state="queued",
            submitted_at=now,
            started_at=now,
            summary=f"{definition.descriptor.name} queued.",
            arguments=arguments or {},
            invocation_origin=invocation_origin,
            requesting_turn_id=requesting_turn_id,
            capability_class=capability_class or definition.descriptor.capability_class,
        )
        with self._lock:
            self._executions[execution_id] = record

        self._activity_stream.append_event(
            ACTIVITY_TOOL_REQUESTED,
            "tool_service",
            f"Tool requested: {definition.descriptor.name}",
            payload={
                "execution_id": execution_id,
                "tool_id": tool_id,
                "invocation_origin": invocation_origin,
                "requesting_turn_id": requesting_turn_id,
            },
        )
        record.state = "running"
        record.summary = f"{definition.descriptor.name} running."
        self._activity_stream.append_event(
            ACTIVITY_TOOL_STARTED,
            "tool_service",
            f"Tool started: {definition.descriptor.name}",
            payload={"execution_id": execution_id, "tool_id": tool_id},
        )

        task_id = self._task_manager.submit_task(
            f"tool:{tool_id}",
            invoke_tool,
            definition,
            record.arguments or {},
            on_success=lambda result, execution_id=execution_id: self._complete_execution(
                execution_id,
                result,
            ),
            on_error=lambda task_result, execution_id=execution_id: self._fail_execution(
                execution_id,
                task_result,
            ),
            metadata={"tool_id": tool_id, "execution_id": execution_id},
        )
        with self._lock:
            self._executions[execution_id].task_id = task_id

        self._logger.info("Tool submitted. tool_id=%s execution_id=%s", tool_id, execution_id)
        return execution_id

    def cancel_tool(self, execution_id: str) -> bool:
        with self._lock:
            record = self._executions.get(execution_id)
            if record is None or record.state not in {"queued", "running"}:
                return False
            record.summary = f"Cancellation requested for {record.tool_id}."
            record.detail = "TaskManager does not yet support hard cancellation."
        self._logger.info("Tool cancellation requested. execution_id=%s", execution_id)
        return True

    def get_execution_snapshot(self, execution_id: str) -> ToolExecutionSnapshot | None:
        with self._lock:
            record = self._executions.get(execution_id)
        if record is None:
            return None
        return record.to_snapshot()

    def get_snapshot(self) -> ToolRuntimeSnapshot:
        tools = self.list_tools()
        with self._lock:
            executions = list(self._executions.values())

        executions.sort(key=lambda record: record.submitted_at)
        recent = [record.to_snapshot() for record in executions[-MAX_RECENT_TASKS:]]
        active_ids = [
            record.execution_id
            for record in executions
            if record.state in {"queued", "running"}
        ]
        return ToolRuntimeSnapshot(
            available_tools=tools,
            recent_executions=recent,
            active_execution_ids=active_ids,
            updated_at=utc_timestamp(),
        )

    def _complete_execution(self, execution_id: str, result: Any) -> None:
        with self._lock:
            record = self._executions[execution_id]
            record.state = "completed"
            record.completed_at = utc_timestamp()
            record.summary = f"Tool completed: {record.tool_id}"
            record.result_preview = result

        self._activity_stream.append_event(
            ACTIVITY_TOOL_COMPLETED,
            "tool_service",
            f"Tool completed: {record.tool_id}",
            payload={"execution_id": execution_id, "tool_id": record.tool_id},
        )

    def _fail_execution(self, execution_id: str, task_result: TaskResult) -> None:
        with self._lock:
            record = self._executions[execution_id]
            record.state = "failed"
            record.completed_at = utc_timestamp()
            record.summary = f"Tool failed: {record.tool_id}"
            record.detail = task_result.error_message or "Unknown error"
            record.result_preview = {"traceback": task_result.traceback_text}

        self._activity_stream.append_event(
            ACTIVITY_TOOL_FAILED,
            "tool_service",
            f"Tool failed: {record.tool_id}",
            level="error",
            detail=task_result.error_message or "",
            payload={"execution_id": execution_id, "tool_id": record.tool_id},
        )

    def _register_data_hooks(self) -> None:
        self._data_hook_catalog.register_hook(
            "tools.catalog",
            family="tool",
            producer="tool_service",
            description="Discovered portable tool packages.",
            freshness="live",
            preview_provider=lambda: [tool.to_dict() for tool in self.list_tools()],
        )
        self._data_hook_catalog.register_hook(
            "tools.runtime",
            family="tool",
            producer="tool_service",
            description="Tool execution history and active state.",
            freshness="live",
            preview_provider=lambda: self.get_snapshot().to_dict(),
        )
