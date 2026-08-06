"""
agent.shell — MindSHARD Agent orchestration shell.

The shell is the conductor. It owns the session, memory, and LLM bridge.
The LOOP controls the sequencing. Loops are swappable — pass any AgentLoop
implementation and the shell runs it with the same memory + LLM substrate.

Built-in loops (in agent.loops):
  - PlanActObserveLoop:      plan → execute → evaluate → reflect
  - ReactLoop:               reason + act in single-step cycles
  - IterativeRefinementLoop: draft → evaluate → refine until confident

Usage::

    from agent import MindShardAgent
    from agent.loops import PlanActObserveLoop, ReactLoop
    from bridge.llm import EchoBridge

    # Default loop
    agent = MindShardAgent.create(llm=EchoBridge())
    result = agent.run("Build a function that validates email addresses")

    # Swap the loop
    agent = MindShardAgent.create(llm=EchoBridge(), loop=ReactLoop())
    result = agent.run("Debug this auth issue")

    # Multi-turn conversation
    agent.chat("What did we build last session?")
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import core  # triggers sys.path setup
from core.projector.ltm.memory import (
    AgentMemory, MemoryEntry, MemoryKind, RecallStrategy,
)
from bridge.llm import LLMBridge
from .loops import (
    AgentLoop, LoopResult, LoopStep,
    PlanActObserveLoop, ReactLoop, IterativeRefinementLoop,
    ExecutionControl, get_loop, list_loops, LOOP_REGISTRY,
)

logger = logging.getLogger(__name__)


# Keys whose values are internal IDs / URIs, not user-facing text.
_SKIP_KEYS = frozenset({
    "evidence_id", "memory_id", "artifact_id", "source_id",
    "session_id", "id", "type", "kind", "phase",
})


def _extract_text_from_json(obj: Any, depth: int = 0, key: str = "") -> str:
    """
    Recursively pull readable strings out of an arbitrary JSON structure.
    Used as a last-resort when the model ignores the natural-language
    instruction and spits out structured data anyway.
    Skips internal ID fields and memory:// URIs.
    """
    if depth > 5:
        return ""
    if isinstance(obj, str):
        # Skip internal URIs and very short tokens
        if key in _SKIP_KEYS or obj.startswith("memory://") or len(obj) < 4:
            return ""
        return obj
    if isinstance(obj, dict):
        parts = []
        for k, v in obj.items():
            t = _extract_text_from_json(v, depth + 1, key=k)
            if t:
                parts.append(t)
        return " ".join(parts)
    if isinstance(obj, list):
        parts = []
        for item in obj:
            t = _extract_text_from_json(item, depth + 1, key=key)
            if t:
                parts.append(t)
        return " ".join(parts)
    return ""


# ── Result type ──────────────────────────────────────────────────────

@dataclass
class AgentResult:
    """Final output from an agent run."""
    task: str
    final_output: str
    loop_name: str = ""
    trace: List[LoopStep] = field(default_factory=list)
    memories_created: List[str] = field(default_factory=list)
    total_llm_calls: int = 0
    total_latency_ms: float = 0.0
    session_id: str = ""

    @property
    def success(self) -> bool:
        return bool(self.final_output)


# ══════════════════════════════════════════════════════════════════════
# MindShardAgent
# ══════════════════════════════════════════════════════════════════════

_SYSTEM_CHAT = """You are a thoughtful conversational AI inside the MindSHARD agent system.
You have access to long-term memory from previous conversations.
Respond in clear, natural language. Be direct and substantive.
Do NOT respond with JSON, code fences, or structured data — just speak naturally."""


class MindShardAgent:
    """
    The orchestration shell. Holds memory + LLM + loop.
    The loop is swappable at construction or per-run.
    """

    def __init__(
        self,
        llm: LLMBridge,
        memory: AgentMemory,
        loop: Optional[AgentLoop] = None,
        session_id: str = "",
        recall_strategy: RecallStrategy = RecallStrategy.BALANCED,
        recall_budget: int = 6,
    ) -> None:
        self._llm = llm
        self._memory = memory
        self._loop = loop or PlanActObserveLoop()
        self._session_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"
        self._strategy = recall_strategy
        self._recall_budget = recall_budget

    @classmethod
    def create(
        cls,
        llm: LLMBridge,
        db_path: str = ":memory:",
        loop: Optional[AgentLoop] = None,
        session_id: str = "",
        **kwargs,
    ) -> "MindShardAgent":
        """Factory that creates agent + memory together."""
        memory = AgentMemory.create(db_path=db_path, semantic_backend="none")
        return cls(llm=llm, memory=memory, loop=loop, session_id=session_id, **kwargs)

    @property
    def memory(self) -> AgentMemory:
        return self._memory

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def loop(self) -> AgentLoop:
        return self._loop

    @loop.setter
    def loop(self, new_loop: AgentLoop) -> None:
        """Swap the execution loop at runtime."""
        self._loop = new_loop
        logger.info("Loop swapped to: %s", new_loop.name)

    def close(self) -> None:
        self._memory.close()

    # ══════════════════════════════════════════════════════════════════
    # Run — delegates to the active loop
    # ══════════════════════════════════════════════════════════════════

    def run(
        self,
        task: str,
        loop: Optional[AgentLoop] = None,
        control: ExecutionControl | None = None,
    ) -> AgentResult:
        """
        Execute a task using the active loop (or an override).

        Args:
            task: The task description in natural language.
            loop: Optional one-shot loop override (doesn't change the default).

        Returns:
            AgentResult with output, trace, and memory IDs.
        """
        active_loop = loop or self._loop

        logger.info("Running task with loop=%s: %s", active_loop.name, task[:60])

        loop_result = active_loop.execute(
            task=task,
            llm=self._llm,
            memory=self._memory,
            session_id=self._session_id,
            recall_strategy=self._strategy,
            recall_budget=self._recall_budget,
            control=control,
        )

        return AgentResult(
            task=task,
            final_output=loop_result.final_output,
            loop_name=active_loop.name,
            trace=loop_result.trace,
            memories_created=loop_result.memories_created,
            total_llm_calls=loop_result.total_llm_calls,
            total_latency_ms=loop_result.total_latency_ms,
            session_id=self._session_id,
        )

    # ══════════════════════════════════════════════════════════════════
    # Chat — conversational interface
    # ══════════════════════════════════════════════════════════════════

    def _trim_context_to_fit(
        self, context: str, message: str, system: str,
    ) -> str:
        """
        Trim the memory context block so the total prompt fits inside
        the LLM's context window.  Cuts from the END of the context
        (least-relevant memories appear last from the evidence bag).

        If the LLM bridge doesn't expose context sizing (e.g. EchoBridge),
        returns the context unchanged.
        """
        estimate = getattr(self._llm, "estimate_tokens", None)
        max_prompt = getattr(self._llm, "max_prompt_tokens", None)
        if not (estimate and max_prompt):
            return context

        budget = max_prompt()
        # Tokens consumed by everything except memory context
        fixed_tokens = (
            estimate(system)
            + estimate(message)
            + estimate("MEMORY CONTEXT:\n\n\nUSER MESSAGE:\n\n\nRespond directly in natural language.")
        )
        available = budget - fixed_tokens
        if available <= 0:
            logger.warning("Prompt overhead alone exceeds token budget; sending without context")
            return ""

        ctx_tokens = estimate(context)
        if ctx_tokens <= available:
            return context  # fits fine

        # Truncate by character ratio
        ratio = available / ctx_tokens
        truncated = context[: int(len(context) * ratio)]
        # Cut at last complete line to avoid garbled markdown
        last_nl = truncated.rfind("\n")
        if last_nl > 0:
            truncated = truncated[:last_nl]

        logger.info(
            "Context trimmed: %d → %d est. tokens (budget=%d, fixed=%d)",
            ctx_tokens, estimate(truncated), budget, fixed_tokens,
        )
        return truncated

    def chat(self, message: str, control: ExecutionControl | None = None) -> str:
        """
        Single-turn conversational interface with memory.

        Uses a natural-language system prompt so the model responds
        conversationally rather than emitting raw JSON structures.
        Context is trimmed to fit the model's actual context window.
        """
        if control is not None:
            control.checkpoint("chat.receive", "Received a chat turn.")
        self._memory.remember(
            text=f"User: {message}",
            kind=MemoryKind.CONVERSATION,
            tags=["user_message"],
            session_id=self._session_id,
        )

        if control is not None:
            control.checkpoint("chat.recall", "Recalling conversational context.")
        recall = self._memory.reflect(
            query=message,
            strategy=self._strategy,
            budget=self._recall_budget,
        )
        context = recall.interrogated_context or ""

        # Trim context to fit the model's context window
        context = self._trim_context_to_fit(context, message, _SYSTEM_CHAT)

        prompt = (
            f"MEMORY CONTEXT:\n{context}\n\n"
            f"USER MESSAGE:\n{message}\n\n"
            f"Respond directly in natural language."
        )
        if control is not None:
            control.checkpoint("chat.generate", "Generating the chat response.")
        resp = self._llm.generate(prompt, system=_SYSTEM_CHAT)

        response_text = ""
        if resp.ok:
            raw = resp.text.strip()
            # Strip markdown code fences small models sometimes emit
            if raw.startswith("```"):
                first_nl = raw.find("\n")
                if first_nl != -1:
                    raw = raw[first_nl + 1:]
                if raw.rstrip().endswith("```"):
                    raw = raw.rstrip()[:-3].rstrip()
            # If the model still emitted JSON despite being told not to,
            # try to extract something readable from it.
            if raw.startswith("{"):
                try:
                    parsed = json.loads(raw)
                    # Hunt for any human-readable value
                    response_text = (
                        parsed.get("response")
                        or parsed.get("text")
                        or parsed.get("answer")
                        or parsed.get("explanation")
                        or parsed.get("reflection")
                        or parsed.get("evaluation")
                        or parsed.get("thought")
                        or parsed.get("result")
                        or ""
                    )
                    # If no known key, concatenate all string values
                    if not response_text:
                        response_text = _extract_text_from_json(parsed)
                except (json.JSONDecodeError, AttributeError):
                    pass
            # Fall back to raw text if nothing extracted
            if not response_text:
                response_text = raw
        else:
            response_text = f"(error: {resp.error})"

        if control is not None:
            control.checkpoint("chat.store_response", "Storing the chat response.")
        self._memory.remember(
            text=f"Agent: {response_text[:500]}",
            kind=MemoryKind.CONVERSATION,
            tags=["agent_response"],
            session_id=self._session_id,
        )

        return response_text

    # ══════════════════════════════════════════════════════════════════
    # Utilities
    # ══════════════════════════════════════════════════════════════════

    def stats(self) -> Dict[str, Any]:
        """Agent + memory stats."""
        return {
            "session_id": self._session_id,
            "loop": self._loop.name,
            "llm": self._llm.name(),
            "recall_strategy": self._strategy.value,
            "memory": self._memory.stats(),
        }

    @staticmethod
    def available_loops() -> List[str]:
        """List all registered loop names."""
        return list_loops()
