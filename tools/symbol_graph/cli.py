"""
FILE:       tools/symbol_graph/cli.py
ROLE:       Query surface over the resolved symbol graph - who defines, who refers, who is unused.
DOMAIN:     tool
DOES:       action=stats: graph shape + the honesty ledger (what could NOT be resolved).
            action=refs: a symbol's definition, resolved inbound references (real callers, not
            name coincidences), and resolved outbound references.
            action=build: persist the full graph as an artifact for other consumers.
            action=summarize: one-sentence purpose per module (G5), through the governed
            inference seam, CAS-cached by file hash so re-runs only pay for changed files.
DEPENDS ON: tools._toolkit, tools.symbol_graph_shared, tools.llm_shared (summarize)
WIRES TO:   invoked by src/core/invoke.py; substrate shared with dead_code and
            domain_boundary_audit so all three answer from the SAME facts.
NOTES:      The graph is rebuilt per call rather than cached: a build is sub-second at toolkit
            scale, and a stale cached answer that LOOKS resolved is worse than the cost of
            re-parsing. `refs` answers carry `fuzzy_attr_count` and the unresolved ledger so a
            caller can see the boundary of what "no references" actually proves.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from tools._toolkit import output_root, resolve_within_roots, tool_main
from tools.symbol_graph_shared import build_graph

SUMMARY_MODEL = os.environ.get("SUITE_SUMMARY_MODEL", "qwen2.5:3b")

_SUM_PROMPT = (
    "In ONE plain sentence, state what this Python module is FOR - its job in the project, "
    "not a list of its functions. Ground it only in the evidence below. No preamble.\n\n")


def _summaries_path() -> "Path":
    return output_root() / "symbol_graph" / "summaries.json"


def _load_summaries() -> dict:
    p = _summaries_path()
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _summarize(graph: dict, root, args: dict) -> dict:
    """G5: one-sentence purpose per module, CAS-cached by file content hash.

    The cache key is the file's sha256, so a re-run summarizes ONLY what changed - the same
    free-lunch contract bd_index keeps for vectors. Degrades honestly: with no local model the
    call reports exactly which modules are missing summaries instead of pretending."""
    from tools import llm_shared

    max_nodes = max(1, min(int(args.get("max_nodes", 40)), 200))
    cache = _load_summaries()
    modules = graph["modules"]

    todo = []          # (module, path, sha, evidence)
    fresh: dict[str, dict] = {}
    for mod, info in sorted(modules.items()):
        fpath = root / info["path"]
        try:
            body = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        cached = cache.get(info["path"])
        if cached and cached.get("sha") == sha:
            fresh[info["path"]] = cached
            continue
        tree_syms = [s for s in graph["symbols"].values() if s["module"] == mod]
        doc = ""
        stripped = body.lstrip()
        if stripped[:3] in ('"""', "'''"):
            doc = stripped[3:stripped.find(stripped[:3], 3)][:600]
        evidence = (f"path: {info['path']}\ndocstring: {doc or '(none)'}\n"
                    f"defines: {', '.join(s['qualname'] for s in tree_syms[:25]) or '(nothing)'}\n"
                    f"head:\n" + "\n".join(body.splitlines()[:20]))
        todo.append((mod, info["path"], sha, evidence))

    probe = llm_shared.probe(SUMMARY_MODEL, kind="chat")
    summarized = 0
    truncated = len(todo) > max_nodes
    if probe["available"]:
        for mod, rel_path, sha, evidence in todo[:max_nodes]:
            out = llm_shared.chat(SUMMARY_MODEL, _SUM_PROMPT + evidence[:4000],
                                  purpose="node.summary", num_predict=90, temperature=0.1)
            if not out["ok"]:
                break
            text = " ".join(str(out["content"]).split()).strip()
            if text:
                fresh[rel_path] = {"sha": sha, "module": mod, "summary": text}
                summarized += 1

    # persist the union so partial progress is never thrown away
    merged = {**cache, **fresh}
    p = _summaries_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(merged, indent=1), encoding="utf-8")

    missing = [t[1] for t in todo if t[1] not in fresh]
    return {
        "tool": "symbol_graph", "action": "summarize", "root": root.as_posix(),
        "modules": len(modules), "cached": len(fresh) - summarized, "summarized": summarized,
        "missing": missing[:50], "missing_count": len(missing),
        "truncated": truncated,
        "backend": probe["backend"] if probe["available"] else None,
        "degraded": not probe["available"],
        "written": str(p),
        **({} if probe["available"] else
           {"note": f"no summary backend reachable ({probe['error']}); cache untouched, "
                    "missing modules listed honestly"}),
    }


