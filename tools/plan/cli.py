"""
FILE:       tools/plan/cli.py
ROLE:       The planner ENGINE - turn an intention + a project map into a real, governed project.
DOMAIN:     tool
DOES:       propose: draft a project map from intent (local model; degrades to an archetype).
            preview: validate the map and show the WHOLE plan (genesis + scaffold + provenance +
            journal) without writing. build: execute that plan as ONE resumable operation, each
            stage run THROUGH THE SEAM and recorded as an idempotent operation step. resume:
            continue an interrupted build (done steps are skipped). status: show a build.
DEPENDS ON: tools._toolkit, tools.scaffold_shared (map validation), tools.llm_shared (propose);
            calls genesis/scaffold_project/provenance/journal/operation THROUGH the seam.
NOTES:      Orchestration only - the planner OWNS none of the logic it sequences; it calls each
            tool through the governed seam (like delegate), so it cannot become a monolith. It is
            the first real CONSUMER of the E4 operation ledger (resumable, idempotent) and the E5
            provenance graph (the built structure traces back to the intent). The agent proposes
            the map; the planner never DECIDES what the project should be - judgment stays outside.
"""
from __future__ import annotations

from tools import scaffold_shared as sc
from tools._toolkit import apply_with, confirmed, first_json_object, seam_call, tool_main

_TIMEOUT = 180
_SUMMARY_MODEL = "qwen2.5:3b"


def _seam(tool: str, args: dict) -> dict:
    return seam_call(tool, args, timeout=_TIMEOUT)


# ---------------------------------------------------------------- propose (optional Brain step)
_PROPOSE_PROMPT = (
    "You are laying out a NEW project from a one-sentence intent. Output ONLY a JSON object with "
    "a 'tree' array of nodes; each node is either {\"dir\":\"relpath\"} or "
    "{\"file\":\"relpath\",\"role\":\"...\",\"does\":\"...\"}. Keep it small and sensible. "
    "No prose, no code fences.\n\nINTENT: ")


def _propose(intent: str, name: str, archetype: str | None) -> dict:
    """Draft a project map. Prefer the local model; fall back to an archetype (honest degrade)."""
    from tools import llm_shared

    if archetype and archetype in sc.ARCHETYPES:
        return {"map": {"name": name, "plan": intent, "archetype": archetype}, "degraded": False,
                "source": f"archetype:{archetype}"}
    out = llm_shared.chat(_SUMMARY_MODEL, _PROPOSE_PROMPT + intent, purpose="plan.propose",
                          num_predict=400, temperature=0.2)
    if out["ok"]:
        obj = first_json_object(out["content"])
        if isinstance(obj, dict) and isinstance(obj.get("tree"), list):
            candidate = {"name": name, "plan": intent, "tree": obj["tree"]}
            norm, err = sc.validate_map(candidate)
            if not err:
                return {"map": candidate, "degraded": False, "source": "local-model"}
    # degrade: a sensible default archetype the human/agent can edit
    fallback = archetype if archetype in sc.ARCHETYPES else "python-cli"
    return {"map": {"name": name, "plan": intent, "archetype": fallback}, "degraded": True,
            "source": f"archetype:{fallback} (no usable model proposal)",
            "note": "no local model proposal was usable; returning an editable archetype map"}





# ---------------------------------------------------------------- operation-ledger helpers
def _done_keys(op_id: str) -> set:
    r = _seam("operation", {"action": "show", "op_id": op_id})
    steps = (r.get("output") or {}).get("operation", {}).get("steps", []) if r["ok"] else []
    return {s.get("idempotency_key") for s in steps
            if s.get("status") == "done" and s.get("idempotency_key")}


def _record(op_id: str, key: str, tool: str, result_ref: str = "") -> None:
    _seam("operation", {"action": "step", "op_id": op_id, "tool": tool, "status": "done",
                        "idempotency_key": key, "result_ref": result_ref})


def _fail(op_id: str, tool: str, failure_class: str, note: str) -> None:
    _seam("operation", {"action": "step", "op_id": op_id, "tool": tool, "status": "failed",
                        "failure_class": failure_class, "note": note[:300]})


