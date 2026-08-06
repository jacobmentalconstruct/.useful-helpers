"""
FILE:       tools/fs_op/cli.py
ROLE:       Governed filesystem mutation (the sidecar's mkdir/cp/mv/rm/touch).
DOMAIN:     tool
DOES:       Apply a BATCH of filesystem ops (mkdir | touch | copy | move | delete) in one call.
            Preview-first: the dry-run lists every op it would perform; one apply executes the
            whole batch. All paths confined to the work target / toolkit home.
DEPENDS ON: tools._toolkit, (stdlib) shutil, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
NOTES:      Batch-consent convention: many items -> one plan -> one yes (never a prompt per op).
            delete is recursive for directories; the batch approval is the gate. Escapes are
            refused by resolve_within_roots, so fs_op cannot reach arbitrary host paths.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from tools._toolkit import confirmed, project_root, resolve_within_roots, suite_home, tool_main

_OPS = {"mkdir", "touch", "copy", "move", "delete"}
_NEEDS_DEST = {"copy", "move"}
_DESTRUCTIVE = {"delete", "move"}  # ops that REMOVE the source


def _is_root(p) -> bool:
    """A work-target or toolkit-home root itself  -  never removable via fs_op."""
    rp = p.resolve()
    return rp == project_root().resolve() or rp == suite_home().resolve()


def _plan_op(op: dict) -> dict:
    kind = str(op.get("op") or "").strip().lower()
    if kind not in _OPS:
        return {"op": kind, "ok": False, "error": f"unknown op {kind!r}; use {sorted(_OPS)}"}
    src, err = resolve_within_roots(op.get("path", ""))
    if err:
        return {"op": kind, "ok": False, "error": err}
    if kind in _DESTRUCTIVE and _is_root(src):
        return {"op": kind, "path": src.as_posix(), "ok": False,
                "error": "refusing to delete/move a root (the work target or toolkit home)"}
    entry = {"op": kind, "path": src.as_posix(), "exists": src.exists()}
    if kind in _NEEDS_DEST:
        dest, err = resolve_within_roots(op.get("dest", ""))
        if err:
            return {**entry, "ok": False, "error": f"dest: {err}"}
        entry["dest"] = dest.as_posix()
    if kind == "delete" and not src.exists():
        return {**entry, "ok": False, "error": "nothing to delete (path does not exist)"}
    entry["ok"] = True
    return entry


def _apply_op(entry: dict) -> dict:
    kind = entry["op"]
    src = Path(entry["path"])
    try:
        if kind == "mkdir":
            src.mkdir(parents=True, exist_ok=True)
        elif kind == "touch":
            src.parent.mkdir(parents=True, exist_ok=True)
            src.touch(exist_ok=True)
        elif kind == "delete":
            if src.is_dir():
                shutil.rmtree(src)
            else:
                src.unlink(missing_ok=True)
        elif kind in _NEEDS_DEST:
            dest = Path(entry["dest"])
            dest.parent.mkdir(parents=True, exist_ok=True)
            if kind == "copy":
                shutil.copytree(src, dest) if src.is_dir() else shutil.copy2(src, dest)
            else:  # move
                shutil.move(str(src), str(dest))
        return {**entry, "done": True}
    except OSError as e:
        return {**entry, "done": False, "error": f"{type(e).__name__}: {e}"}


@tool_main
def run(args: dict) -> dict:
    ops = args.get("ops")
    if not isinstance(ops, list):
        # single-op convenience form
        if args.get("op"):
            ops = [{k: args[k] for k in ("op", "path", "dest") if k in args}]
        else:
            return {"ok": False, "error": "provide 'ops' (a list) or a single 'op' + 'path'"}
    if not ops:
        return {"ok": False, "error": "no ops given"}

    plan = [_plan_op(o) for o in ops]
    invalid = [p for p in plan if not p.get("ok")]
    if invalid:
        return {"ok": False, "tool": "fs_op", "error": "one or more ops are invalid; nothing done",
                "invalid": invalid, "plan": plan}

    if not confirmed(args):
        return {"tool": "fs_op", "dry_run": True, "count": len(plan), "plan": plan,
                "apply_with": {"apply": True}}

    results = [_apply_op(p) for p in plan]
    failed = [r for r in results if not r.get("done")]
    return {"tool": "fs_op", "dry_run": False, "applied": len(results) - len(failed),
            "failed": len(failed), "results": results, "ok": not failed}
