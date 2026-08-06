"""
FILE:       tools/repo_search/cli.py
ROLE:       Structured repository text search.
DOMAIN:     tool
DOES:       Search text files under a root using rg when available, with a Python fallback.
            Returns JSON rows with path, line number, and a trimmed line preview.
DEPENDS ON: tools._toolkit, (stdlib) pathlib, subprocess, shutil
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Kept toolkit-local: prefers ripgrep when present, falls back to a Python
            scan so it works on a bare host.
"""
from __future__ import annotations

import fnmatch
import re
import shutil
import subprocess
from pathlib import Path

from tools._toolkit import tool_main, toolkit_home_names

_PRUNE = {".git", ".venv", "node_modules", "__pycache__", "dist", "build"}


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _textish(path: Path) -> bool:
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".sqlite3", ".db", ".pyc"}:
        return False
    try:
        chunk = path.read_bytes()[:2048]
    except OSError:
        return False
    return b"\x00" not in chunk


def _fallback(
    root: Path, query: str, glob: str, limit: int, case_sensitive: bool, prune: set[str]
) -> list[dict]:
    needle = query if case_sensitive else query.lower()
    rows: list[dict] = []
    for path in root.rglob("*"):
        if len(rows) >= limit:
            break
        if any(part in prune for part in path.relative_to(root).parts):
            continue
        if not path.is_file() or not fnmatch.fnmatch(path.name, glob) or not _textish(path):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            hay = line if case_sensitive else line.lower()
            if needle in hay:
                rows.append({"path": path.relative_to(root).as_posix(), "line": lineno,
                             "text": line.strip()[:300]})
                if len(rows) >= limit:
                    break
    return rows


@tool_main
def run(args: dict) -> dict:
    root = Path(args.get("root") or ".").resolve()
    project = Path.cwd().resolve()
    if not root.exists() or not root.is_dir():
        return {"ok": False, "error": f"root is not a directory: {root}"}
    if not _inside(project, root):
        return {"ok": False, "error": "root must stay inside the project workspace"}

    query = str(args.get("query") or args.get("pattern") or "")
    if not query:
        return {"ok": False, "error": "'query' is required"}
    glob = str(args.get("glob") or "*")
    limit = max(1, min(int(args.get("limit", 50)), 500))
    case_sensitive = bool(args.get("case_sensitive", False))
    prune = _PRUNE | toolkit_home_names()

    rg = shutil.which("rg")
    if rg:
        cmd = [rg, "--line-number", "--no-heading", "--color", "never", "--glob", f"!{{{','.join(sorted(prune))}}}/**"]
        if not case_sensitive:
            cmd.append("--ignore-case")
        if glob != "*":
            cmd.extend(["--glob", glob])
        cmd.extend(["--", query, str(root)])
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        rows: list[dict] = []
        for line in proc.stdout.splitlines():
            if len(rows) >= limit:
                break
            match = re.match(r"^(.*):(\d+):(.*)$", line)
            if not match:
                continue
            p, lineno, text = match.groups()
            try:
                rel = Path(p).resolve().relative_to(root).as_posix()
            except ValueError:
                rel = p
            rows.append({"path": rel, "line": int(lineno), "text": text.strip()[:300]})
        return {"tool": "repo_search", "root": root.as_posix(), "query": query, "engine": "rg",
                "count": len(rows), "truncated": len(rows) >= limit, "matches": rows}

    rows = _fallback(root, query, glob, limit, case_sensitive, prune)
    return {"tool": "repo_search", "root": root.as_posix(), "query": query, "engine": "python",
            "count": len(rows), "truncated": len(rows) >= limit, "matches": rows}
