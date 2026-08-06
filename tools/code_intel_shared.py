"""
FILE:       tools/code_intel_shared.py
ROLE:       Shared AST helpers for code-intelligence tools.
DOMAIN:     tool (shared substrate)
DOES:       Provides workspace-bounded Python file walking, AST parsing, import extraction,
            symbol indexing, and conservative expression rendering.
DEPENDS ON: (stdlib) ast, os, pathlib
WIRES TO:   tools/import_graph, complexity_score, dead_code, blocking_call_scan,
            tkinter_widget_tree
NOTES:      Shared AST-lite substrate for the code-intelligence tools: one walker,
            one skip-set, one relative-path helper.
"""
from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from tools._toolkit import toolkit_home_names

DEFAULT_SKIP_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
    "_artifacts",
}


@dataclass(frozen=True)
class ParsedFile:
    path: Path
    rel: str
    text: str
    tree: ast.AST | None
    error: str = ""


@dataclass(frozen=True)
class Symbol:
    name: str
    qualname: str
    kind: str
    path: str
    line_start: int
    line_end: int
    private: bool
    test_like: bool


def project_root() -> Path:
    return Path.cwd().resolve()


def resolve_root(arg: str | None) -> tuple[Path | None, str]:
    root = (project_root() / (arg or ".")).resolve()
    if not root.exists() or not root.is_dir():
        return None, f"root is not a directory: {root}"
    if not is_inside(project_root(), root):
        return None, "root must stay inside the project workspace"
    return root, ""


def is_inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def iter_python_files(root: Path, *, max_files: int = 500) -> list[Path]:
    skip = set(DEFAULT_SKIP_DIRS) | toolkit_home_names()
    out: list[Path] = []
    for current, dir_names, file_names in os.walk(root):
        dir_names[:] = sorted(d for d in dir_names if d not in skip)
        for name in sorted(file_names):
            if not name.endswith(".py"):
                continue
            out.append(Path(current) / name)
            if len(out) >= max_files:
                return out
    return out


def parse_python_files(root: Path, *, max_files: int = 500) -> list[ParsedFile]:
    rows: list[ParsedFile] = []
    for path in iter_python_files(root, max_files=max_files):
        rp = rel(root, path)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            rows.append(ParsedFile(path=path, rel=rp, text="", tree=None, error=str(exc)))
            continue
        try:
            tree = ast.parse(text, filename=rp)
        except SyntaxError as exc:
            rows.append(ParsedFile(path=path, rel=rp, text=text, tree=None,
                                   error=f"{exc.msg} at line {exc.lineno}"))
            continue
        rows.append(ParsedFile(path=path, rel=rp, text=text, tree=tree))
    return rows


def module_name(root: Path, path: Path) -> str:
    rp = path.resolve().relative_to(root.resolve())
    parts = list(rp.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def python_import_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        module = "." * int(node.level or 0) + str(node.module or "")
        return [f"{module}.{alias.name}".strip(".") for alias in node.names]
    return []


def expr_to_str(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{expr_to_str(node.value)}.{node.attr}"
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Call):
        return f"{expr_to_str(node.func)}(...)"
    if isinstance(node, ast.Subscript):
        return f"{expr_to_str(node.value)}[...]"
    if isinstance(node, ast.Lambda):
        return "lambda"
    return node.__class__.__name__


def call_name(node: ast.Call) -> str:
    return expr_to_str(node.func)


class SymbolIndexer(ast.NodeVisitor):
    def __init__(self, parsed: ParsedFile):
        self.parsed = parsed
        self.class_stack: list[str] = []
        self.symbols: list[Symbol] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._add(node, "class")
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._add(node, "function" if not self.class_stack else "method")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._add(node, "async_function" if not self.class_stack else "async_method")
        self.generic_visit(node)

    def _add(self, node: ast.AST, kind: str) -> None:
        name = str(getattr(node, "name", ""))
        qual = ".".join([*self.class_stack, name]) if self.class_stack else name
        line = int(getattr(node, "lineno", 1) or 1)
        end = int(getattr(node, "end_lineno", line) or line)
        self.symbols.append(Symbol(
            name=name,
            qualname=qual,
            kind=kind,
            path=self.parsed.rel,
            line_start=line,
            line_end=end,
            private=name.startswith("_"),
            test_like=self.parsed.rel.startswith("tests/") or name.startswith("test_") or name.startswith("Test"),
        ))


def index_symbols(parsed_files: Iterable[ParsedFile]) -> list[Symbol]:
    symbols: list[Symbol] = []
    for parsed in parsed_files:
        if parsed.tree is None:
            continue
        visitor = SymbolIndexer(parsed)
        visitor.visit(parsed.tree)
        symbols.extend(visitor.symbols)
    return symbols


class CallCollector(ast.NodeVisitor):
    def __init__(self):
        self.calls: list[tuple[str, int]] = []

    def visit_Call(self, node: ast.Call) -> None:
        self.calls.append((call_name(node), int(getattr(node, "lineno", 1) or 1)))
        self.generic_visit(node)
