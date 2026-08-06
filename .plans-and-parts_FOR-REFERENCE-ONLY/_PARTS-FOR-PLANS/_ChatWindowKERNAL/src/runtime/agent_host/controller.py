"""
Owns: host-facing agent control flow, vendored Mindshard turn orchestration, and agent snapshots.
Does not own: Tk widgets, vendored runtime internals, or portable tool package execution.
Collaborates with: session controller, task manager, activity stream, and the Mindshard adapter.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from dataclasses import dataclass
from typing import Any

from src.runtime.activity_stream import ActivityEvent, ActivityStream
from src.runtime.adapters.mindshard_adapter import MindshardAdapter, MindshardTurnInterrupted
from src.runtime.agent_host.session_controller import HostSessionController
from src.runtime.contracts.agent import (
    AgentController,
    AgentSnapshot,
    AgentStepSnapshot,
    HITLGateSnapshot,
)
from src.runtime.contracts.tools import ToolDescriptor, ToolService
from src.runtime.data_hooks import DataHookCatalog
from src.shell.constants import (
    ACTIVITY_AGENT_HITL_RESOLVED,
    ACTIVITY_AGENT_HITL_WAIT,
    ACTIVITY_AGENT_STEP,
    ACTIVITY_AGENT_TURN,
)
from src.shell.task_manager import TaskManager, TaskResult
from src.utils.time_utils import utc_timestamp


@dataclass(frozen=True)
class _PendingApprovalTurn:
    turn_id: str
    text: str
    mode: str


class _TurnControl:
    def __init__(self, on_checkpoint) -> None:
        self._on_checkpoint = on_checkpoint
        self._condition = threading.Condition()
        self._stop_requested = False
        self._pause_requested = False

    def request_stop(self) -> None:
        with self._condition:
            self._stop_requested = True
            self._condition.notify_all()

    def request_pause(self) -> None:
        with self._condition:
            self._pause_requested = True
            self._condition.notify_all()

    def resume(self) -> None:
        with self._condition:
            self._pause_requested = False
            self._condition.notify_all()

    def checkpoint(self, phase: str, detail: str = "") -> None:
        self._on_checkpoint("checkpoint", phase, detail)
        paused_once = False
        with self._condition:
            if self._stop_requested:
                self._on_checkpoint("stopped", phase, detail)
                raise MindshardTurnInterrupted("Turn stopped by host control.")
            while self._pause_requested and not self._stop_requested:
                if not paused_once:
                    self._on_checkpoint("paused", phase, detail)
                    paused_once = True
                self._condition.wait(timeout=0.1)
            if self._stop_requested:
                self._on_checkpoint("stopped", phase, detail)
                raise MindshardTurnInterrupted("Turn stopped by host control.")
        if paused_once:
            self._on_checkpoint("resumed", phase, detail)


class HostAgentController(AgentController):
    def __init__(
        self,
        adapter: MindshardAdapter,
        session_controller: HostSessionController,
        task_manager: TaskManager,
        activity_stream: ActivityStream,
        data_hook_catalog: DataHookCatalog,
        tool_service: ToolService,
    ) -> None:
        self._adapter = adapter
        self._session_controller = session_controller
        self._task_manager = task_manager
        self._activity_stream = activity_stream
        self._data_hook_catalog = data_hook_catalog
        self._tool_service = tool_service
        self._logger = logging.getLogger("runtime.agent_host")
        self._lock = threading.Lock()
        self._recent_steps: list[AgentStepSnapshot] = []
        self._pending_turn_by_approval_id: dict[str, _PendingApprovalTurn] = {}
        self._active_control: _TurnControl | None = None
        self._active_task_id: str | None = None
        self._snapshot = self._build_snapshot(
            controller_state="idle",
            active_turn_id=None,
            last_user_message="",
            last_agent_message="",
            current_step=None,
            evidence_summary={"state": "ready", "bag_status": "Mindshard runtime attached."},
        )
        self._register_data_hooks()

    def submit_user_turn(self, text: str) -> str:
        if not text.strip():
            raise ValueError("User turn text must not be empty.")

        turn_id = str(uuid.uuid4())
        try:
            command = _parse_user_turn(text)
        except ValueError as exc:
            self._complete_inline_turn(
                turn_id,
                text=text,
                mode="command_error",
                message=str(exc),
                summary="Slash command parsing failed.",
                controller_state="error",
            )
            return turn_id

        self._activity_stream.append_event(
            ACTIVITY_AGENT_TURN,
            "agent_host",
            "User turn received by the host controller.",
            payload={"turn_id": turn_id, "mode": command["mode"], "text_preview": text[:120]},
        )

        if command["mode"] == "tool_list":
            self._complete_inline_turn(
                turn_id,
                text=text,
                mode="tool_command",
                message=_format_tool_list(self._tool_service.list_tools()),
                summary="Tool catalog listed from slash command.",
            )
            return turn_id

        if command["mode"] == "tool":
            self._run_tool_command(turn_id, text, command)
            return turn_id

        if _requires_hitl(text):
            self._queue_hitl_gate(turn_id, text, command["mode"])
            return turn_id

        self._start_turn(turn_id, text, command["mode"])
        self._submit_background_turn(turn_id, command)
        return turn_id

    def request_stop(self) -> None:
        with self._lock:
            current = self._snapshot
            control = self._active_control
            if current.active_turn_id is None or control is None:
                return
            control.request_stop()
            self._snapshot = self._build_snapshot(
                controller_state="stopping",
                active_turn_id=current.active_turn_id,
                last_user_message=current.last_user_message,
                last_agent_message=current.last_agent_message,
                current_step=self._make_step("stop", "Stop requested for the current turn.", "requested"),
                pending_approvals=current.pending_approvals,
                evidence_summary=current.evidence_summary,
                stop_requested=True,
                pause_requested=current.pause_requested,
                current_turn_mode=current.current_turn_mode,
            )
        self._activity_stream.append_event(
            ACTIVITY_AGENT_STEP,
            "agent_host",
            "Stop requested for the current Mindshard turn.",
            level="warning",
            payload={"turn_id": current.active_turn_id},
        )

    def pause_run(self) -> None:
        with self._lock:
            current = self._snapshot
            control = self._active_control
            if current.active_turn_id is None or control is None or current.can_pause is False:
                return
            control.request_pause()
            self._snapshot = self._build_snapshot(
                controller_state="pausing",
                active_turn_id=current.active_turn_id,
                last_user_message=current.last_user_message,
                last_agent_message=current.last_agent_message,
                current_step=self._make_step("pause", "Pause requested at the next safe checkpoint.", "requested"),
                pending_approvals=current.pending_approvals,
                evidence_summary=current.evidence_summary,
                stop_requested=current.stop_requested,
                pause_requested=True,
                current_turn_mode=current.current_turn_mode,
            )
        self._activity_stream.append_event(
            ACTIVITY_AGENT_STEP,
            "agent_host",
            "Pause requested for the current Mindshard turn.",
            level="warning",
            payload={"turn_id": current.active_turn_id},
        )

    def resume_run(self) -> None:
        with self._lock:
            current = self._snapshot
            control = self._active_control
            if current.active_turn_id is None or control is None:
                return
            control.resume()
            self._snapshot = self._build_snapshot(
                controller_state="processing",
                active_turn_id=current.active_turn_id,
                last_user_message=current.last_user_message,
                last_agent_message=current.last_agent_message,
                current_step=self._make_step("resume", "Turn resumed after host pause.", "completed"),
                pending_approvals=current.pending_approvals,
                evidence_summary=current.evidence_summary,
                stop_requested=current.stop_requested,
                pause_requested=False,
                current_turn_mode=current.current_turn_mode,
            )
        self._activity_stream.append_event(
            ACTIVITY_AGENT_STEP,
            "agent_host",
            "Paused Mindshard turn resumed.",
            payload={"turn_id": current.active_turn_id},
        )

    def resolve_hitl_gate(self, approval_id: str, approved: bool, note: str = "") -> None:
        with self._lock:
            current = self._snapshot
            pending = [gate for gate in current.pending_approvals if gate.approval_id != approval_id]
            gate = next((gate for gate in current.pending_approvals if gate.approval_id == approval_id), None)
            pending_turn = self._pending_turn_by_approval_id.pop(approval_id, None)
            if gate is None or pending_turn is None:
                raise KeyError(f"Unknown approval id: {approval_id}")

            self._snapshot = self._build_snapshot(
                controller_state="processing" if approved else "idle",
                active_turn_id=pending_turn.turn_id if approved else None,
                last_user_message=current.last_user_message,
                last_agent_message=current.last_agent_message,
                current_step=self._make_step(
                    "hitl",
                    "Human approval resolved.",
                    "approved" if approved else "rejected",
                ),
                pending_approvals=pending,
                evidence_summary=current.evidence_summary,
                current_turn_mode=pending_turn.mode,
            )

        self._activity_stream.append_event(
            ACTIVITY_AGENT_HITL_RESOLVED,
            "agent_host",
            "Human approval resolved.",
            level="info" if approved else "warning",
            detail=note,
            payload={"approval_id": approval_id, "approved": approved},
        )

        if approved:
            self._submit_background_turn(
                pending_turn.turn_id,
                {"mode": pending_turn.mode, "payload": pending_turn.text},
            )
            return

        self._complete_inline_turn(
            pending_turn.turn_id,
            text=pending_turn.text,
            mode=pending_turn.mode,
            message="Human approval was declined. No agent action was taken.",
            summary="Human approval declined.",
        )

    def get_snapshot(self) -> AgentSnapshot:
        with self._lock:
            return self._snapshot

    def recent_activity(
        self,
        *,
        limit: int = 50,
        families: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        return self._activity_stream.recent_events(limit=limit, families=families)

    def subscribe_activity(self, handler) -> None:
        def adapter(event: ActivityEvent) -> None:
            handler(event.to_dict())

        self._activity_stream.subscribe(adapter)

    def _run_tool_command(self, turn_id: str, text: str, command: dict[str, Any]) -> None:
        tool_id = command["tool_id"]
        parse_error = command.get("parse_error")
        if parse_error:
            self._complete_inline_turn(
                turn_id,
                text=text,
                mode="tool_command",
                message=f"Invalid tool arguments: {parse_error}",
                summary="Slash tool command failed.",
                controller_state="error",
            )
            return

        descriptor = _find_tool_descriptor(self._tool_service.list_tools(), tool_id)
        if descriptor is None:
            self._complete_inline_turn(
                turn_id,
                text=text,
                mode="tool_command",
                message=f"Unknown tool id: {tool_id}",
                summary="Slash tool command failed.",
                controller_state="error",
            )
            return

        try:
            execution_id = self._tool_service.run_tool(
                tool_id,
                command["arguments"],
                invocation_origin="user",
                requesting_turn_id=turn_id,
                capability_class=descriptor.capability_class,
            )
        except Exception as exc:
            self._logger.exception("Slash tool command failed. tool_id=%s", tool_id)
            self._complete_inline_turn(
                turn_id,
                text=text,
                mode="tool_command",
                message=f"Tool start failed: {exc}",
                summary="Slash tool command failed.",
                controller_state="error",
            )
            return

        self._complete_inline_turn(
            turn_id,
            text=text,
            mode="tool_command",
            message=(
                f"Tool started: {descriptor.name}\n"
                f"Execution id: {execution_id}\n"
                f"Capability class: {descriptor.capability_class}"
            ),
            summary="Slash tool command executed.",
            evidence_summary={
                "state": "tool_request",
                "tool_id": descriptor.tool_id,
                "execution_id": execution_id,
                "capability_class": descriptor.capability_class,
            },
        )

    def _start_turn(self, turn_id: str, text: str, mode: str) -> None:
        with self._lock:
            self._recent_steps = []
            self._snapshot = self._build_snapshot(
                controller_state="processing",
                active_turn_id=turn_id,
                last_user_message=text,
                last_agent_message=self._snapshot.last_agent_message,
                current_step=self._make_step("submit", f"Submitting {mode} turn to Mindshard.", "running"),
                evidence_summary=self._build_preflight_evidence_summary(text, mode),
                current_turn_mode=mode,
            )

    def _submit_background_turn(self, turn_id: str, command: dict[str, Any]) -> None:
        text = command["payload"]
        mode = command["mode"]
        control = _TurnControl(self._handle_control_event)
        with self._lock:
            self._active_control = control

        if mode == "run":
            task_id = self._task_manager.submit_task(
                "mindshard.run",
                self._adapter.run_task,
                text,
                loop_name=self._session_controller.get_snapshot().current_loop,
                control=control,
                on_success=lambda result, turn_id=turn_id: self._complete_turn(turn_id, result),
                on_error=lambda task_result, turn_id=turn_id: self._fail_turn(turn_id, task_result),
                metadata={"turn_id": turn_id, "source": "mindshard", "mode": mode},
            )
        else:
            task_id = self._task_manager.submit_task(
                "mindshard.chat",
                self._adapter.send_chat,
                text,
                control=control,
                on_success=lambda result, turn_id=turn_id: self._complete_turn(turn_id, result),
                on_error=lambda task_result, turn_id=turn_id: self._fail_turn(turn_id, task_result),
                metadata={"turn_id": turn_id, "source": "mindshard", "mode": mode},
            )

        with self._lock:
            self._active_task_id = task_id

    def _queue_hitl_gate(self, turn_id: str, text: str, mode: str) -> None:
        gate = HITLGateSnapshot(
            approval_id=str(uuid.uuid4()),
            label="Approval required",
            prompt="This turn requested human confirmation before the host continues.",
            status="waiting",
            requested_at=utc_timestamp(),
            capability_class="manual",
        )
        with self._lock:
            self._pending_turn_by_approval_id[gate.approval_id] = _PendingApprovalTurn(
                turn_id=turn_id,
                text=text,
                mode=mode,
            )
            self._snapshot = self._build_snapshot(
                controller_state="awaiting_hitl",
                active_turn_id=turn_id,
                last_user_message=text,
                last_agent_message=self._snapshot.last_agent_message,
                current_step=self._make_step("hitl", "Awaiting human approval before continuing.", "waiting"),
                pending_approvals=[*self._snapshot.pending_approvals, gate],
                evidence_summary=self._build_preflight_evidence_summary(text, mode),
                current_turn_mode=mode,
            )

        self._activity_stream.append_event(
            ACTIVITY_AGENT_HITL_WAIT,
            "agent_host",
            "Host controller is waiting for human approval.",
            level="warning",
            payload={"turn_id": turn_id, "approval_id": gate.approval_id},
        )

    def _complete_turn(self, turn_id: str, result: dict[str, Any]) -> None:
        self._session_controller.refresh_snapshot()
        steps = [_step_from_payload(item) for item in result.get("steps", [])]
        with self._lock:
            current = self._snapshot
            self._recent_steps = steps[-12:]
            self._snapshot = self._build_snapshot(
                controller_state="idle",
                active_turn_id=None,
                last_user_message=current.last_user_message,
                last_agent_message=str(result.get("final_output", "")),
                current_step=steps[-1] if steps else self._make_step("complete", "Mindshard turn completed.", "completed"),
                evidence_summary=result.get("evidence_summary", current.evidence_summary),
                stop_requested=False,
                pause_requested=False,
                current_turn_mode=result.get("mode", current.current_turn_mode),
                last_completed_turn_id=turn_id,
                recent_steps=steps,
            )
            self._active_control = None
            self._active_task_id = None

        self._activity_stream.append_event(
            ACTIVITY_AGENT_STEP,
            "agent_host",
            "Mindshard turn completed.",
            payload={
                "turn_id": turn_id,
                "mode": result.get("mode", "chat"),
                "llm_calls": result.get("llm_calls", 0),
                "latency_ms": result.get("latency_ms", 0.0),
            },
        )

    def _fail_turn(self, turn_id: str, task_result: TaskResult) -> None:
        self._session_controller.refresh_snapshot()
        with self._lock:
            current = self._snapshot
            self._snapshot = self._build_snapshot(
                controller_state="error",
                active_turn_id=None,
                last_user_message=current.last_user_message,
                last_agent_message=f"Mindshard turn failed: {task_result.error_message or 'Unknown error'}",
                current_step=self._make_step("error", "Mindshard turn failed.", "failed"),
                pending_approvals=current.pending_approvals,
                evidence_summary=current.evidence_summary,
                stop_requested=False,
                pause_requested=False,
                current_turn_mode=current.current_turn_mode,
                last_completed_turn_id=turn_id,
                recent_steps=self._recent_steps,
            )
            self._active_control = None
            self._active_task_id = None

    def _complete_inline_turn(
        self,
        turn_id: str,
        *,
        text: str,
        mode: str,
        message: str,
        summary: str,
        controller_state: str = "idle",
        evidence_summary: dict[str, Any] | None = None,
    ) -> None:
        self._session_controller.refresh_snapshot()
        step = self._make_step(mode, summary, "completed" if controller_state == "idle" else controller_state)
        with self._lock:
            self._recent_steps = [step]
            self._snapshot = self._build_snapshot(
                controller_state=controller_state,
                active_turn_id=None,
                last_user_message=text,
                last_agent_message=message,
                current_step=step,
                evidence_summary=evidence_summary or self._build_preflight_evidence_summary(text, mode),
                current_turn_mode=mode,
                last_completed_turn_id=turn_id,
                recent_steps=[step],
            )
        self._activity_stream.append_event(
            ACTIVITY_AGENT_STEP,
            "agent_host",
            summary,
            level="error" if controller_state == "error" else "info",
            payload={"turn_id": turn_id, "mode": mode},
        )

    def _handle_control_event(self, state: str, phase: str, detail: str) -> None:
        with self._lock:
            current = self._snapshot
            if current.active_turn_id is None:
                return
            step = self._make_step(phase, _phase_summary(phase, detail), _phase_status(state))
            recent_steps = [*self._recent_steps, step][-12:]
            self._recent_steps = recent_steps
            controller_state = current.controller_state
            pause_requested = current.pause_requested
            can_pause = current.can_pause
            can_resume = current.can_resume
            if state == "paused":
                controller_state = "paused"
                pause_requested = True
                can_pause = False
                can_resume = True
            elif state == "resumed":
                controller_state = "processing"
                pause_requested = False
                can_pause = True
                can_resume = False
            elif state == "stopped":
                controller_state = "stopping"
                can_pause = False
                can_resume = False
            elif controller_state != "paused":
                controller_state = "processing"
                can_pause = True
                can_resume = False

            self._snapshot = self._build_snapshot(
                controller_state=controller_state,
                active_turn_id=current.active_turn_id,
                last_user_message=current.last_user_message,
                last_agent_message=current.last_agent_message,
                current_step=step,
                pending_approvals=current.pending_approvals,
                evidence_summary=current.evidence_summary,
                stop_requested=current.stop_requested or state == "stopped",
                pause_requested=pause_requested,
                current_turn_mode=current.current_turn_mode,
                recent_steps=recent_steps,
                can_pause=can_pause,
                can_resume=can_resume,
            )

        if state != "checkpoint":
            self._activity_stream.append_event(
                ACTIVITY_AGENT_STEP,
                "agent_host",
                _phase_summary(phase, detail),
                level="warning" if state == "paused" else "info",
                payload={"phase": phase, "state": state},
            )

    def _build_snapshot(
        self,
        *,
        controller_state: str,
        active_turn_id: str | None,
        last_user_message: str,
        last_agent_message: str,
        current_step: AgentStepSnapshot | None,
        pending_approvals: list[HITLGateSnapshot] | None = None,
        evidence_summary: dict[str, Any] | None = None,
        stop_requested: bool = False,
        pause_requested: bool = False,
        current_turn_mode: str = "chat",
        last_completed_turn_id: str | None = None,
        recent_steps: list[AgentStepSnapshot] | None = None,
        can_pause: bool | None = None,
        can_resume: bool | None = None,
    ) -> AgentSnapshot:
        session_snapshot = self._session_controller.get_snapshot()
        pending = pending_approvals if pending_approvals is not None else []
        recent = recent_steps if recent_steps is not None else list(self._recent_steps)
        return AgentSnapshot(
            controller_state=controller_state,
            active_turn_id=active_turn_id,
            last_user_message=last_user_message,
            last_agent_message=last_agent_message,
            current_loop=session_snapshot.current_loop,
            current_step=current_step,
            pending_approvals=pending,
            evidence_summary=evidence_summary or {},
            stop_requested=stop_requested,
            pause_requested=pause_requested,
            current_turn_mode=current_turn_mode,
            last_completed_turn_id=last_completed_turn_id,
            recent_steps=recent,
            current_model=session_snapshot.current_model,
            model_status=session_snapshot.model_status,
            session_id=session_snapshot.active_session.session_id,
            session_name=session_snapshot.active_session.name,
            can_pause=can_pause if can_pause is not None else controller_state in {"processing", "pausing"},
            can_resume=can_resume if can_resume is not None else controller_state == "paused",
            updated_at=utc_timestamp(),
        )

    def _build_preflight_evidence_summary(self, text: str, mode: str) -> dict[str, Any]:
        session_snapshot = self._session_controller.get_snapshot()
        return {
            "state": "queued",
            "mode": mode,
            "input_length": len(text),
            "available_tools": len(self._tool_service.list_tools()),
            "session_id": session_snapshot.active_session.session_id,
            "model": session_snapshot.current_model,
            "loop": session_snapshot.current_loop,
        }

    def _register_data_hooks(self) -> None:
        self._data_hook_catalog.register_hook(
            "agent.snapshot",
            family="agent",
            producer="agent_host",
            description="Current host-side agent snapshot.",
            freshness="live",
            preview_provider=lambda: self.get_snapshot().to_dict(),
        )
        self._data_hook_catalog.register_hook(
            "agent.pending_approvals",
            family="agent",
            producer="agent_host",
            description="Pending HITL approvals awaiting user action.",
            freshness="live",
            preview_provider=lambda: [gate.to_dict() for gate in self.get_snapshot().pending_approvals],
        )
        self._data_hook_catalog.register_hook(
            "agent.self_awareness",
            family="agent",
            producer="agent_host",
            description="Placeholder slot for host-owned self-awareness diagnostics.",
            freshness="live",
            preview_provider=lambda: {
                "state": "reserved",
                "enabled": False,
                "note": "Host-owned self-awareness store will attach here in a later phase.",
            },
        )

    @staticmethod
    def _make_step(phase: str, summary: str, status: str) -> AgentStepSnapshot:
        return AgentStepSnapshot(
            step_id=str(uuid.uuid4()),
            phase=phase,
            summary=summary,
            status=status,
            created_at=utc_timestamp(),
        )


def _requires_hitl(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("approve", "approval", "hitl", "human review"))


def _parse_user_turn(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("/run "):
        return {"mode": "run", "payload": stripped[5:].strip()}
    if stripped.startswith("/task "):
        return {"mode": "run", "payload": stripped[6:].strip()}
    if stripped == "/tool list":
        return {"mode": "tool_list", "payload": stripped}
    if stripped.startswith("/tool "):
        body = stripped[6:].strip()
        if not body:
            return {"mode": "tool_list", "payload": stripped}
        tool_id, _, raw_arguments = body.partition(" ")
        arguments: dict[str, Any] = {}
        if raw_arguments.strip():
            try:
                parsed = json.loads(raw_arguments.strip())
            except json.JSONDecodeError as exc:
                return {
                    "mode": "tool",
                    "payload": stripped,
                    "tool_id": tool_id,
                    "arguments": {},
                    "parse_error": str(exc),
                }
            if not isinstance(parsed, dict):
                raise ValueError("Tool arguments must decode to a JSON object.")
            arguments = parsed
        return {
            "mode": "tool",
            "payload": stripped,
            "tool_id": tool_id,
            "arguments": arguments,
            "parse_error": "",
        }
    return {"mode": "chat", "payload": text}


def _format_tool_list(tools: list[ToolDescriptor]) -> str:
    if not tools:
        return "No tools are currently available."
    lines = ["Available tools:"]
    for tool in tools:
        lines.append(f"- {tool.tool_id}: {tool.description}")
    return "\n".join(lines)


def _find_tool_descriptor(tools: list[ToolDescriptor], tool_id: str) -> ToolDescriptor | None:
    for tool in tools:
        if tool.tool_id == tool_id:
            return tool
    return None


def _phase_summary(phase: str, detail: str) -> str:
    if detail:
        return detail
    return f"Mindshard checkpoint: {phase}"


def _phase_status(state: str) -> str:
    return {
        "checkpoint": "running",
        "paused": "paused",
        "resumed": "completed",
        "stopped": "stopped",
    }.get(state, "running")


def _step_from_payload(payload: dict[str, Any]) -> AgentStepSnapshot:
    return AgentStepSnapshot(
        step_id=str(payload.get("step_id", uuid.uuid4())),
        phase=str(payload.get("phase", "")),
        summary=str(payload.get("summary", "")),
        status=str(payload.get("status", "")),
        created_at=str(payload.get("created_at", utc_timestamp())),
        detail=str(payload.get("detail", "")),
        metadata=dict(payload.get("metadata", {})),
    )
