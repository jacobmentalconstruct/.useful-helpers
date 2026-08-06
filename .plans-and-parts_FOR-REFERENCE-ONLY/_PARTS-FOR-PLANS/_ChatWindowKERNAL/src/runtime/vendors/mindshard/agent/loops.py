"""
agent.loops — Swappable execution loops.

Each loop implements the same AgentLoop protocol but sequences
the think/act/observe cycle differently. Register new loops
by subclassing AgentLoop and passing them to MindShardAgent.

Built-in loops:
  - PlanActObserveLoop:  plan all steps → execute sequentially → reflect
  - ReactLoop:           single-step reasoning + action (no upfront plan)
  - IterativeRefinement: implement → evaluate → refine until confidence threshold

Usage::

    from agent.loops import ReactLoop, PlanActObserveLoop
    from agent.shell import MindShardAgent
    from bridge.llm import EchoBridge

    # Use the default plan-first loop
    agent = MindShardAgent.create(llm=EchoBridge(), loop=PlanActObserveLoop())

    # Swap in the react loop
    agent = MindShardAgent.create(llm=EchoBridge(), loop=ReactLoop())
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from core.projector.ltm.memory import (
    AgentMemory, MemoryKind, RecallStrategy,
)
from bridge.llm import LLMBridge

logger = logging.getLogger(__name__)


class ExecutionControl(Protocol):
    """Host-owned safe-checkpoint control for pause/stop orchestration."""

    def checkpoint(self, phase: str, detail: str = "") -> None:
        ...


# ── Shared types ─────────────────────────────────────────────────────

@dataclass
class LoopStep:
    """One step in the loop's execution trace."""
    phase: str               # "think", "act", "observe", "reflect", "react"
    step_number: int
    description: str
    input_summary: str = ""
    output_text: str = ""
    memories_recalled: int = 0
    memories_created: int = 0
    llm_calls: int = 0
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoopResult:
    """What a loop produces."""
    final_output: str
    trace: List[LoopStep] = field(default_factory=list)
    memories_created: List[str] = field(default_factory=list)
    total_llm_calls: int = 0
    total_latency_ms: float = 0.0

    @property
    def success(self) -> bool:
        return bool(self.final_output)


# ── Loop protocol ────────────────────────────────────────────────────

class AgentLoop(ABC):
    """
    Abstract execution loop. Subclass this to create new loop strategies.

    The shell provides:
      - llm:      the LLM bridge for generation
      - memory:   the LTM layer for recall/remember
      - session_id: scoping for memories

    Your loop decides how to sequence calls to these.
    """

    @abstractmethod
    def execute(
        self,
        task: str,
        llm: LLMBridge,
        memory: AgentMemory,
        session_id: str,
        recall_strategy: RecallStrategy,
        recall_budget: int,
        control: ExecutionControl | None = None,
    ) -> LoopResult:
        """Run the loop on a task. Return the result."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable loop name."""
        ...


# ── Prompt templates ─────────────────────────────────────────────────

_SYSTEM = """You are a focused task executor inside the MindSHARD agent system.
You have access to long-term memory from previous sessions.
Always respond with valid JSON. No markdown fences or extra text."""


def _call_llm(llm: LLMBridge, prompt: str, max_tokens: int = 2048) -> dict:
    """Call LLM and parse JSON response. Returns {} on failure."""
    resp = llm.generate(prompt, system=_SYSTEM, max_tokens=max_tokens)
    if not resp.ok:
        return {"_error": resp.error, "_latency": resp.latency_ms}
    try:
        parsed = json.loads(resp.text)
        parsed["_latency"] = resp.latency_ms
        return parsed
    except json.JSONDecodeError:
        return {"_raw": resp.text, "_latency": resp.latency_ms}


def _recall_context(
    memory: AgentMemory,
    query: str,
    strategy: RecallStrategy,
    budget: int,
    mode: str = "chat",
) -> tuple:
    """Recall and return (context_string, memory_count)."""
    result = memory.reflect(query=query, strategy=strategy, budget=budget, mode=mode)
    ctx = result.interrogated_context or "(no relevant memories)"
    return ctx, len(result.memories)


def _checkpoint(control: ExecutionControl | None, phase: str, detail: str = "") -> None:
    if control is not None:
        control.checkpoint(phase, detail)


# ══════════════════════════════════════════════════════════════════════
# Loop 1: Plan → Act → Observe (the default)
# ══════════════════════════════════════════════════════════════════════

