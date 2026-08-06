"""
FILE:       tools/scaffold_project/cli.py
ROLE:       Materialize a NEW project from a contract map - dirs, files, boilerplate, plan doc.
DOMAIN:     tool
DOES:       action=archetypes: list the built-in starting maps.
            action=show_archetype: return one archetype's full map (the agent tailors it).
            action=plan (default): validate a map + preview EVERY dir/file it would create, with
            collisions flagged - one plan for one approval. Writes nothing.
            action=create (apply:true): materialize the tree. Refuses to overwrite unless
            overwrite:true; refuses any path that escapes the resolved base.
DEPENDS ON: tools._toolkit, tools.scaffold_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json. A future `planner` tool
            generates the map and sequences this with sidecar_install / journal.
NOTES:      Deliberately dumb: it plans nothing, it honors the contract the agent fed it, and it
            writes ONLY the project tree (no sidecar traces, nothing outside the base). Preview is
            free and always available; a single apply:true executes the WHOLE batch - the
            batch-consent convention. A scaffolded project is born precept-clean.
"""
from __future__ import annotations

from pathlib import Path

from tools import scaffold_shared as sc
from tools._toolkit import apply_with, confirmed, output_root, resolve_within_roots, tool_main


def _base_for(args: dict) -> "tuple[Path | None, str]":
    """Where the project is created: `root` (relative, confined to the roots), or a default under
    the output root. Confined by resolve_within_roots so a scaffold can never escape the sidecar's
    governed area."""
    raw = str(args.get("root") or "").strip()
    if not raw:
        name = str((args.get("map") or {}).get("name") or "new-project")
        slug = "".join(c if (c.isalnum() or c in "-_") else "-" for c in name.lower()).strip("-")
        return (output_root() / "scaffold" / (slug or "new-project")), ""
    return resolve_within_roots(raw)


@tool_main
def run(args: dict) -> dict:
    action = str(args.get("action") or "plan").lower()

    if action == "archetypes":
        return {"tool": "scaffold_project", "action": "archetypes",
                "archetypes": [{"id": k, "label": v.get("label"),
                                "description": v.get("description"),
                                "nodes": len(v.get("tree", []))}
                               for k, v in sorted(sc.ARCHETYPES.items())],
                "templates": sorted(sc.BOILERPLATE)}

    if action == "show_archetype":
        key = str(args.get("archetype") or "")
        arch = sc.ARCHETYPES.get(key)
        if arch is None:
            return {"ok": False, "error": f"unknown archetype {key!r}",
                    "known": sorted(sc.ARCHETYPES)}
        return {"tool": "scaffold_project", "action": "show_archetype", "archetype": key,
                "map": {"name": key, "plan": arch.get("description", ""),
                        "tree": arch.get("tree", [])}}

    if action not in {"plan", "create"}:
        return {"ok": False, "error": f"unknown action {action!r}; "
                "use archetypes|show_archetype|plan|create"}

    project_map = args.get("map")
    if not isinstance(project_map, dict):
        return {"ok": False, "error": "map is required (a project-map object); "
                "see action=show_archetype for a starting point"}

    norm, err = sc.validate_map(project_map)
    if err:
        return {"ok": False, "error": f"invalid project map: {err}"}

    base, berr = _base_for(args)
    if berr:
        return {"ok": False, "error": f"destination: {berr}"}
    planned, perr = sc.plan_tree(norm, base)
    if perr:
        return {"ok": False, "error": perr}

    dirs = [p for p in planned if p["kind"] == "dir"]
    files = [p for p in planned if p["kind"] == "file"]
    collisions = [p["rel"] for p in planned if p["collision"]]
    # a directory path already occupied by a file is fatal regardless of overwrite
    dir_blocked = [p["rel"] for p in dirs if p["collision"]]

    preview = {
        "tool": "scaffold_project", "name": norm["name"],
        "base": base.as_posix(),
        "planned_dirs": [p["rel"] for p in dirs],
        "planned_files": [{"rel": p["rel"], "bytes": p["bytes"], "collision": p["collision"]}
                          for p in files],
        "collisions": collisions,
        "summary": {"dirs": len(dirs), "files": len(files),
                    "total_bytes": sum(p.get("bytes", 0) for p in files),
                    "collisions": len(collisions)},
    }

    if not confirmed(args):
        return {**preview, "action": "plan", "dry_run": True, "created": False,
                "apply_with": apply_with()}

    # ---- create ------------------------------------------------------------------------
    if dir_blocked:
        return {**preview, "ok": False, "action": "create", "created": False,
                "error": f"a file already occupies a planned directory path: {dir_blocked}"}
    if collisions and not args.get("overwrite"):
        return {**preview, "ok": False, "action": "create", "created": False,
                "error": "destination has collisions; pass overwrite:true to replace them",
                "collisions": collisions}

    written: list[str] = []
    for p in dirs:
        Path(p["abs"]).mkdir(parents=True, exist_ok=True)
    for p in files:
        dest = Path(p["abs"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(p["content"], encoding="utf-8")
        written.append(p["rel"])

    return {**preview, "action": "create", "created": True, "written": written,
            "summary": {**preview["summary"], "written": len(written)}}
