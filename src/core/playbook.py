"""
FILE:       src/core/playbook.py
ROLE:       Playbook runner  -  compose registered tools into an ordered workflow.
DOMAIN:     core (orchestration - above tools, below the entrances)
DOES:       Run a list of steps [{id?, tool, args}] through the invoke() seam in order. Each
            step's structured output is bound to its id; later steps reference it with
            "@<id>.<dotted.path>" args (whole-string refs only). Stops on the first failure
            unless stop_on_error=False. Returns a structured run report.
DEPENDS ON: src.core.invoke, src.core.config, src.lib.logging_setup
WIRES TO:   called by interfaces.cli (run-playbook) and interfaces.mcp_server (playbook/run)
NOTES:      Not a leaf tool  -  orchestration belongs in the control plane (leaf tools are
            subprocess-isolated and never import src.core). Every step still routes through the
            one invoke() seam, so governance added there applies to playbooks too.
"""
from __future__ import annotations

import re

from src.core.config import Paths
from src.core.invoke import invoke
from src.lib.logging_setup import get_logger

log = get_logger("core.playbook")

# A reference is a whole-string '@<id>.<dotted.path>' with NO whitespace, so ordinary prose
# that merely starts with '@' is left literal. '@@' escapes a literal leading '@'.
_REF_RE = re.compile(r"@[^\s@]+\.[^\s@]+")


def _lookup(context: dict, path: str):
    cur = context
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            if part not in cur:
                raise KeyError(path)
            cur = cur[part]
        else:
            raise KeyError(path)
    return cur


def _resolve_refs(value, context: dict):
    """Resolve whole-string '@id.path' refs against prior step outputs. '@@' escapes a literal @."""
    if isinstance(value, str):
        if value.startswith("@@"):
            return value[1:]
        if _REF_RE.fullmatch(value):
            return _lookup(context, value[1:])
        return value
    if isinstance(value, dict):
        return {k: _resolve_refs(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_refs(v, context) for v in value]
    return value


def run_playbook(paths: Paths, steps: list, *, stop_on_error: bool = True) -> dict:
    """Run an ordered list of {id?, tool, args} steps through invoke(); return a run report."""
    if not isinstance(steps, list):
        return {"ok": False, "error": "playbook must be a list of steps", "steps": []}

    context: dict = {}
    reports: list[dict] = []
    completed = 0
    failed_at = None

    for index, step in enumerate(steps):
        sid = str(step.get("id", index))
        tool = step.get("tool")
        if not tool:
            reports.append({"id": sid, "ok": False, "error": "step missing 'tool'"})
            failed_at = sid
            if stop_on_error:
                break
            continue
        try:
            args = _resolve_refs(step.get("args", {}) or {}, context)
        except (KeyError, IndexError, ValueError) as e:
            reports.append({"id": sid, "tool": tool, "ok": False, "error": f"unresolved ref: {e}"})
            failed_at = sid
            if stop_on_error:
                break
            continue

        # A chain step is a WORKFLOW caller, not an anonymous one. Left unattributed
        # every step of every chain recorded as "unknown" - and chains are how the
        # daily drivers will be expressed, so the whole of T7 would have been
        # invisible in the shared record.
        result = invoke(paths, tool, args, client="workflow")
        context[sid] = result.output if isinstance(result.output, dict) else {}
        reports.append({"id": sid, "tool": tool, "ok": result.ok,
                        "output": result.output, "error": result.error})
        if result.ok:
            completed += 1
        else:
            failed_at = sid
            log.warning("playbook step %s (%s) failed: %s", sid, tool, result.error)
            if stop_on_error:
                break

    return {"ok": failed_at is None, "count": len(steps), "completed": completed,
            "failed_at": failed_at, "steps": reports}
