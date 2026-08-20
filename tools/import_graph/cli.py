"""
FILE:       tools/import_graph/cli.py
ROLE:       Python import graph analyzer.
DOMAIN:     tool
DOES:       Parses workspace-local Python files, extracts imports, resolves likely internal
            edges, reports external imports, fan-in/fan-out, and simple cycles.
DEPENDS ON: tools._toolkit, tools.code_intel_shared, (stdlib) ast, collections
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      AST-lite import extraction. Deterministic and objective  -  trust it.
"""
from __future__ import annotations

import ast
from collections import Counter, defaultdict

from tools._toolkit import tool_main
from tools.code_intel_shared import (
    iter_python_files,
    module_name,
    parse_python_files,
    python_import_names,
    resolve_root,
)

#: How far the cheap PATH-ONLY module index may walk. Bounded like everything else, but
#: an order above the parse cap: collecting names costs no read, so the thing that makes
#: internal/external classification correct should not be the thing that runs out first.
MODULE_INDEX_CAP = 5000


def _resolve_internal(import_name: str, modules: set[str], aliases: dict[str, str]) -> str:
    name = import_name.lstrip(".")
    parts = name.split(".")
    for i in range(len(parts), 0, -1):
        candidate = ".".join(parts[:i])
        if candidate in modules:
            return candidate
        if candidate in aliases:
            return aliases[candidate]
    return ""


def _cycles(edges: list[dict], limit: int) -> list[list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        graph[edge["from_module"]].append(edge["to_module"])

    found: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()

    def visit(start: str, node: str, stack: list[str]) -> None:
        if len(found) >= limit or len(stack) > 12:
            return
        for nxt in graph.get(node, []):
            if nxt == start:
                cycle = stack + [start]
                key = tuple(sorted(cycle[:-1]))
                if key not in seen:
                    seen.add(key)
                    found.append(cycle)
                continue
            if nxt in stack:
                continue
            visit(start, nxt, stack + [nxt])

    for node in sorted(graph):
        visit(node, node, [node])
        if len(found) >= limit:
            break
    return found


@tool_main
def run(args: dict) -> dict:
    root, error = resolve_root(args.get("root"))
    if error:
        return {"ok": False, "error": error}
    assert root is not None

    max_files = max(1, min(int(args.get("max_files", 500)), 5000))
    cycle_limit = max(0, min(int(args.get("cycle_limit", 20)), 100))
    parsed = parse_python_files(root, max_files=max_files)

    # THE MODULE UNIVERSE COMES FROM PATHS, NOT FROM PARSING.
    #
    # `modules` was built from the CAPPED parse set, so on a project larger than the cap
    # every import pointing at an unparsed file was classified EXTERNAL. That does not
    # degrade the answer, it INVERTS it: measured on a real 805-file target, the default
    # cap of 500 produced `internal_edges: 0` and `hubs: []`, while the same target
    # uncapped produced 681 edges and 50 hotspots. Zero is not a smaller version of 681 -
    # it is the opposite claim, reported with the same confidence.
    #
    # Awareness promotes its canonical handles from those hubs, so the visible symptom was
    # `attach` offering NO handles at all on a nontrivial software project - the T8 loop's
    # first step, "start from a handle awareness promoted", had nothing to start from.
    #
    # A module NAME is derived from its path; it costs no read and no parse. So the index
    # spans the whole tree while the expensive half stays bounded, and truncating the
    # parse now loses edges it could not see rather than misclassifying the ones it could.
    #
    # Found by the release walk against a real target. Every fixture before it was smaller
    # than the cap, which is exactly why none of them could see this.
    index_paths = iter_python_files(root, max_files=MODULE_INDEX_CAP)
    modules = {m for m in (module_name(root, p) for p in index_paths) if m}
    module_by_path = {p.rel: module_name(root, p.path) for p in parsed}
    aliases = {f"{root.name}.{mod}": mod for mod in modules if mod}
    imports = []
    internal_edges = []
    external = Counter()
    parse_errors = [{"path": p.rel, "error": p.error} for p in parsed if p.error]

    for p in parsed:
        if p.tree is None:
            continue
        src_mod = module_by_path[p.rel]
        for node in ast.walk(p.tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            names = python_import_names(node)
            line = int(getattr(node, "lineno", 1) or 1)
            for name in names:
                target = _resolve_internal(name, modules, aliases)
                row = {"path": p.rel, "module": src_mod, "line": line, "import": name,
                       "internal_module": target}
                imports.append(row)
                if target:
                    internal_edges.append({"from_module": src_mod, "to_module": target,
                                           "path": p.rel, "line": line, "import": name})
                else:
                    external[name.split(".", 1)[0]] += 1

    fan_in = Counter(edge["to_module"] for edge in internal_edges)
    fan_out = Counter(edge["from_module"] for edge in internal_edges)
    hotspots = [
        {"module": mod, "fan_in": fan_in.get(mod, 0), "fan_out": fan_out.get(mod, 0)}
        for mod in sorted(modules)
        if fan_in.get(mod, 0) or fan_out.get(mod, 0)
    ]
    hotspots.sort(key=lambda r: (r["fan_in"] + r["fan_out"], r["fan_in"]), reverse=True)

    return {
        "tool": "import_graph",
        "root": root.as_posix(),
        "file_count": len(parsed),
        "module_count": len(modules),
        "import_count": len(imports),
        "internal_edge_count": len(internal_edges),
        "external_imports": [{"name": name, "count": count} for name, count in external.most_common()],
        "internal_edges": internal_edges,
        "hotspots": hotspots[:50],
        "cycles": _cycles(internal_edges, cycle_limit) if cycle_limit else [],
        "parse_errors": parse_errors,
        "truncated": len(parsed) >= max_files,
        "summary": {
            "files": len(parsed),
            "modules": len(modules),
            "internal_edges": len(internal_edges),
            "external_roots": len(external),
            "parse_errors": len(parse_errors),
        },
    }
