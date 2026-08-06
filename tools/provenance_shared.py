"""
FILE:       tools/provenance_shared.py
ROLE:       Formation provenance - record WHY an artifact exists, and trace it back to its origin.
DOMAIN:     tool (shared substrate)
DOES:       A SQLite ledger of entities and typed, directed relations between them. Every relation
            carries an explicit ORIGIN (discovered | operational | interpretive) so "found in the
            artifacts" is never confused with "created by our work" or "a model's provisional
            guess". An activity is a first-class entity whose roles (requested_by / used /
            generated / approved_by / validated_by / ...) are edges to its participants, so a
            multi-participant event stays coherent. trace() walks backward from an artifact to the
            chain that formed it.
DEPENDS ON: (stdlib) hashlib, sqlite3, time, uuid, pathlib
WIRES TO:   tools/provenance (the CLI). Separate storage from journal/evidence/operations - a
            distinct truth class. Activities carry an op_id linking to the operation ledger (E4).
NOTES:      ORIGIN is a closed, enforced contract - that is the whole point (discovered vs created
            vs guessed). The RELATION vocabulary is deliberately OPEN (a recommended set is
            documented, but any string is allowed): the review warns against freezing a universal
            ontology before real use exposes what is needed. Pure functions over an explicit db
            path, so the whole graph is testable without a live target. Entity identity is
            content-of-reference based (hash of kind|ref) so recording the same entity twice
            dedupes to one stable node.
"""
from __future__ import annotations

import hashlib
import sqlite3
import time
import uuid
from pathlib import Path

# The closed, enforced contract: where a relation CAME FROM.
ORIGINS = {"discovered", "operational", "interpretive"}

