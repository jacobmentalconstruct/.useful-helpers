"""
FILE:       tools/artifact_cleaner/cli.py
ROLE:       Dry-run-first runtime artifact cleaner.
DOMAIN:     tool
DOES:       Finds allowlisted generated artifacts and optionally removes them only when
            dry_run:false and confirm:true. Protects tracked files by default.
DEPENDS ON: tools._toolkit, (stdlib) pathlib, shutil, subprocess
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Apply authority: preview-first, and refuses to delete outside the
            toolkit's own artifact root.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from tools._toolkit import suite_home, tool_main

_DEFAULT_PATTERNS = [
    "__pycache__",
    "*/__pycache__",
    "*/*/__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "*.log",
    "_artifacts/test_tmp/*",
    "_tmp_sqlite_probe/*",
]


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _tracked(root: Path, path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(root.resolve())
        completed = subprocess.run(["git", "ls-files", "--error-unmatch", "--", rel.as_posix()],
                                   cwd=str(root), capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=5, check=False)
        return completed.returncode == 0
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return False


def _measure(path: Path) -> tuple[int, int]:
    if path.is_file():
        try:
            return path.stat().st_size, 1
        except OSError:
            return 0, 1
    total = 0
    files = 0
    for child in path.rglob("*"):
        if child.is_file():
            files += 1
            try:
                total += child.stat().st_size
            except OSError:
                pass
    return total, files


def _candidates(root: Path, patterns: list[str], limit: int) -> list[Path]:
    rows = []
    seen = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if not path.exists() or not _inside(root, path):
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            rows.append(path)
            if len(rows) >= limit:
                return rows
    return rows


def _remove(path: Path) -> tuple[bool, str]:
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        return True, ""
    except OSError as e:
        return False, str(e)


@tool_main
def run(args: dict) -> dict:
    # Generated artifacts default under the toolkit home, so clean there by default; an explicit
    # root (e.g. ".") can target the work-target project instead.
    root = Path(args.get("root") or args.get("project_root") or suite_home()).resolve()
    project = Path.cwd().resolve()
    if not root.is_dir():
        return {"ok": False, "error": f"root is not a directory: {root}"}
    if not _inside(project, root):
        return {"ok": False, "error": "root must stay inside the project workspace"}

    dry_run = bool(args.get("dry_run", True))
    confirm = bool(args.get("confirm", False))
    allow_tracked = bool(args.get("allow_tracked", False))
    patterns = [str(x) for x in args.get("include_patterns", _DEFAULT_PATTERNS)]
    max_candidates = max(1, min(int(args.get("max_candidates", 500)), 5000))
    if not dry_run and not confirm:
        return {"ok": False, "error": "cleanup requires confirm:true when dry_run is false"}

    rows = []
    removed = []
    failed = []
    blocked = []
    total_bytes = 0
    for path in _candidates(root, patterns, max_candidates):
        tracked = _tracked(root, path)
        size_bytes, file_count = _measure(path)
        item = {"path": _rel(root, path), "kind": "directory" if path.is_dir() else "file",
                "size_bytes": size_bytes, "file_count": file_count, "tracked": tracked,
                "allowed": not tracked or allow_tracked}
        total_bytes += size_bytes
        if tracked and not allow_tracked:
            item["reason"] = "tracked_file_protected"
            blocked.append(item)
            rows.append(item)
            continue
        if not dry_run:
            ok, error = _remove(path)
            item["removed"] = ok
            if error:
                item["error"] = error
                failed.append(item)
            else:
                removed.append(item)
        rows.append(item)

    summary = {
        "candidate_count": len(rows),
        "blocked_count": len(blocked),
        "removed_count": len(removed),
        "failed_count": len(failed),
        "total_candidate_bytes": total_bytes,
        "tracked_files_protected": not allow_tracked,
        "truncated": len(rows) >= max_candidates,
    }
    return {
        "ok": len(failed) == 0,
        "tool": "artifact_cleaner",
        "root": root.as_posix(),
        "dry_run": dry_run,
        "confirm": confirm,
        "allow_tracked": allow_tracked,
        "patterns": patterns,
        "candidate_count": len(rows),
        "blocked_count": len(blocked),
        "removed_count": len(removed),
        "failed_count": len(failed),
        "total_candidate_bytes": total_bytes,
        "candidates": rows,
        "blocked": blocked,
        "removed": removed,
        "failed": failed,
        "summary": summary,
        "warnings": ["Review dry-run output before cleanup; only allowlisted candidates are considered."],
    }