def _find_symbols(graph: dict, query: str) -> list[str]:
    """Match a query against symbol ids: exact id, exact qualname, exact name, then substring."""
    symbols = graph["symbols"]
    if query in symbols:
        return [query]
    exact_qual = [sid for sid, s in symbols.items() if s["qualname"] == query]
    if exact_qual:
        return exact_qual
    exact_name = [sid for sid, s in symbols.items() if s["name"] == query]
    if exact_name:
        return exact_name
    q = query.lower()
    return [sid for sid in symbols if q in sid.lower()][:20]


@tool_main
def run(args: dict) -> dict:
    action = str(args.get("action", "stats")).lower()
    root, err = resolve_within_roots(str(args.get("root") or "."))
    if err:
        return {"ok": False, "error": err}
    max_files = max(1, min(int(args.get("max_files", 2000)), 5000))

    graph = build_graph(root, max_files=max_files)
    honesty = {
        "unresolved": graph["unresolved"],
        "fuzzy_attr_kinds": len(graph["fuzzy_attr_uses"]),
        "parse_errors": graph["parse_errors"],
        "note": ("`refs` edges are RESOLVED (bound through an import or local definition). "
                 "Dynamic dispatch, star imports, and untyped attribute access are counted in "
                 "the ledger, not silently ignored - absence of a resolved ref is only as "
                 "strong as this ledger is small."),
    }

    if action == "stats":
        return {
            "tool": "symbol_graph", "action": "stats", "root": root.as_posix(),
            "files": graph["file_count"], "modules": len(graph["modules"]),
            "symbols": len(graph["symbols"]), "imports": len(graph["imports"]),
            "refs": len(graph["refs"]),
            "external_imports": dict(sorted(graph["external_imports"].items(),
                                            key=lambda kv: -kv[1])[:20]),
            "honesty": honesty,
        }

    if action == "refs":
        query = str(args.get("symbol") or "").strip()
        if not query:
            return {"ok": False, "error": "symbol is required for refs (name, qualname, or id)"}
        matches = _find_symbols(graph, query)
        if not matches:
            return {"ok": False, "error": f"no symbol matches {query!r}",
                    "hint": "try action=stats, or a bare name like 'run'"}
        limit = max(1, min(int(args.get("limit", 50)), 500))
        out = []
        for sid in matches[:10]:
            s = graph["symbols"][sid]
            inbound = [r for r in graph["refs"] if r["dst"] == sid][:limit]
            outbound = [r for r in graph["refs"] if r["src"] == sid][:limit]
            module_summary = (_load_summaries().get(s["path"]) or {}).get("summary")
            out.append({
                "id": sid, "kind": s["kind"], "path": s["path"],
                "module_summary": module_summary,
                "lines": [s["line_start"], s["line_end"]],
                "decorators": s["decorators"],
                "inbound_count": len([r for r in graph["refs"] if r["dst"] == sid]),
                "inbound": inbound,
                "outbound": outbound,
                "fuzzy_attr_count": graph["fuzzy_attr_uses"].get(s["name"], 0),
            })
        return {"tool": "symbol_graph", "action": "refs", "root": root.as_posix(),
                "query": query, "match_count": len(matches), "symbols": out,
                "honesty": honesty}

    if action == "summarize":
        return _summarize(graph, root, args)

    if action == "build":
        dest = output_root() / "symbol_graph" / "graph.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(graph, indent=1), encoding="utf-8")
        return {"tool": "symbol_graph", "action": "build", "root": root.as_posix(),
                "written": str(dest), "files": graph["file_count"],
                "symbols": len(graph["symbols"]), "refs": len(graph["refs"]),
                "honesty": honesty}

    return {"ok": False, "error": f"unknown action {action!r}; use stats|refs|build"}