class PlanActObserveLoop(AgentLoop):
    """
    Plan all steps upfront, then execute sequentially with
    observation after each step. Reflects at the end.

    Good for: well-defined tasks, code generation, multi-step builds.
    """

    def __init__(self, max_steps: int = 10) -> None:
        self._max_steps = max_steps

    @property
    def name(self) -> str:
        return "plan_act_observe"

    def execute(
        self,
        task,
        llm,
        memory,
        session_id,
        recall_strategy,
        recall_budget,
        control: ExecutionControl | None = None,
    ) -> LoopResult:
        t0 = time.time()
        trace: List[LoopStep] = []
        created: List[str] = []
        llm_calls = 0

        # Store task
        task_mem = memory.remember(task, MemoryKind.PLAN, ["task"], session_id)
        created.append(task_mem.memory_id)

        # ── THINK ─────────────────────────────────────────────────
        _checkpoint(control, "think", "Planning task execution.")
        ctx, mem_count = _recall_context(memory, task, recall_strategy, recall_budget)
        plan_data = _call_llm(llm, f"Decompose this task into steps.\n\nTASK: {task}\n\nMEMORY:\n{ctx}\n\nRespond with JSON: {{\"plan\": [{{\"step\": 1, \"action\": \"...\", \"description\": \"...\"}}], \"reasoning\": \"...\"}}")
        llm_calls += 1

        plan = plan_data.get("plan", [])
        trace.append(LoopStep(
            phase="think", step_number=1,
            description=f"Plan: {len(plan)} steps",
            output_text=plan_data.get("reasoning", ""),
            memories_recalled=mem_count, llm_calls=1,
            latency_ms=plan_data.get("_latency", 0),
            metadata={"plan": plan},
        ))

        # ── ACT + OBSERVE per step ────────────────────────────────
        outputs = []
        for i, step_info in enumerate(plan[:self._max_steps]):
            desc = step_info.get("description", f"Step {i+1}")

            # ACT
            _checkpoint(control, "act", desc)
            ctx, mc = _recall_context(memory, f"{task} — {desc}", recall_strategy, 4, "explain")
            prev = "\n".join(f"Step {j+1}: {o[:150]}" for j, o in enumerate(outputs)) or "(first step)"

            act_data = _call_llm(llm,
                f"Execute this step.\n\nTASK: {task}\nSTEP {i+1}/{len(plan)}: {desc}\n\nMEMORY:\n{ctx}\n\nPREVIOUS:\n{prev}\n\n"
                f"Respond with JSON: {{\"code\": \"...\", \"language\": \"python\", \"explanation\": \"...\", \"output\": \"...\"}}", max_tokens=4096)
            llm_calls += 1

            # Prefer code > output > explanation, skipping empty strings
            output = (act_data.get("code") or "").strip() or (act_data.get("output") or "").strip() or (act_data.get("explanation") or "").strip()
            outputs.append(output)

            trace.append(LoopStep(
                phase="act", step_number=len(trace)+1,
                description=desc, output_text=output,
                memories_recalled=mc, llm_calls=1,
                latency_ms=act_data.get("_latency", 0),
                metadata={"code": act_data.get("code", ""), "step_index": i+1},
            ))

            # OBSERVE
            _checkpoint(control, "observe", f"Evaluate {desc}")
            obs_data = _call_llm(llm,
                f"Evaluate this result.\n\nTASK: {task}\nACTION: {desc}\nRESULT: {output[:800]}\n\n"
                f"Respond with JSON: {{\"evaluation\": \"...\", \"issues\": [], \"confidence\": 0.85, \"should_continue\": true}}")
            llm_calls += 1

            trace.append(LoopStep(
                phase="observe", step_number=len(trace)+1,
                description=f"Evaluate step {i+1}",
                output_text=obs_data.get("evaluation", ""),
                llm_calls=1, latency_ms=obs_data.get("_latency", 0),
                metadata={"confidence": obs_data.get("confidence", 0.5),
                          "should_continue": obs_data.get("should_continue", True)},
            ))

            # Store result
            _checkpoint(control, "remember", f"Store result for {desc}")
            mem = memory.remember(
                f"Step {i+1}: {desc}\nResult: {output[:500]}",
                MemoryKind.OBSERVATION, ["step_result"], session_id,
                links_to=[task_mem.memory_id],
            )
            created.append(mem.memory_id)

            if not obs_data.get("should_continue", True):
                break

        # ── REFLECT ───────────────────────────────────────────────
        _checkpoint(control, "reflect", "Generating post-task reflection.")
        summary = "\n".join(f"[{s.phase}] {s.description}: {s.output_text[:80]}" for s in trace)
        ref_data = _call_llm(llm,
            f"Reflect on the task.\n\nTASK: {task}\nTRACE:\n{summary}\n\n"
            f"Respond with JSON: {{\"reflection\": \"...\", \"lessons\": [], \"should_remember\": true, \"memory_text\": \"...\"}}")
        llm_calls += 1

        if ref_data.get("should_remember", True):
            mem = memory.remember(
                ref_data.get("memory_text", ref_data.get("reflection", "")),
                MemoryKind.REFLECTION, ["reflection"], session_id,
                links_to=[task_mem.memory_id],
            )
            created.append(mem.memory_id)

        trace.append(LoopStep(
            phase="reflect", step_number=len(trace)+1,
            description="Post-task reflection",
            output_text=ref_data.get("reflection", ""),
            llm_calls=1, latency_ms=ref_data.get("_latency", 0),
        ))

        # Assemble
        final = "\n\n".join(f"# Step {i+1}\n{o}" for i, o in enumerate(outputs) if o)
        if ref_data.get("reflection"):
            final += f"\n\n# Reflection\n{ref_data['reflection']}"

        return LoopResult(
            final_output=final or "(no output)",
            trace=trace, memories_created=created,
            total_llm_calls=llm_calls,
            total_latency_ms=(time.time() - t0) * 1000,
        )


