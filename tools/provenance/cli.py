"""
FILE:       tools/provenance/cli.py
ROLE:       Formation provenance surface - record why things exist, then TRACE an artifact back.
DOMAIN:     tool
DOES:       action=note: record one typed relation (subject -relation-> object) with an ORIGIN.
            action=activity: record a multi-participant event (requested_by/used/generated/...).
            action=trace: the payoff - walk backward from an artifact to the chain that formed it.
            action=list|show: inspect edges / an entity's neighborhood.
DEPENDS ON: tools._toolkit (state_root), tools.provenance_shared
WIRES TO:   invoked by src/core/invoke.py. Ledger at <state_root>/provenance.sqlite3; a distinct
            truth class, separate from journal/evidence/operations. Activities carry an op_id
            linking to the operation ledger (E4).
NOTES:      Every relation MUST declare its origin (discovered | operational | interpretive) - that
            closed contract is the point: the system never confuses what it FOUND with what it
            CREATED with what a model GUESSED. The relation vocabulary itself is open (a compact
            recommended set is suggested, unknown relations warn but are allowed).
"""
from __future__ import annotations

from tools import provenance_shared as pv
from tools._toolkit import state_root, tool_main

_DB = "provenance.sqlite3"


def _conn():
    return pv.open_db(state_root() / _DB)


def _entity_arg(args: dict, key: str):
    """An entity given as {kind,ref,label} under `key`, or split kind_/ref_ fields."""
    if isinstance(args.get(key), dict):
        return args[key]
    return {"kind": args.get(f"{key}_kind"), "ref": args.get(f"{key}_ref"),
            "label": args.get(f"{key}_label")}


@tool_main
def run(args: dict) -> dict:
    action = str(args.get("action") or "list").lower()
    conn = _conn()
    try:
        if action == "note":
            r = pv.add_edge(conn, _entity_arg(args, "subject"), str(args.get("relation") or ""),
                            _entity_arg(args, "object"), str(args.get("origin") or ""),
                            op_id=str(args.get("op_id") or ""), note=str(args.get("note") or ""))
            return r if not r.get("ok") else {"tool": "provenance", "action": "note", **r}

        if action == "activity":
            parts = args.get("participants")
            if not isinstance(parts, list):
                return {"ok": False, "error": "participants must be a list of {role, kind, ref, label}"}
            r = pv.add_activity(conn, str(args.get("verb") or ""), parts,
                                str(args.get("origin") or ""), op_id=str(args.get("op_id") or ""),
                                note=str(args.get("note") or ""))
            return r if not r.get("ok") else {"tool": "provenance", "action": "activity", **r}

        if action == "trace":
            kind = str(args.get("kind") or "")
            ref = str(args.get("ref") or "")
            if not ref:
                return {"ok": False, "error": "kind + ref identify the artifact to trace"}
            r = pv.trace(conn, kind or "thing", ref, int(args.get("max_depth", 6)))
            return r if not r.get("ok") else {"tool": "provenance", "action": "trace", **r}

        if action == "show":
            kind = str(args.get("kind") or "")
            ref = str(args.get("ref") or "")
            if not ref:
                return {"ok": False, "error": "kind + ref identify the entity"}
            got = pv.show_entity(conn, kind or "thing", ref)
            if not got:
                return {"ok": False, "error": f"no such entity {kind}:{ref}"}
            return {"tool": "provenance", "action": "show", **got}

        if action == "list":
            rows = pv.list_edges(conn, args.get("origin"), int(args.get("limit", 50)))
            return {"tool": "provenance", "action": "list", "count": len(rows), "edges": rows}

        return {"ok": False, "error": f"unknown action {action!r}; "
                "use note|activity|trace|list|show"}
    finally:
        conn.close()
