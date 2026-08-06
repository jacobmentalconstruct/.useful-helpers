"""
FILE:       tools/dead_code/cli.py
ROLE:       Unused-symbol scanner, answered from the RESOLVED symbol graph.
DOMAIN:     tool
DOES:       Builds the resolved symbol graph, seeds a root set (framework entrypoints, exports,
            lifecycle names, tests), and reports the symbols UNREACHABLE from any root - with
            fuzzy attribute-name evidence downgrading confidence, never silently granting life.
DEPENDS ON: tools._toolkit, tools.code_intel_shared (resolve_root), tools.symbol_graph_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      The predecessor counted name coincidence as life: any file mentioning `run` kept
            every `run` alive, and two dead functions calling each other read as referenced -
            both invisible by construction. Reachability over RESOLVED edges is the fix: a
            symbol is a candidate when no path from any live root reaches it, and a reference
            from another unreachable symbol no longer counts as life. Framework-decorated and
            __all__-exported symbols are ROOTS now (the graph can tell they are live), so they
            stop appearing as low-confidence noise in the candidate list. Still signals, not
            verdicts: the honesty ledger (dynamic dispatch, star imports) bounds what
            "unreachable" proves, and fuzzy attribute matches cap confidence at medium.
"""
from __future__ import annotations

from tools._toolkit import tool_main
from tools.code_intel_shared import resolve_root
from tools.symbol_graph_shared import build_graph, reachable_symbols

ENTRYPOINT_NAMES = {"main", "run", "cli", "app", "setup", "teardown"}
LIFECYCLE_NAMES = {"__init__", "__enter__", "__exit__", "__aenter__", "__aexit__", "__call__"}

# Framework-entrypoint decorators (final attribute/name): a symbol carrying one is invoked by a
# framework, not by a static caller. Matched on the LAST name so @app.command, @router.get,
# @cli.callback all hit. Extend per project via the `entrypoint_decorators` arg.
DEFAULT_ENTRYPOINT_DECORATORS = {
    # Typer / click
    "command", "callback", "group",
    # FastAPI / Starlette / Flask routing + lifecycle
    "get", "post", "put", "delete", "patch", "options", "head", "route", "websocket",
    "on_event", "middleware", "exception_handler", "before_request", "after_request",
    # pytest / registration / descriptors that imply external invocation
    "fixture", "register", "setter", "getter", "deleter", "abstractmethod",
    "property", "cached_property",
}


def _test_like(sym: dict) -> bool:
    return (sym["path"].startswith("tests/") or sym["name"].startswith("test_")
            or sym["name"].startswith("Test"))


