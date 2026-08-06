"""
FILE:       tools/linenumber/cli.py
ROLE:       Make text agent-friendly with stable, parseable line numbers (+ integrity map).
DOMAIN:     tool
DOES:       action=annotate: prefix each line with a numbered style (pipe/colon/bracket).
            action=strip: remove our own numbering safely. action=map: line -> SHA-256 map.
            Operates on `text` or a `path`; returns data (Observe)  -  no file writes.
DEPENDS ON: tools._toolkit, (stdlib) hashlib, re, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from tools._toolkit import tool_main

_STYLES = {
    "pipe": lambda n, w: f"{n:>{w}}│ ",
    "colon": lambda n, w: f"{n:>{w}}: ",
    "bracket": lambda n, w: f"[L{n:0{w}d}] ",
}
_PREFIX_RES = (
    re.compile(r"^(?P<p>\s*\d+│\s)"),
    re.compile(r"^(?P<p>\s*\d+:\s)"),
    re.compile(r"^(?P<p>\s*\[L\d+\]\s)"),
)


def _get_text(args: dict) -> tuple[str | None, str | None]:
    if args.get("text") is not None:
        return str(args["text"]), None
    path = args.get("path")
    if not path:
        return None, "provide 'text' or 'path'"
    p = Path(path)
    if not p.is_file():
        return None, f"not a file: {path}"
    return p.read_text(encoding="utf-8"), None


@tool_main
def run(args: dict) -> dict:
    action = str(args.get("action", "annotate")).lower()
    text, err = _get_text(args)
    if err:
        return {"ok": False, "error": err}
    lines = text.splitlines(keepends=True)

    if action == "annotate":
        style = str(args.get("style", "pipe"))
        if style not in _STYLES:
            return {"ok": False, "error": f"unknown style {style!r}; use {list(_STYLES)}"}
        start = int(args.get("start", 1))
        total = len(lines)
        width = max(int(args.get("width", 0)), len(str(start + total - 1)), 3)
        fmt = _STYLES[style]
        out = [f"{fmt(start + i, width)}{ln}" for i, ln in enumerate(lines)]
        return {"tool": "linenumber", "action": "annotate", "style": style,
                "total_lines": total, "numbered": "".join(out)}

    if action == "strip":
        out = []
        for ln in lines:
            m = next((r.match(ln) for r in _PREFIX_RES if r.match(ln)), None)
            out.append(ln[m.end("p"):] if m else ln)
        return {"tool": "linenumber", "action": "strip",
                "total_lines": len(lines), "stripped": "".join(out)}

    if action == "map":
        entries = [{"n": i, "hash": hashlib.sha256(ln.encode("utf-8")).hexdigest()}
                   for i, ln in enumerate(lines, 1)]
        return {"tool": "linenumber", "action": "map",
                "total_lines": len(entries), "lines": entries}

    return {"ok": False, "error": f"unknown action {action!r}; use annotate|strip|map"}