# ══════════════════════════════════════════════════════════════════════
# Loop 2: ReAct (Reasoning + Acting, single-step)
# ══════════════════════════════════════════════════════════════════════

class ReactLoop(AgentLoop):
    """
    No upfront plan. Each iteration: reason about what to do next,
    do it, observe the result, decide whether to continue.

    Good for: exploratory tasks, debugging, open-ended questions.
    """

    def __init__(self, max_iterations: int = 8) -> None:
        self._max_iter = max_iterations

    @property
    def name(self) -> str:
        return "react"

    def execute(
        self,
        task,
        llm,
        memory,
        session_id,
        recall_strategy,
        recall_budget,
        control: ExecutionControl | None = None,
    ) -> LoopResult:
        t0 = time.time()
        trace: List[LoopStep] = []
        created: List[str] = []
        llm_calls = 0

        task_mem = memory.remember(task, MemoryKind.PLAN, ["task"], session_id)
        created.append(task_mem.memory_id)

        history = []
        final_output = ""

        for iteration in range(self._max_iter):
            _checkpoint(control, "react", f"React iteration {iteration + 1}")
            ctx, mc = _recall_context(memory, task, recall_strategy, recall_budget)
            hist_text = "\n".join(history[-6:]) or "(start)"

            react_data = _call_llm(llm,
                f"You are working on: {task}\n\nMEMORY:\n{ctx}\n\nHISTORY:\n{hist_text}\n\n"
                f"What should you do next? If the task is complete, set finished=true.\n\n"
                f"Respond with JSON: {{\"thought\": \"...\", \"action\": \"...\", \"result\": \"...\", "
                f"\"finished\": false}}", max_tokens=4096)
            llm_calls += 1

            thought = react_data.get("thought", "")
            action = react_data.get("action", "")
            result = react_data.get("result", "")
            finished = react_data.get("finished", False)

            history.append(f"Thought: {thought}\nAction: {action}\nResult: {result}")

            trace.append(LoopStep(
                phase="react", step_number=len(trace)+1,
                description=f"React #{iteration+1}: {thought[:50]}",
                output_text=result, memories_recalled=mc,
                llm_calls=1, latency_ms=react_data.get("_latency", 0),
                metadata={"thought": thought, "action": action, "finished": finished},
            ))

            _checkpoint(control, "remember", f"Store react iteration {iteration + 1}")
            mem = memory.remember(
                f"React step: {thought}\nAction: {action}\nResult: {result[:300]}",
                MemoryKind.OBSERVATION, ["react_step"], session_id,
                links_to=[task_mem.memory_id],
            )
            created.append(mem.memory_id)

            if result:
                final_output = result

            if finished:
                break

        return LoopResult(
            final_output=final_output or "\n".join(h for h in history),
            trace=trace, memories_created=created,
            total_llm_calls=llm_calls,
            total_latency_ms=(time.time() - t0) * 1000,
        )


# ══════════════════════════════════════════════════════════════════════
# Loop 3: Iterative Refinement
# ══════════════════════════════════════════════════════════════════════

