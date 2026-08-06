"""
FILE:       tools/glob/cli.py
ROLE:       Match files by glob pattern through the governed seam (the sidecar's `Glob`).
DOMAIN:     tool
DOES:       Return paths under a root matching a glob pattern (supports ** recursion), pruning
            noise + the toolkit's own home by default so the sidecar never drowns the project view.
DEPENDS ON: tools._toolkit, (stdlib) pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      file_tree filters by kind/ext; this matches by PATTERN (`**/*.py`, `src/**/*.ts`).
            Pass include_all:true to keep noise/toolkit-home results.
"""
from __future__ import annotations

from tools._toolkit import resolve_within_roots, tool_main, toolkit_home_names

_PRUNE = {".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules", "__pycache__",
          ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build", "_artifacts"}


@tool_main
def run(args: dict) -> dict:
    pattern = str(args.get("pattern") or "").strip()
    if not pattern:
        return {"ok": False, "error": "pattern is required"}
    root, err = resolve_within_roots(args.get("root", "."))
    if err:
        return {"ok": False, "error": err}
    if not root.is_dir():
        return {"ok": False, "error": f"root is not a directory: {root}"}

    limit = max(1, min(int(args.get("limit", 1000)), 20000))
    include_all = bool(args.get("include_all", False))
    skip = set() if include_all else (_PRUNE | toolkit_home_names())

    resolved_root = root.resolve()
    matches: list[str] = []
    truncated = False
    for p in root.glob(pattern):
        # A pattern like `../*.py` can walk out of the root  -  confine results to it, or glob
        # would quietly expose paths the rest of the hands refuse to touch.
        try:
            rel = p.resolve().relative_to(resolved_root)
        except ValueError:
            continue
        if not rel.parts:
            continue  # the root itself (an escaping pattern can circle back to it)  -  not a match
        if not include_all and (set(rel.parts) & skip):
            continue
        matches.append(rel.as_posix() + ("/" if p.is_dir() else ""))
        if len(matches) >= limit:
            truncated = True
            break

    return {
        "tool": "glob",
        "root": root.as_posix(),
        "pattern": pattern,
        "count": len(matches),
        "matches": sorted(matches),
        "truncated": truncated,
    }
