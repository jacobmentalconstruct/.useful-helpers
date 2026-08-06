"""
FILE:       tools/module_decomp_plan/cli.py
ROLE:       Module decomposition planner.
DOMAIN:     tool
DOES:       Uses AST symbol spans, complexity cues, and import density to propose bounded
            refactor/decomposition candidates for Python modules.
DEPENDS ON: tools._toolkit, tools.code_intel_shared, (stdlib) ast, collections
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from donor code-intel aspirations; observe-only planning, no edits.
"""
from __future__ import annotations

import ast
from collections import Counter

from tools._toolkit import tool_main
from tools.code_intel_shared import index_symbols, parse_python_files, python_import_names, resolve_root

BRANCH_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.ExceptHandler, ast.Match, ast.IfExp)


def _complexity(node: ast.AST) -> int:
    score = 1
    for child in ast.walk(node):
        if isinstance(child, BRANCH_NODES):
            score += 1
        elif isinstance(child, ast.BoolOp):
            score += max(1, len(child.values) - 1)
    return score


def _symbol_nodes(tree: ast.AST) -> list[ast.AST]:
    rows = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            rows.append(node)
    rows.sort(key=lambda n: int(getattr(n, "lineno", 1) or 1))
    return rows


@tool_main
def run(args: dict) -> dict:
    root, error = resolve_root(args.get("root"))
    if error:
        return {"ok": False, "error": error}
    assert root is not None

    max_files = max(1, min(int(args.get("max_files", 500)), 5000))
    limit = max(1, min(int(args.get("limit", 20)), 200))
    parsed = parse_python_files(root, max_files=max_files)
    all_symbols = index_symbols(parsed)
    symbol_counts = Counter(s.path for s in all_symbols)

    candidates = []
    parse_errors = [{"path": p.rel, "error": p.error} for p in parsed if p.error]
    for p in parsed:
        if p.tree is None:
            continue
        lines = max(1, len(p.text.splitlines()))
        imports = []
        for node in ast.walk(p.tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.extend(python_import_names(node))
        nodes = _symbol_nodes(p.tree)
        complex_symbols = []
        for node in nodes:
            line = int(getattr(node, "lineno", 1) or 1)
            end = int(getattr(node, "end_lineno", line) or line)
            comp = _complexity(node)
            span = max(1, end - line + 1)
            if comp >= 8 or span >= 80:
                complex_symbols.append({
                    "name": str(getattr(node, "name", "")),
                    "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                    "line_start": line,
                    "line_end": end,
                    "lines": span,
                    "complexity": comp,
                })
        reasons = []
        if lines >= 250:
            reasons.append("large_module")
        if symbol_counts[p.rel] >= 12:
            reasons.append("many_symbols")
        if len(imports) >= 15:
            reasons.append("many_imports")
        if complex_symbols:
            reasons.append("complex_symbols")
        if not reasons:
            continue
        score = lines // 25 + symbol_counts[p.rel] + len(imports) + sum(s["complexity"] for s in complex_symbols)
        suggestions = []
        if complex_symbols:
            suggestions.append("Extract the largest/most complex functions first behind a narrow helper API.")
        if symbol_counts[p.rel] >= 12:
            suggestions.append("Group related symbols by responsibility and move one group per commit.")
        if len(imports) >= 15:
            suggestions.append("Review import clusters; they often reveal candidate dependency boundaries.")
        candidates.append({
            "path": p.rel,
            "lines": lines,
            "symbol_count": symbol_counts[p.rel],
            "import_count": len(imports),
            "score": score,
            "reasons": reasons,
            "complex_symbols": complex_symbols[:10],
            "suggestions": suggestions,
        })

    candidates.sort(key=lambda r: r["score"], reverse=True)
    return {
        "tool": "module_decomp_plan",
        "root": root.as_posix(),
        "candidate_count": len(candidates),
        "candidates": candidates[:limit],
        "parse_errors": parse_errors,
        "truncated": len(parsed) >= max_files or len(candidates) > limit,
        "summary": {
            "files": len(parsed),
            "candidates": len(candidates),
            "returned": min(len(candidates), limit),
            "parse_errors": len(parse_errors),
        },
    }