class IterativeRefinementLoop(AgentLoop):
    """
    Implement once, then iteratively evaluate and refine until
    confidence exceeds a threshold.

    Good for: code generation, writing, anything that benefits from drafts.
    """

    def __init__(
        self,
        max_iterations: int = 5,
        confidence_threshold: float = 0.8,
    ) -> None:
        self._max_iter = max_iterations
        self._threshold = confidence_threshold

    @property
    def name(self) -> str:
        return "iterative_refinement"

    def execute(
        self,
        task,
        llm,
        memory,
        session_id,
        recall_strategy,
        recall_budget,
        control: ExecutionControl | None = None,
    ) -> LoopResult:
        t0 = time.time()
        trace: List[LoopStep] = []
        created: List[str] = []
        llm_calls = 0

        task_mem = memory.remember(task, MemoryKind.PLAN, ["task"], session_id)
        created.append(task_mem.memory_id)

        ctx, mc = _recall_context(memory, task, recall_strategy, recall_budget)

        # Initial implementation
        _checkpoint(control, "act", "Generating initial implementation.")
        impl_data = _call_llm(llm,
            f"Implement this task.\n\nTASK: {task}\n\nMEMORY:\n{ctx}\n\n"
            f"Respond with JSON: {{\"code\": \"...\", \"language\": \"python\", \"explanation\": \"...\"}}",
            max_tokens=4096)
        llm_calls += 1

        current = impl_data.get("code") or impl_data.get("explanation", "")
        trace.append(LoopStep(
            phase="act", step_number=1, description="Initial implementation",
            output_text=current, memories_recalled=mc, llm_calls=1,
            latency_ms=impl_data.get("_latency", 0),
        ))

        # Refine loop
        for iteration in range(self._max_iter):
            # Evaluate
            _checkpoint(control, "observe", f"Evaluate draft {iteration + 1}")
            eval_data = _call_llm(llm,
                f"Evaluate this implementation.\n\nTASK: {task}\nIMPLEMENTATION:\n{current[:2000]}\n\n"
                f"Respond with JSON: {{\"evaluation\": \"...\", \"issues\": [], \"suggestions\": [], "
                f"\"confidence\": 0.0}}")
            llm_calls += 1

            confidence = eval_data.get("confidence", 0.5)
            issues = eval_data.get("issues", [])

            trace.append(LoopStep(
                phase="observe", step_number=len(trace)+1,
                description=f"Evaluate draft #{iteration+1}",
                output_text=eval_data.get("evaluation", ""),
                llm_calls=1, latency_ms=eval_data.get("_latency", 0),
                metadata={"confidence": confidence, "issues": issues},
            ))

            if confidence >= self._threshold or not issues:
                break

            # Refine
            _checkpoint(control, "act", f"Refine draft {iteration + 1}")
            refine_data = _call_llm(llm,
                f"Refine this implementation based on feedback.\n\nTASK: {task}\n"
                f"CURRENT:\n{current[:2000]}\nISSUES: {json.dumps(issues)}\n"
                f"SUGGESTIONS: {json.dumps(eval_data.get('suggestions', []))}\n\n"
                f"Respond with JSON: {{\"code\": \"...\", \"changes\": \"what changed\"}}",
                max_tokens=4096)
            llm_calls += 1

            refined = refine_data.get("code", "")
            if refined:
                current = refined

            trace.append(LoopStep(
                phase="act", step_number=len(trace)+1,
                description=f"Refine #{iteration+1}",
                output_text=refine_data.get("changes", ""),
                llm_calls=1, latency_ms=refine_data.get("_latency", 0),
            ))

        # Store final
        _checkpoint(control, "remember", "Store final implementation artifact.")
        mem = memory.remember(
            f"Final implementation:\n{current[:1000]}",
            MemoryKind.ARTIFACT, ["implementation", "final"], session_id,
            links_to=[task_mem.memory_id],
        )
        created.append(mem.memory_id)

        return LoopResult(
            final_output=current or "(no output)",
            trace=trace, memories_created=created,
            total_llm_calls=llm_calls,
            total_latency_ms=(time.time() - t0) * 1000,
        )


# ── Registry ─────────────────────────────────────────────────────────

LOOP_REGISTRY: Dict[str, type] = {
    "plan_act_observe": PlanActObserveLoop,
    "react": ReactLoop,
    "iterative_refinement": IterativeRefinementLoop,
}


def get_loop(name: str, **kwargs) -> AgentLoop:
    """Get a loop by name from the registry."""
    cls = LOOP_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown loop: {name!r}. Available: {list(LOOP_REGISTRY.keys())}")
    return cls(**kwargs)


def list_loops() -> List[str]:
    """Return available loop names."""
    return list(LOOP_REGISTRY.keys())