# Recommended (not enforced) relation vocabulary - a compact starting set. Any string is allowed.
RECOMMENDED_RELATIONS = {
    "motivated", "retrieved", "supported", "used", "used_in", "generated", "produced",
    "derived_from", "accepted_by", "approved_by", "requested_by", "executed_by",
    "validated_by", "superseded_by", "refined_from",
}
# Roles/relations that mean "the subject PRODUCED the object" - trace starts from these.
_CREATION = {"generated", "produced", "accepted_by", "refined_from"}
# Roles that point at an activity's INPUTS - trace recurses backward through these.
_INPUT = {"used", "used_in", "derived_from", "supported", "requested_by"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS pv_entities (
  entity_id  TEXT PRIMARY KEY,
  kind       TEXT NOT NULL,
  ref        TEXT NOT NULL,
  label      TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(kind, ref)
);
CREATE TABLE IF NOT EXISTS pv_edges (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  subject_id TEXT NOT NULL,
  relation   TEXT NOT NULL,
  object_id  TEXT NOT NULL,
  origin     TEXT NOT NULL,
  op_id      TEXT,
  note       TEXT,
  created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _eid(kind: str, ref: str) -> str:
    return hashlib.sha256(f"{kind}|{ref}".encode("utf-8")).hexdigest()[:16]


def open_db(path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def ensure_entity(conn, kind: str, ref: str, label: str = "") -> str:
    kind = str(kind or "").strip() or "thing"
    ref = str(ref or "").strip()
    if not ref:
        raise ValueError("entity ref is required")
    eid = _eid(kind, ref)
    row = conn.execute("SELECT entity_id, label FROM pv_entities WHERE entity_id=?", (eid,)).fetchone()
    if row is None:
        conn.execute("INSERT INTO pv_entities(entity_id,kind,ref,label,created_at) VALUES(?,?,?,?,?)",
                     (eid, kind, ref, label, _now()))
    elif label and not row["label"]:
        conn.execute("UPDATE pv_entities SET label=? WHERE entity_id=?", (label, eid))
    return eid


def _norm_entity(spec) -> tuple[str, str, str]:
    """Accept an entity as {kind, ref, label} or 'kind:ref'. Returns (kind, ref, label)."""
    if isinstance(spec, dict):
        return (str(spec.get("kind") or "thing"), str(spec.get("ref") or ""),
                str(spec.get("label") or ""))
    s = str(spec or "")
    if ":" in s:
        k, r = s.split(":", 1)
        return (k.strip() or "thing", r.strip(), "")
    return ("thing", s.strip(), "")


def add_edge(conn, subject, relation: str, obj, origin: str,
             op_id: str = "", note: str = "") -> dict:
    if origin not in ORIGINS:
        return {"ok": False, "error": f"origin must be one of {sorted(ORIGINS)}",
                "hint": "discovered = found in artifacts; operational = created by our work; "
                        "interpretive = a model/heuristic guess, still provisional"}
    relation = str(relation or "").strip()
    if not relation:
        return {"ok": False, "error": "relation is required"}
    sk, sr, sl = _norm_entity(subject)
    ok_, orf, olb = _norm_entity(obj)
    if not sr or not orf:
        return {"ok": False, "error": "subject and object each need a ref"}
    sid = ensure_entity(conn, sk, sr, sl)
    oid = ensure_entity(conn, ok_, orf, olb)
    conn.execute("INSERT INTO pv_edges(subject_id,relation,object_id,origin,op_id,note,created_at) "
                 "VALUES(?,?,?,?,?,?,?)", (sid, relation, oid, origin, op_id, note, _now()))
    conn.commit()
    warn = None if relation in RECOMMENDED_RELATIONS else \
        f"'{relation}' is outside the recommended set (allowed, but keep the vocabulary compact)"
    return {"ok": True, "subject_id": sid, "relation": relation, "object_id": oid,
            "origin": origin, "warning": warn}


def add_activity(conn, verb: str, participants: list, origin: str,
                 op_id: str = "", note: str = "") -> dict:
    """Record a multi-participant event as a first-class activity entity plus one edge per role.
    participants: [{role, kind, ref, label}]. The activity IS an entity (kind='activity'), so
    trace treats it uniformly - it produced the `generated` participants FROM the `used` ones."""
    if origin not in ORIGINS:
        return {"ok": False, "error": f"origin must be one of {sorted(ORIGINS)}"}
    verb = str(verb or "").strip() or "activity"
    if not participants:
        return {"ok": False, "error": "an activity needs at least one participant"}
    act_ref = f"{verb}:{uuid.uuid4().hex[:12]}"
    act_id = ensure_entity(conn, "activity", act_ref, verb)
    edges = []
    for p in participants:
        role = str((p or {}).get("role") or "").strip()
        if not role:
            return {"ok": False, "error": "each participant needs a role"}
        pk, pr, pl = _norm_entity(p)
        if not pr:
            return {"ok": False, "error": f"participant with role {role!r} needs a ref"}
        pid = ensure_entity(conn, pk, pr, pl)
        conn.execute("INSERT INTO pv_edges(subject_id,relation,object_id,origin,op_id,note,created_at) "
                     "VALUES(?,?,?,?,?,?,?)", (act_id, role, pid, origin, op_id, note, _now()))
        edges.append({"role": role, "entity_id": pid, "ref": pr})
    conn.commit()
    return {"ok": True, "activity_id": act_id, "verb": verb, "op_id": op_id,
            "participants": edges}


def _entity_by_ref(conn, kind: str, ref: str):
    return conn.execute("SELECT * FROM pv_entities WHERE entity_id=?",
                        (_eid(kind, ref),)).fetchone()


def trace(conn, kind: str, ref: str, max_depth: int = 6) -> dict:
    """Backward formation chain: from an entity, walk to whatever PRODUCED it and, transitively,
    to the inputs and decisions behind that. This is the 'why does this exist?' answer."""
    start = _entity_by_ref(conn, kind, ref)
    if start is None:
        return {"ok": False, "error": f"no such entity {kind}:{ref}"}
    chain: list[dict] = []
    seen: set[str] = set()
    frontier = [(start["entity_id"], 0)]
    while frontier:
        eid, depth = frontier.pop(0)
        if eid in seen or depth >= max_depth:
            continue
        seen.add(eid)
        # incoming edges: someone did something that resulted in THIS entity
        rows = conn.execute(
            "SELECT e.*, s.kind AS s_kind, s.ref AS s_ref, s.label AS s_label "
            "FROM pv_edges e JOIN pv_entities s ON e.subject_id=s.entity_id "
            "WHERE e.object_id=? ORDER BY e.id", (eid,)).fetchall()
        for r in rows:
            chain.append({"depth": depth, "object_id": eid,
                          "subject": {"kind": r["s_kind"], "ref": r["s_ref"], "label": r["s_label"]},
                          "relation": r["relation"], "origin": r["origin"], "op_id": r["op_id"]})
            subj = r["subject_id"]
            frontier.append((subj, depth + 1))
            # If the producer is an activity, expose ALL its participants (approvals and
            # validations are part of WHY the thing exists, not just its inputs) but only recurse
            # backward on the INPUT roles - an approval or a validation is a leaf, not a source.
            if r["s_kind"] == "activity":
                parts = conn.execute(
                    "SELECT e.object_id, e.relation, t.kind, t.ref, t.label FROM pv_edges e "
                    "JOIN pv_entities t ON e.object_id=t.entity_id WHERE e.subject_id=?",
                    (subj,)).fetchall()
                for inp in parts:
                    if inp["object_id"] == eid:
                        continue  # the `generated` edge back to the entity we are tracing
                    chain.append({"depth": depth + 1, "object_id": subj,
                                  "subject": {"kind": inp["kind"], "ref": inp["ref"],
                                              "label": inp["label"]},
                                  "relation": inp["relation"], "origin": None,
                                  "op_id": r["op_id"], "activity_participant": True})
                    if inp["relation"] in _INPUT:
                        frontier.append((inp["object_id"], depth + 2))
    origins_seen = sorted({c["origin"] for c in chain if c["origin"]})
    return {"ok": True, "entity": {"kind": start["kind"], "ref": start["ref"],
                                   "label": start["label"]},
            "chain": chain, "steps": len(chain), "origins": origins_seen}


def show_entity(conn, kind: str, ref: str) -> dict:
    ent = _entity_by_ref(conn, kind, ref)
    if ent is None:
        return {}
    eid = ent["entity_id"]
    incoming = conn.execute(
        "SELECT e.relation,e.origin,e.op_id,s.kind,s.ref FROM pv_edges e "
        "JOIN pv_entities s ON e.subject_id=s.entity_id WHERE e.object_id=? ORDER BY e.id",
        (eid,)).fetchall()
    outgoing = conn.execute(
        "SELECT e.relation,e.origin,e.op_id,o.kind,o.ref FROM pv_edges e "
        "JOIN pv_entities o ON e.object_id=o.entity_id WHERE e.subject_id=? ORDER BY e.id",
        (eid,)).fetchall()
    return {"entity": dict(ent),
            "incoming": [dict(r) for r in incoming],
            "outgoing": [dict(r) for r in outgoing]}


def list_edges(conn, origin: str | None = None, limit: int = 50) -> list[dict]:
    q = ("SELECT e.relation,e.origin,e.op_id,e.created_at,s.kind AS s_kind,s.ref AS s_ref,"
         "o.kind AS o_kind,o.ref AS o_ref FROM pv_edges e "
         "JOIN pv_entities s ON e.subject_id=s.entity_id "
         "JOIN pv_entities o ON e.object_id=o.entity_id ")
    if origin:
        rows = conn.execute(q + "WHERE e.origin=? ORDER BY e.id DESC LIMIT ?",
                            (origin, limit)).fetchall()
    else:
        rows = conn.execute(q + "ORDER BY e.id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
