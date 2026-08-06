"""
FILE:       tools/test_scaffold/cli.py
ROLE:       Preview-first Python test scaffold generator.
DOMAIN:     tool
DOES:       Reads a Python module, extracts public functions/classes, and emits a unittest or
            pytest-style starter test file; writes only with write:true.
DEPENDS ON: tools._toolkit, tools.code_intel_shared, (stdlib) ast, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Generated tests are starters, not coverage.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from tools._toolkit import tool_main
from tools.code_intel_shared import is_inside, project_root, rel


def _slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_").lower()
    return s or "module"


def _public_symbols(tree: ast.AST) -> list[dict]:
    rows = []
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            if name.startswith("_"):
                continue
            rows.append({"name": name, "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                         "async": isinstance(node, ast.AsyncFunctionDef),
                         "line": int(getattr(node, "lineno", 1) or 1)})
    return rows


def _module_import(root: Path, path: Path) -> str:
    rp = path.resolve().relative_to(root.resolve()).with_suffix("")
    parts = list(rp.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _render_unittest(module: str, symbols: list[dict]) -> str:
    class_name = "Test" + "".join(part.capitalize() for part in module.split(".")[-1].split("_"))
    lines = [
        "import unittest",
        "",
        f"import {module} as target",
        "",
        "",
        f"class {class_name}(unittest.TestCase):",
    ]
    if not symbols:
        lines.extend(["    def test_module_imports(self):", "        self.assertIsNotNone(target)"])
    for sym in symbols:
        lines.extend([
            f"    def test_{_slug(sym['name'])}_placeholder(self):",
            f"        self.assertTrue(hasattr(target, {sym['name']!r}))",
            "",
        ])
    lines.extend(["", "if __name__ == '__main__':", "    unittest.main()", ""])
    return "\n".join(lines)


def _render_pytest(module: str, symbols: list[dict]) -> str:
    lines = [f"import {module} as target", ""]
    if not symbols:
        lines.extend(["def test_module_imports():", "    assert target is not None", ""])
    for sym in symbols:
        lines.extend([
            f"def test_{_slug(sym['name'])}_placeholder():",
            f"    assert hasattr(target, {sym['name']!r})",
            "",
        ])
    return "\n".join(lines)


@tool_main
def run(args: dict) -> dict:
    root = project_root()
    path = (root / str(args.get("path") or "")).resolve()
    if not path.is_file():
        return {"ok": False, "error": f"path is not a file: {path}"}
    if not is_inside(root, path):
        return {"ok": False, "error": "path must stay inside the project workspace"}
    if path.suffix != ".py":
        return {"ok": False, "error": "test_scaffold currently supports Python .py files"}

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text, filename=rel(root, path))
    except (OSError, SyntaxError) as exc:
        return {"ok": False, "error": str(exc)}

    framework = str(args.get("framework") or "unittest").lower()
    if framework not in {"unittest", "pytest"}:
        return {"ok": False, "error": "framework must be unittest or pytest"}
    symbols = _public_symbols(tree)
    module = str(args.get("module") or _module_import(root, path))
    content = _render_pytest(module, symbols) if framework == "pytest" else _render_unittest(module, symbols)

    default_out = root / "tests" / f"test_{path.stem}.py"
    out_arg = args.get("out")
    out_path = (root / str(out_arg)).resolve() if out_arg else default_out
    if not is_inside(root, out_path):
        return {"ok": False, "error": "out must stay inside the project workspace"}
    write = bool(args.get("write", False))
    written = False
    if write:
        if out_path.exists() and not bool(args.get("overwrite", False)):
            return {"ok": False, "error": f"refusing to overwrite existing file: {rel(root, out_path)}"}
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        written = True

    return {
        "tool": "test_scaffold",
        "source": rel(root, path),
        "out": rel(root, out_path),
        "framework": framework,
        "symbol_count": len(symbols),
        "symbols": symbols,
        "content": content,
        "written": written,
        "summary": {"symbols": len(symbols), "written": written},
    }

