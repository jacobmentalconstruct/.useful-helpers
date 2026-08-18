"""
FILE:       tools/report/cli.py
ROLE:       Structural logical-analysis report for Python code (a file or a project tree).
DOMAIN:     tool
DOES:       Parses Python via AST and reports per-module purpose (docstring), classes + methods,
            functions, and imports  -  as structured data + a Markdown rendering. Pure Observe.
DEPENDS ON: tools._toolkit, (stdlib) ast, os, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      No-AI variant: pure structural extraction, no model calls.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

from tools._toolkit import is_instance_path, tool_main

_IGNORES = {".git", ".venv", "venv", "__pycache__", "node_modules", "build", "dist"}


def _first(text: str) -> str:
    lines = (text or "").splitlines()
    return lines[0] if lines else ""


def _analyze(path: Path, rel: str) -> dict:
    try:
        node = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as e:
        return {"file": rel, "error": f"syntax error line {e.lineno}: {e.msg}"}
    except Exception as e:  # unreadable / decode
        return {"file": rel, "error": str(e)}

    imports: list[str] = []
    classes: list[dict] = []
    functions: list[dict] = []
    for item in node.body:
        if isinstance(item, ast.Import):
            imports += [a.name for a in item.names]
        elif isinstance(item, ast.ImportFrom):
            imports.append(f"{item.module or ''} (from)")
        elif isinstance(item, ast.ClassDef):
            methods = [s.name for s in item.body if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes.append({"name": item.name, "doc": _first(ast.get_docstring(item) or ""), "methods": methods})
        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({"name": item.name, "doc": _first(ast.get_docstring(item) or "")})

    return {"file": rel, "purpose": _first(ast.get_docstring(node) or ""),
            "imports": imports, "classes": classes, "functions": functions}


def _md(mod: dict) -> str:
    if "error" in mod:
        return f"## `{mod['file']}`\n\n_Error: {mod['error']}_\n"
    out = [f"## `{mod['file']}`", "", f"**Purpose:** {mod['purpose'] or '(none)'}", ""]
    if mod["classes"]:
        out.append("**Classes:**")
        for c in mod["classes"]:
            out.append(f"- `class {c['name']}`: {c['doc']}")
            out += [f"  - `def {m}()`" for m in c["methods"]]
    if mod["functions"]:
        out.append("**Functions:**")
        out += [f"- `def {fn['name']}()`: {fn['doc']}" for fn in mod["functions"]]
    if mod["imports"]:
        out.append("**Imports:** " + ", ".join(f"`{i}`" for i in mod["imports"]))
    return "\n".join(out) + "\n"


@tool_main
def run(args: dict) -> dict:
    target = Path(args.get("path") or ".")
    if not target.exists():
        return {"ok": False, "error": f"not found: {target}"}

    if target.is_file():
        mod = _analyze(target, target.name)
        return {"tool": "report", "kind": "file", "modules": [mod], "markdown": _md(mod)}

    mods: list[dict] = []
    ignores = set(_IGNORES)
    for dirpath, dirnames, filenames in os.walk(target):
        # Sidecar pruned by PATH, not by name - see _toolkit.is_instance_path.
        dirnames[:] = sorted(d for d in dirnames if d not in ignores
                             and not is_instance_path(Path(dirpath) / d))
        for f in sorted(filenames):
            if f.endswith(".py"):
                fp = Path(dirpath) / f
                mods.append(_analyze(fp, str(fp.relative_to(target)).replace("\\", "/")))

    return {
        "tool": "report", "kind": "dir",
        "summary": {
            "files": len(mods),
            "classes": sum(len(m.get("classes", [])) for m in mods),
            "functions": sum(len(m.get("functions", [])) for m in mods),
        },
        # `modules` is DECLARED in this tool's manifest and the file branch already
        # returned it; the directory branch computed `mods`, rendered it to prose, and
        # threw the structure away. So the manifest promised a field the common path
        # never returned - a documented claim with nothing behind it (E10), found by the
        # C1b audit (journal 0032).
        #
        # It matters beyond tidiness: every module's `purpose` docstring was in here,
        # reachable only by parsing the markdown back out of prose. A consumer that has
        # to re-parse a rendering to recover the data that produced it is a consumer
        # working around a contract, not using one.
        "modules": mods,
        "markdown": "\n---\n".join(_md(m) for m in mods),
    }
