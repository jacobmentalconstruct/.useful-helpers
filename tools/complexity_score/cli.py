"""
FILE:       tools/complexity_score/cli.py
ROLE:       Python complexity and hotspot scorer.
DOMAIN:     tool
DOES:       Scores functions/classes/modules with cyclomatic-ish branch counts, nesting,
            line spans, and ranks likely review hotspots.
DEPENDS ON: tools._toolkit, tools.code_intel_shared, (stdlib) ast, collections
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      REHOME (rewritten) from donor AST-analysis patterns; intentionally heuristic.
"""
from __future__ import annotations

import ast
from collections import Counter

from tools._toolkit import tool_main
from tools.code_intel_shared import parse_python_files, resolve_root

BRANCH_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ExceptHandler,
    ast.IfExp,
    ast.Assert,
    ast.Try,
    ast.Match,
)


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self, path: str):
        self.path = path
        self.class_stack: list[str] = []
        self.rows: list[dict] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        line = int(getattr(node, "lineno", 1) or 1)
        end = int(getattr(node, "end_lineno", line) or line)
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        self.rows.append({
            "path": self.path,
            "kind": "class",
            "name": ".".join([*self.class_stack, node.name]) if self.class_stack else node.name,
            "line_start": line,
            "line_end": end,
            "lines": max(1, end - line + 1),
            "complexity": 1 + len(methods),
            "max_nesting": _max_nesting(node),
            "methods": len(methods),
        })
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._function(node, "function")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._function(node, "async_function")
        self.generic_visit(node)

    def _function(self, node: ast.AST, kind: str) -> None:
        name = str(getattr(node, "name", ""))
        qual = ".".join([*self.class_stack, name]) if self.class_stack else name
        line = int(getattr(node, "lineno", 1) or 1)
        end = int(getattr(node, "end_lineno", line) or line)
        branches = 0
        bool_ops = 0
        returns = 0
        raises = 0
        awaits = 0
        for child in ast.walk(node):
            if isinstance(child, BRANCH_NODES):
                branches += 1
            elif isinstance(child, ast.BoolOp):
                bool_ops += max(1, len(child.values) - 1)
            elif isinstance(child, ast.Return):
                returns += 1
            elif isinstance(child, ast.Raise):
                raises += 1
            elif isinstance(child, ast.Await):
                awaits += 1
        complexity = 1 + branches + bool_ops
        lines = max(1, end - line + 1)
        self.rows.append({
            "path": self.path,
            "kind": "method" if self.class_stack else kind,
            "name": qual,
            "line_start": line,
            "line_end": end,
            "lines": lines,
            "complexity": complexity,
            "max_nesting": _max_nesting(node),
            "returns": returns,
            "raises": raises,
            "awaits": awaits,
            "score": complexity * 2 + lines // 20 + _max_nesting(node),
        })


def _max_nesting(node: ast.AST) -> int:
    max_depth = 0

    def walk(child: ast.AST, depth: int) -> None:
        nonlocal max_depth
        nested = isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With,
                                    ast.AsyncWith, ast.Match))
        next_depth = depth + 1 if nested else depth
        max_depth = max(max_depth, next_depth)
        for grand in ast.iter_child_nodes(child):
            walk(grand, next_depth)

    walk(node, 0)
    return max_depth


@tool_main
def run(args: dict) -> dict:
    root, error = resolve_root(args.get("root"))
    if error:
        return {"ok": False, "error": error}
    assert root is not None

    max_files = max(1, min(int(args.get("max_files", 500)), 5000))
    limit = max(1, min(int(args.get("limit", 25)), 200))
    parsed = parse_python_files(root, max_files=max_files)

    rows: list[dict] = []
    module_scores: Counter[str] = Counter()
    parse_errors = [{"path": p.rel, "error": p.error} for p in parsed if p.error]
    for p in parsed:
        if p.tree is None:
            continue
        visitor = ComplexityVisitor(p.rel)
        visitor.visit(p.tree)
        rows.extend(visitor.rows)
        module_scores[p.rel] += sum(r.get("score", r.get("complexity", 1)) for r in visitor.rows)

    hotspots = sorted(rows, key=lambda r: (r.get("score", r.get("complexity", 0)),
                                           r.get("complexity", 0), r.get("lines", 0)),
                      reverse=True)[:limit]
    module_hotspots = [{"path": path, "score": score} for path, score in module_scores.most_common(limit)]
    return {
        "tool": "complexity_score",
        "root": root.as_posix(),
        "file_count": len(parsed),
        "symbol_count": len(rows),
        "hotspots": hotspots,
        "module_hotspots": module_hotspots,
        "parse_errors": parse_errors,
        "truncated": len(parsed) >= max_files,
        "summary": {
            "files": len(parsed),
            "symbols": len(rows),
            "hotspots_returned": len(hotspots),
            "parse_errors": len(parse_errors),
        },
    }