@tool_main
def run(args: dict) -> dict:
    root, error = resolve_root(args.get("root"))
    if error:
        return {"ok": False, "error": error}
    assert root is not None

    max_files = max(1, min(int(args.get("max_files", 500)), 5000))
    limit = max(1, min(int(args.get("limit", 50)), 500))
    include_private = bool(args.get("include_private", False))
    entrypoint_decorators = set(DEFAULT_ENTRYPOINT_DECORATORS) | {
        str(x) for x in (args.get("entrypoint_decorators") or [])}

    graph = build_graph(root, max_files=max_files)
    symbols = graph["symbols"]
    exports_by_module = {m: set(info.get("exports") or []) for m, info in graph["modules"].items()}

    # -- roots: everything with a legitimate reason to have no static caller ------------------
    roots: set[str] = set()
    root_reasons: dict[str, int] = {"framework_decorator": 0, "exported": 0,
                                    "entrypoint_or_lifecycle": 0, "test_like": 0, "dunder": 0}
    for sid, s in symbols.items():
        if any(d in entrypoint_decorators for d in s["decorators"]):
            reason = "framework_decorator"
        elif s["name"] in exports_by_module.get(s["module"], ()):
            reason = "exported"
        elif s["name"] in ENTRYPOINT_NAMES or s["name"] in LIFECYCLE_NAMES:
            reason = "entrypoint_or_lifecycle"
        elif _test_like(s):
            reason = "test_like"
        elif s["name"].startswith("__") and s["name"].endswith("__"):
            reason = "dunder"
        else:
            continue
        roots.add(sid)
        root_reasons[reason] += 1

    # Interface overrides are live BY CONSTRUCTION: a method overriding a same-named method of a
    # resolved base class that is itself a root (e.g. an @abstractmethod) is invoked through the
    # interface, not by name. Transitive over the resolved base chain.
    method_names_of: dict[str, dict[str, str]] = {}
    for sid, s in symbols.items():
        if "." in s["qualname"]:
            cls_id = f"{s['module']}::{s['qualname'].rsplit('.', 1)[0]}"
            method_names_of.setdefault(cls_id, {})[s["name"]] = sid

    def _base_chain(cls_id: str, seen: set) -> list:
        out = []
        for b in (symbols.get(cls_id, {}).get("bases") or []):
            if b not in seen:
                seen.add(b)
                out.append(b)
                out.extend(_base_chain(b, seen))
        return out

    root_reasons["implements_interface"] = 0
    for cls_id, s in list(symbols.items()):
        if s["kind"] != "class" or not s.get("bases"):
            continue
        for base_id in _base_chain(cls_id, {cls_id}):
            for mname, msid in method_names_of.get(base_id, {}).items():
                if msid in roots:
                    override = method_names_of.get(cls_id, {}).get(mname)
                    if override and override not in roots:
                        roots.add(override)
                        root_reasons["implements_interface"] += 1

    # Two tiers: `strict_live` is proven over resolved edges alone; `dispatch_live` also grants
    # every method of a live class (frameworks that getattr their way to methods - NodeVisitor's
    # visit_*, handler registries). Live only under the second assumption = a medium lead. Dead
    # under BOTH = dead under every assumption we can model. This also stops the confidence
    # cascade where a helper called only by dynamically-dispatched methods read as a
    # high-confidence dead cluster.
    strict_live = reachable_symbols(graph, roots)
    dispatch_live = reachable_symbols(graph, roots, assume_method_dispatch=True)
    fuzzy = graph["fuzzy_attr_uses"]
    inbound_count: dict[str, int] = {}
    for r in graph["refs"]:
        inbound_count[r["dst"]] = inbound_count.get(r["dst"], 0) + 1

    candidates = []
    skipped = dict(root_reasons)
    skipped["private_filtered"] = 0
    for sid, s in symbols.items():
        if sid in strict_live or sid in roots:
            continue
        if s["name"].startswith("_") and not include_private:
            skipped["private_filtered"] += 1
            continue
        fuzzy_hits = fuzzy.get(s["name"], 0)
        inbound = inbound_count.get(sid, 0)
        if sid in dispatch_live and fuzzy_hits:
            # two INDEPENDENT signs of life (live class + something somewhere names this
            # attribute) - almost certainly dispatched dynamically; a lead, not a call to action
            confidence = "low"
            reason = (f"method of a live class AND {fuzzy_hits} attribute-name match(es) exist "
                      "- very likely invoked via dynamic dispatch")
        elif sid in dispatch_live:
            confidence = "medium"
            reason = ("reachable only if a framework dispatches methods dynamically "
                      "(live class, no resolved call)")
        elif fuzzy_hits:
            confidence = "medium"
            reason = (f"unreachable from any root, but {fuzzy_hits} attribute-name match(es) "
                      "exist - dynamic dispatch could invoke it")
        elif s["kind"] in {"method", "async_method"}:
            confidence = "medium"
            reason = "unreachable method with no attribute-name match anywhere; inheritance or metaclass dispatch not modelled"
        elif inbound:
            # referenced ONLY by other unreachable symbols - the mutually-dead cluster the
            # name-counting predecessor could not see at all
            confidence = "high"
            reason = f"referenced only by {inbound} other unreachable symbol(s) - a dead cluster"
        else:
            confidence = "high"
            reason = "no resolved reference and unreachable from every root"
        candidates.append({
            "path": s["path"], "name": s["name"], "qualname": s["qualname"], "kind": s["kind"],
            "line_start": s["line_start"], "line_end": s["line_end"],
            "confidence": confidence, "decorators": s["decorators"],
            "inbound_resolved": inbound, "fuzzy_attr_matches": fuzzy_hits,
            "reason": reason,
        })

    _order = {"high": 0, "medium": 1, "low": 2}
    candidates.sort(key=lambda r: (_order.get(r["confidence"], 3), r["path"], r["line_start"]))
    return {
        "tool": "dead_code",
        "root": root.as_posix(),
        "resolved": True,
        "file_count": graph["file_count"],
        "symbol_count": len(symbols),
        "candidate_count": len(candidates),
        "candidates": candidates[:limit],
        "skipped": skipped,
        "parse_errors": graph["parse_errors"],
        "honesty": {
            "unresolved": graph["unresolved"],
            "note": ("'unreachable' is proven over RESOLVED edges only. The unresolved ledger "
                     "(dynamic dispatch, star imports) bounds that proof - a large ledger means "
                     "weaker candidates. Fuzzy attribute matches already cap confidence at medium."),
        },
        "truncated": graph["file_count"] >= max_files or len(candidates) > limit,
        "warnings": [
            "Signals, not verdicts: reachability is static. Reflection, plugins registered by "
            "string, and torn-off entrypoints can still invoke 'unreachable' code. Verify "
            "before deleting.",
        ],
        "summary": {
            "files": graph["file_count"],
            "symbols": len(symbols),
            "roots": len(roots),
            "live_strict": len(strict_live),
            "live_with_dispatch": len(dispatch_live),
            "candidates": len(candidates),
            "returned": min(len(candidates), limit),
            "parse_errors": len(graph["parse_errors"]),
        },
    }
