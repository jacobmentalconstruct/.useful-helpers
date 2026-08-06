"""
Owns: the live bridge between host runtime contracts and the vendored MindSHARD runtime.
Does not own: Tk widgets, host tool policy, or chat/workspace layout behavior.
Collaborates with: host controllers and src.runtime.vendors.mindshard.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from src.runtime.vendors.mindshard import ensure_bootstrap


DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_LOOP = "plan_act_observe"
ECHO_MODEL = "echo/test"
DEFAULT_MODELS = [
    ECHO_MODEL,
    "qwen2.5:0.5b",
    "qwen2.5-coder:0.5b",
    "qwen2.5:1.5b",
    "qwen2.5-coder:1.5b",
    "qwen2.5:3b",
    "qwen2.5-coder:3b",
    "qwen2.5:7b",
    "qwen2.5-coder:7b",
]


class MindshardTurnInterrupted(RuntimeError):
    """Raised when host turn control stops execution at a safe checkpoint."""


class MindshardAdapter:
    def __init__(
        self,
        db_path: Path,
        *,
        initial_model: str | None = None,
        initial_loop: str | None = None,
        initial_session_id: str | None = None,
        use_echo: bool = False,
    ) -> None:
        self._db_path = db_path
        self._model = initial_model or DEFAULT_MODEL
        self._loop_name = initial_loop or DEFAULT_LOOP
        self._preferred_session_id = initial_session_id or ""
        self._use_echo = use_echo or self._model == ECHO_MODEL
        self._logger = logging.getLogger("runtime.mindshard")
        self._lock = threading.RLock()
        self._initialized = False
        self._imports: dict[str, Any] = {}
        self._agent = None
        self._last_error = ""

    @property
    def last_error(self) -> str:
        with self._lock:
            return self._last_error

    def initialize(self) -> None:
        with self._lock:
            if self._initialized:
                return
            self._load_imports()
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            bridge = self._build_bridge()
            loop = self._imports["get_loop"](self._loop_name)
            self._agent = self._imports["MindShardAgent"].create(
                llm=bridge,
                db_path=str(self._db_path),
                loop=loop,
                session_id=self._preferred_session_id,
            )
            self._initialized = True
            self._last_error = ""
            self._ensure_session_record("")
            self._logger.info(
                "Mindshard runtime initialized. model=%s loop=%s db=%s",
                self.model_name,
                self.loop_name,
                self._db_path,
            )

    def close(self) -> None:
        with self._lock:
            if self._agent is not None:
                self._agent.close()
            self._agent = None
            self._initialized = False

    @property
    def model_name(self) -> str:
        with self._lock:
            if self._agent is not None:
                return self._agent._llm.name()
            return ECHO_MODEL if self._use_echo else self._model

    @property
    def loop_name(self) -> str:
        with self._lock:
            if self._agent is not None:
                return self._agent.loop.name
            return self._loop_name

    @property
    def session_id(self) -> str:
        with self._lock:
            if self._agent is not None:
                return self._agent.session_id
            return self._preferred_session_id

    def runtime_status(self, *, refresh_models: bool = False) -> dict[str, Any]:
        try:
            self.initialize()
            model_status = self._probe_model_status(refresh=refresh_models)
        except Exception as exc:
            self._last_error = str(exc)
            model_status = f"Unavailable: {exc}"
        return {
            "model_name": self.model_name,
            "model_status": model_status,
            "loop_name": self.loop_name,
            "session_id": self.session_id,
            "use_echo": self._use_echo,
            "available_models": self.list_models(refresh=refresh_models),
        }

    def list_models(self, *, refresh: bool = False) -> list[str]:
        models = list(DEFAULT_MODELS)
        try:
            self._load_imports()
            if refresh and not self._use_echo:
                bridge = self._imports["OllamaBridge"](model=self._model)
                discovered = bridge.list_models()
                models.extend(discovered)
        except Exception:
            pass
        models.append(self._model)
        return list(dict.fromkeys(model for model in models if model))

    def list_loops(self) -> list[str]:
        self._load_imports()
        return list(self._imports["list_loops"]())

    def switch_model(self, model_name: str) -> None:
        self.initialize()
        with self._lock:
            if model_name == ECHO_MODEL:
                self._agent._llm = self._imports["EchoBridge"]()
                self._use_echo = True
                self._model = ECHO_MODEL
            else:
                self._agent._llm = self._imports["OllamaBridge"](model=model_name)
                self._use_echo = False
                self._model = model_name
            self._logger.info("Mindshard model switched: %s", self.model_name)

    def switch_loop(self, loop_name: str) -> None:
        self.initialize()
        with self._lock:
            self._agent.loop = self._imports["get_loop"](loop_name)
            self._loop_name = loop_name
            self._logger.info("Mindshard loop switched: %s", loop_name)

    def save_current_session(self, name: str = "") -> dict[str, Any]:
        self.initialize()
        with self._lock:
            self._agent.memory.save_session(self._agent.session_id, name)
            return self.current_session_info()

    def list_sessions(self) -> list[dict[str, Any]]:
        self.initialize()
        with self._lock:
            return self._agent.memory.list_sessions()

    def current_session_info(self) -> dict[str, Any]:
        self.initialize()
        with self._lock:
            info = self._agent.memory.load_session(self._agent.session_id)
            if info:
                return info
            return {
                "session_id": self._agent.session_id,
                "name": "",
                "created_at": "",
                "updated_at": "",
                "message_count": 0,
            }

    def load_session(self, session_id: str) -> dict[str, Any]:
        self.initialize()
        with self._lock:
            self._agent.memory.save_session(self._agent.session_id)
            self._agent._session_id = session_id
            self._preferred_session_id = session_id
            self._ensure_session_record("")
            return self.current_session_info()

    def new_session(self, name: str = "") -> dict[str, Any]:
        self.initialize()
        with self._lock:
            self._agent.memory.save_session(self._agent.session_id)
            new_id = f"sess_{uuid.uuid4().hex[:8]}"
            self._agent._session_id = new_id
            self._preferred_session_id = new_id
            self._ensure_session_record(name)
            return self.current_session_info()

    def rename_session(self, session_id: str, new_name: str) -> dict[str, Any]:
        self.initialize()
        with self._lock:
            self._agent.memory.rename_session(session_id, new_name)
            if session_id == self._agent.session_id:
                self._ensure_session_record(new_name)
            info = self._agent.memory.load_session(session_id)
            return info or self.current_session_info()

    def delete_session(self, session_id: str) -> int:
        self.initialize()
        with self._lock:
            is_current = session_id == self._agent.session_id
            removed = self._agent.memory.delete_session(session_id)
            if is_current:
                self.new_session()
            return removed

    def reset_session(self) -> dict[str, Any]:
        self.initialize()
        with self._lock:
            current = self._agent.session_id
            self._agent.memory.delete_session(current)
            return self.new_session()

    def send_chat(self, message: str, *, control=None) -> dict[str, Any]:
        self.initialize()
        started_at = time.time()
        try:
            response = self._agent.chat(message, control=control)
            stopped = False
        except MindshardTurnInterrupted:
            response = "Chat turn stopped before the next safe checkpoint."
            stopped = True
        finally:
            self._ensure_session_record("")
        summary = self._build_evidence_summary(message)
        return {
            "mode": "chat",
            "final_output": response,
            "steps": [
                {
                    "step_id": f"chat-{int(started_at * 1000)}",
                    "phase": "chat",
                    "summary": "Mindshard chat response completed.",
                    "detail": response,
                    "status": "stopped" if stopped else "completed",
                    "created_at": summary["captured_at"],
                    "metadata": {"llm_calls": 1},
                }
            ],
            "llm_calls": 1,
            "latency_ms": (time.time() - started_at) * 1000,
            "evidence_summary": summary,
            "stopped": stopped,
        }

    def run_task(self, task: str, *, loop_name: str = "", control=None) -> dict[str, Any]:
        self.initialize()
        loop_override = None
        if loop_name and loop_name != self.loop_name:
            loop_override = self._imports["get_loop"](loop_name)
        try:
            result = self._agent.run(task, loop=loop_override, control=control)
            stopped = False
            final_output = result.final_output
            llm_calls = result.total_llm_calls
            latency_ms = result.total_latency_ms
            trace_steps = result.trace
        except MindshardTurnInterrupted:
            stopped = True
            final_output = "Run stopped before the next safe checkpoint."
            llm_calls = 0
            latency_ms = 0.0
            trace_steps = []
        finally:
            self._ensure_session_record("")
        summary = self._build_evidence_summary(task)
        return {
            "mode": "run",
            "final_output": final_output,
            "steps": [
                {
                    "step_id": f"step-{index}",
                    "phase": step.phase,
                    "summary": step.description,
                    "detail": step.output_text,
                    "status": "stopped" if stopped else "completed",
                    "created_at": summary["captured_at"],
                    "metadata": {
                        "input_summary": step.input_summary,
                        "memories_recalled": step.memories_recalled,
                        "memories_created": step.memories_created,
                        "llm_calls": step.llm_calls,
                        "latency_ms": step.latency_ms,
                        **step.metadata,
                    },
                }
                for index, step in enumerate(trace_steps, start=1)
            ],
            "llm_calls": llm_calls,
            "latency_ms": latency_ms,
            "evidence_summary": summary,
            "stopped": stopped,
        }

    def _build_evidence_summary(self, query: str) -> dict[str, Any]:
        self.initialize()
        recall = self._agent.memory.reflect(query=query, budget=6)
        kernel_stats = self._agent.memory.kernel.stats()
        return {
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "memory_count": len(recall.memories),
            "memory_ids": [entry.memory_id for entry in recall.memories[:5]],
            "memory_kinds": [entry.kind.value for entry in recall.memories[:5]],
            "projection_nodes": recall.stats.get("projection_nodes", 0),
            "candidates_before_filter": recall.stats.get("candidates_before_filter", 0),
            "candidates_after_filter": recall.stats.get("candidates_after_filter", 0),
            "lens_profile": recall.stats.get("lens_profile", ""),
            "interrogated_preview": (recall.interrogated_context or "")[:400],
            "kernel_stats": kernel_stats,
        }

    def _ensure_session_record(self, name: str) -> None:
        self._agent.memory.save_session(self._agent.session_id, name)

    def _probe_model_status(self, *, refresh: bool = False) -> str:
        if self._use_echo:
            return "Echo/test ready"
        if not refresh:
            return "Configured"
        self._load_imports()
        bridge = self._imports["OllamaBridge"](model=self._model)
        return "Ready" if bridge.is_available() else f"Unavailable: {self._model}"

    def _build_bridge(self):
        if self._use_echo or self._model == ECHO_MODEL:
            self._use_echo = True
            self._model = ECHO_MODEL
            return self._imports["EchoBridge"]()
        return self._imports["OllamaBridge"](model=self._model)

    def _load_imports(self) -> None:
        if self._imports:
            return
        ensure_bootstrap()
        from agent.loops import get_loop, list_loops
        from agent.shell import MindShardAgent
        from bridge.llm import EchoBridge, OllamaBridge

        self._imports = {
            "MindShardAgent": MindShardAgent,
            "EchoBridge": EchoBridge,
            "OllamaBridge": OllamaBridge,
            "get_loop": get_loop,
            "list_loops": list_loops,
        }