# ---------------------------------------------------------------- the build orchestration
def _build(intent: str, name: str, project_map: dict, root: str, op_id: str,
           overwrite: bool) -> dict:
    done = _done_keys(op_id)
    trail: list[dict] = []

    # 1. genesis (required) - "already initialized" counts as satisfied (idempotent).
    if "genesis" not in done:
        g = _seam("genesis", {"intent": intent, "name": name, "apply": True})
        out = g.get("output") or {}
        if g["ok"] or out.get("already_initialized"):
            _record(op_id, "genesis", "genesis",
                    result_ref=(out.get("workspace") or {}).get("workspace_id", ""))
            trail.append({"step": "genesis", "ok": True,
                          "already": bool(out.get("already_initialized"))})
        else:
            _fail(op_id, "genesis", "capability_unavailable", str(g.get("error") or out.get("error")))
            return {"ok": False, "op_id": op_id, "error": f"genesis failed: {g.get('error')}",
                    "trail": trail}
    else:
        trail.append({"step": "genesis", "ok": True, "skipped": True})

    # 2. scaffold (required) - materialize the tree.
    if "scaffold" not in done:
        s = _seam("scaffold_project", {"action": "create", "map": project_map, "root": root,
                                       "apply": True, "overwrite": overwrite})
        out = s.get("output") or {}
        if s["ok"] and out.get("created"):
            _record(op_id, "scaffold", "scaffold_project", result_ref=out.get("base", ""))
            trail.append({"step": "scaffold", "ok": True, "base": out.get("base"),
                          "files": out.get("summary", {}).get("written")})
        else:
            _fail(op_id, "scaffold_project", "no_effect", str(s.get("error") or out.get("error")))
            return {"ok": False, "op_id": op_id, "error": f"scaffold failed: {out.get('error') or s.get('error')}",
                    "trail": trail}
    else:
        trail.append({"step": "scaffold", "ok": True, "skipped": True})

    # 3. provenance (best-effort) - the built structure traces back to the intent.
    if "provenance" not in done:
        _seam("provenance", {"action": "note",
                             "subject": {"kind": "intent", "ref": intent, "label": name},
                             "relation": "motivated",
                             "object": {"kind": "project", "ref": name},
                             "origin": "operational", "op_id": op_id})
        _seam("provenance", {"action": "activity", "verb": "scaffold project", "origin": "operational",
                             "op_id": op_id, "participants": [
                                 {"role": "requested_by", "kind": "intent", "ref": intent},
                                 {"role": "executed_by", "kind": "capability", "ref": "scaffold_project"},
                                 {"role": "generated", "kind": "project", "ref": name}]})
        _record(op_id, "provenance", "provenance")
        trail.append({"step": "provenance", "ok": True})
    else:
        trail.append({"step": "provenance", "ok": True, "skipped": True})

    # 4. journal (best-effort) - narrate the milestone.
    if "journal" not in done:
        _seam("journal", {"action": "add", "title": f"Planned build: {name}", "phase": "genesis",
                          "summary": f"Built the initial structure for '{name}' from intent: {intent}",
                          "decisions": ["Structure materialized via the planner (genesis -> scaffold)."]})
        _record(op_id, "journal", "journal")
        trail.append({"step": "journal", "ok": True})
    else:
        trail.append({"step": "journal", "ok": True, "skipped": True})

    _seam("operation", {"action": "finish", "op_id": op_id})
    return {"ok": True, "op_id": op_id, "created": True, "name": name, "trail": trail,
            "trace_hint": {"tool": "provenance", "args": {"action": "trace", "kind": "project",
                                                          "ref": name}}}


@tool_main
def run(args: dict) -> dict:
    action = str(args.get("action") or "preview").lower()
    intent = str(args.get("intent") or "").strip()
    name = str(args.get("name") or "").strip() or "untitled-project"

    if action == "propose":
        if not intent:
            return {"ok": False, "error": "intent is required to propose a map"}
        return {"tool": "plan", "action": "propose",
                **_propose(intent, name, args.get("archetype"))}

    if action == "status":
        op_id = str(args.get("op_id") or "")
        if not op_id:
            return {"ok": False, "error": "op_id is required for status"}
        r = _seam("operation", {"action": "show", "op_id": op_id})
        if not r["ok"]:
            return {"ok": False, "error": r.get("error") or "no such operation"}
        return {"tool": "plan", "action": "status", "operation": (r["output"] or {}).get("operation")}

    if action == "resume":
        op_id = str(args.get("op_id") or "")
        if not op_id:
            return {"ok": False, "error": "op_id is required to resume"}
        st = _seam("operation", {"action": "show", "op_id": op_id})
        op = (st.get("output") or {}).get("operation") if st["ok"] else None
        if not op:
            return {"ok": False, "error": f"no such operation {op_id}"}
        # recover the plan inputs from the operation, or require them again
        r_intent = intent or op.get("goal") or ""
        r_name = name if args.get("name") else (op.get("title") or "").removeprefix("Plan: ") or name
        pmap = args.get("map")
        if not isinstance(pmap, dict):
            return {"ok": False, "error": "resume needs the same map (pass `map`) to continue the build"}
        if not confirmed(args):
            return {"tool": "plan", "action": "resume", "op_id": op_id, "dry_run": True,
                    "resumable": True, "apply_with": apply_with()}
        return {"tool": "plan", "action": "resume",
                **_build(r_intent, r_name, pmap, str(args.get("root") or ""), op_id,
                         bool(args.get("overwrite")))}

    # action in {preview, build} -----------------------------------------------------------
    if not intent:
        return {"ok": False, "error": "intent is required"}
    project_map = args.get("map")
    if not isinstance(project_map, dict):
        return {"ok": False, "error": "map is required (a project-map object); "
                "use action=propose to draft one, or scaffold_project show_archetype"}
    norm, err = sc.validate_map(project_map)
    if err:
        return {"ok": False, "error": f"invalid project map: {err}"}

    preview = {
        "tool": "plan", "name": name, "intent": intent,
        "will": [
            "genesis: record workspace identity + intent, seed the journal",
            f"scaffold_project: create {len(norm['files'])} file(s), {len(norm['dirs'])} dir(s) + PROJECT_PLAN.md",
            "provenance: record that this intent motivated the project (traceable)",
            "journal: note the milestone",
            "operation: the whole build is one resumable, idempotent operation",
        ],
        "planned_files": [f["rel"] for f in norm["files"]],
        "planned_dirs": norm["dirs"],
    }
    if not confirmed(args):
        return {**preview, "action": "preview", "dry_run": True, "created": False,
                "apply_with": apply_with()}

    # build for real: open the operation, then orchestrate.
    op = _seam("operation", {"action": "start", "title": f"Plan: {name}", "goal": intent})
    if not op["ok"]:
        return {"ok": False, "error": f"could not open operation: {op.get('error')}"}
    op_id = (op["output"] or {}).get("op_id")
    return {**preview, "action": "build",
            **_build(intent, name, project_map, str(args.get("root") or ""), op_id,
                     bool(args.get("overwrite")))}
