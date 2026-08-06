"""
FILE:       tools/edit/cli.py
ROLE:       Headless find/replace on text or a file  -  regex or literal, with a count guard.
DOMAIN:     tool
DOES:       Replace `pattern` with `replacement` over `text` or a `path`. `literal:true` matches an
            exact string (no regex). `expected_replacements` REFUSES the write unless the count
            matches  -  so a greedy/ambiguous match can't silently change more than intended.
            Preview by default; writes back only with write:true (or apply:true) AND a `path`.
DEPENDS ON: tools._toolkit, (stdlib) re
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
NOTES:      Path is confined to the roots. `expected_replacements` is the safety belt for exact
            edits; without it, behavior is the old regex subn (backward compatible).
"""
from __future__ import annotations

import re

from tools._toolkit import confirmed, resolve_within_roots, tool_main

_FLAGS = {"ignorecase": re.IGNORECASE, "multiline": re.MULTILINE, "dotall": re.DOTALL}


@tool_main
def run(args: dict) -> dict:
    pattern = args.get("pattern")
    replacement = args.get("replacement")
    if pattern is None or replacement is None:
        return {"ok": False, "error": "'pattern' and 'replacement' are required"}
    pattern, replacement = str(pattern), str(replacement)

    if args.get("text") is not None:
        content, source, path = str(args["text"]), "text", None
    elif args.get("path"):
        path, err = resolve_within_roots(args["path"])
        if err:
            return {"ok": False, "error": err}
        if not path.is_file():
            return {"ok": False, "error": f"not a file: {path}"}
        content, source = path.read_text(encoding="utf-8"), "path"
    else:
        return {"ok": False, "error": "provide 'text' or 'path'"}

    literal = bool(args.get("literal"))
    count = int(args.get("count", 0))
    if literal:
        # exact-string replacement; count=0 means all
        n = content.count(pattern) if count == 0 else min(content.count(pattern), count)
        new_content = content.replace(pattern, replacement, -1 if count == 0 else count)
    else:
        flags = 0
        for name, val in _FLAGS.items():
            if args.get(name):
                flags |= val
        try:
            new_content, n = re.subn(pattern, replacement, content, count=count, flags=flags)
        except re.error as e:
            return {"ok": False, "error": f"bad regex: {e}"}

    # The safety belt: refuse to touch anything if the match count isn't what the caller expected.
    expected = args.get("expected_replacements")
    if expected is not None and n != int(expected):
        return {"ok": False, "tool": "edit", "replacements": n, "written": False,
                "error": f"expected {int(expected)} replacement(s), found {n}: refusing",
                "literal": literal}

    changed = new_content != content
    result = {"tool": "edit", "replacements": n, "changed": changed, "source": source,
              "literal": literal}
    if confirmed(args, legacy=("write",)) and source == "path" and changed:
        path.write_text(new_content, encoding="utf-8")
        result["written"] = True
        result["path"] = path.as_posix()
    else:
        result["written"] = False
        result["result"] = new_content  # preview
        if source == "path":
            result["apply_with"] = {"apply": True}
    return result
