"""
FILE:       tools/diff/cli.py
ROLE:       Unified text/file diff through the seam (review a change; ground it as evidence).
DOMAIN:     tool
DOES:       Produce a unified diff between two inputs  -  each a file path (confined to the roots) or
            inline text. Reports the diff plus added/removed line counts. Pure Observe.
DEPENDS ON: tools._toolkit, (stdlib) difflib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Pass a/b as paths, or a_text/b_text as inline strings (mix freely). Capped output.
"""
from __future__ import annotations

import difflib

from tools._toolkit import resolve_within_roots, tool_main

_CAP = 200_000


def _load(args: dict, key: str) -> tuple[str | None, str, str]:
    """Return (text, label, error). Prefers <key>_text; else <key> as a path within the roots."""
    tkey = f"{key}_text"
    if args.get(tkey) is not None:
        return str(args[tkey]), f"<{key}_text>", ""
    if args.get(key):
        path, err = resolve_within_roots(args[key])
        if err:
            return None, "", err
        if not path.is_file():
            return None, "", f"not a file: {path}"
        return path.read_text(encoding="utf-8", errors="replace"), path.as_posix(), ""
    return None, "", f"provide '{key}' (a path) or '{tkey}' (inline text)"


@tool_main
def run(args: dict) -> dict:
    a_text, a_label, err = _load(args, "a")
    if err:
        return {"ok": False, "error": err}
    b_text, b_label, err = _load(args, "b")
    if err:
        return {"ok": False, "error": err}

    a_lines = a_text.splitlines(keepends=True)
    b_lines = b_text.splitlines(keepends=True)
    diff_lines = list(difflib.unified_diff(
        a_lines, b_lines, fromfile=str(args.get("from_label") or a_label),
        tofile=str(args.get("to_label") or b_label), n=int(args.get("context", 3))))
    added = sum(1 for ln in diff_lines if ln.startswith("+") and not ln.startswith("+++"))
    removed = sum(1 for ln in diff_lines if ln.startswith("-") and not ln.startswith("---"))
    text = "".join(diff_lines)
    return {
        "tool": "diff",
        "identical": a_text == b_text,
        "added": added,
        "removed": removed,
        "diff": text[:_CAP],
        "truncated": len(text) > _CAP,
    }
