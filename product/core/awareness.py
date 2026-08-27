from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import storage, substrate
from .instance import InstanceContext


class AwarenessError(RuntimeError):
    pass


TABLES = ("awareness_revisions", "awareness_items")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _awareness_id() -> str:
    return f"awareness:{uuid.uuid4().hex}"


def _item_id() -> str:
    return f"awareness-item:{uuid.uuid4().hex}"


def _json(document: Any) -> str:
    return json.dumps(document, sort_keys=True)


def _decode_revision(row: sqlite3.Row) -> dict:
    revision = {key: row[key] for key in row.keys()}
    revision["summary"] = json.loads(revision.pop("summary_json"))
    revision["limitations"] = json.loads(revision.pop("limitations_json"))
    revision["unknowns"] = json.loads(revision.pop("unknowns_json"))
    revision["source_handles"] = json.loads(revision.pop("source_handles_json"))
    revision["basis"] = {
        "status": revision.pop("basis_status"),
        "signature": revision.pop("basis_signature"),
    }
    revision["freshness"] = "unknown"
    revision["findings"] = []
    return revision


def _decode_item(row: sqlite3.Row) -> dict:
    item = {key: row[key] for key in row.keys()}
    item["source_handles"] = json.loads(item.pop("source_handles_json"))
    item["provenance"] = json.loads(item.pop("provenance_json"))
    return item


def _inside_or_equal(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _target_signature(context: InstanceContext) -> str:
    digest = hashlib.sha256()
    excluded = context.instance_root.resolve()
    for current, directory_names, file_names in os.walk(context.target_root):
        here = Path(current)
        directory_names[:] = [
            name
            for name in sorted(directory_names)
            if not _inside_or_equal((here / name).resolve(strict=False), excluded)
        ]
        for name in directory_names:
            path = here / name
            stat = path.lstat()
            digest.update(f"D\0{path.relative_to(context.target_root).as_posix()}\0{stat.st_mtime_ns}".encode("utf-8"))
            digest.update(b"\0")
        for name in sorted(file_names):
            path = here / name
            if _inside_or_equal(path.resolve(strict=False), excluded):
                continue
            stat = path.lstat()
            digest.update(f"F\0{path.relative_to(context.target_root).as_posix()}\0{stat.st_size}\0{stat.st_mtime_ns}".encode("utf-8"))
            digest.update(b"\0")
            if path.is_file() and not path.is_symlink():
                digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _basis_signature(status: dict, resources: list[dict], claims: list[dict]) -> str:
    payload = {
        "counts": status["counts"],
        "resources": [
            {
                "handle": item["handle"],
                "latest_version_id": item.get("latest_version_id"),
            }
            for item in resources
        ],
        "claims": [
            {
                "claim_id": item["claim_id"],
                "claim_type": item["claim_type"],
                "statement": item["statement"],
            }
            for item in claims
        ],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _freshness(revision: dict, context: InstanceContext) -> str:
    stored = revision.get("target_signature")
    if not stored:
        return "unknown"
    current = _target_signature(context)
    return "current" if current == stored else "stale"


def status(context: InstanceContext) -> dict:
    connection = storage.connect(context)
    try:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in TABLES
        }
    finally:
        connection.close()
    return {"ok": True, "counts": counts}


def refresh(context: InstanceContext) -> dict:
    created_at = _now()
    substrate_status = substrate.status(context)
    resources = substrate.list_resources(context, 100)
    claims = substrate.list_claims(context, 100)
    basis_missing = (
        substrate_status["counts"]["resources"] == 0
        and substrate_status["counts"]["observations"] == 0
        and substrate_status["counts"]["claims"] == 0
    )
    target_signature = _target_signature(context)

    if basis_missing:
        basis_status = "missing"
        basis = None
        source_handles: list[str] = []
        summary = {
            "target_state": "unknown_unobserved",
            "resource_count": None,
            "claim_count": 0,
        }
        findings: list[dict] = []
        limitations = ["no substrate observations exist; awareness basis is unknown"]
        unknowns = ["target content has not been observed by substrate; unobserved remains unknown"]
    else:
        basis_status = "observed"
        basis = _basis_signature(substrate_status, resources, claims)
        resource_handles = [item["handle"] for item in resources]
        claim_handles = [item["claim_id"] for item in claims]
        source_handles = [*resource_handles[:25], *claim_handles[:25]]
        empty_claim = next((item for item in claims if item["claim_type"] == "target_empty"), None)
        target_state = "observed_empty" if empty_claim else "observed_non_empty"
        summary = {
            "target_state": target_state,
            "resource_count": len(resources),
            "claim_count": len(claims),
        }
        limitations = []
        unknowns = ["anything not represented in substrate observations remains unknown"]
        findings = _findings_from_substrate(resources, claims)

    awareness_id = _awareness_id()
    revision = {
        "awareness_id": awareness_id,
        "created_at": created_at,
        "basis": {"status": basis_status, "signature": basis},
        "target_signature": target_signature if basis else None,
        "freshness": "current" if basis else "unknown",
        "summary": summary,
        "limitations": limitations,
        "unknowns": unknowns,
        "source_handles": source_handles,
        "findings": findings,
    }

    connection = storage.connect(context)
    try:
        with connection:
            connection.execute(
                """
                INSERT INTO awareness_revisions
                    (awareness_id, created_at, basis_status, basis_signature,
                     target_signature, summary_json, limitations_json, unknowns_json,
                     source_handles_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    awareness_id,
                    created_at,
                    basis_status,
                    basis,
                    target_signature if basis else None,
                    _json(summary),
                    _json(limitations),
                    _json(unknowns),
                    _json(source_handles),
                ),
            )
            for item in findings:
                connection.execute(
                    """
                    INSERT INTO awareness_items
                        (item_id, awareness_id, item_type, title, statement, priority,
                         source_handles_json, provenance_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["item_id"],
                        awareness_id,
                        item["item_type"],
                        item["title"],
                        item["statement"],
                        item["priority"],
                        _json(item["source_handles"]),
                        _json(item["provenance"]),
                    ),
                )
    finally:
        connection.close()
    return {"ok": True, "revision": revision}


def current(context: InstanceContext) -> dict:
    connection = storage.connect(context)
    try:
        row = connection.execute(
            """
            SELECT awareness_id, created_at, basis_status, basis_signature,
                   target_signature, summary_json, limitations_json, unknowns_json,
                   source_handles_json
            FROM awareness_revisions
            ORDER BY rowid DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise AwarenessError("no awareness revision exists")
    revision = _read_revision_row(context, row)
    return {"ok": True, "revision": revision}


def list_revisions(context: InstanceContext, limit: int = 50) -> list[dict]:
    connection = storage.connect(context)
    try:
        rows = connection.execute(
            """
            SELECT awareness_id, created_at, basis_status, basis_signature,
                   target_signature, summary_json, limitations_json, unknowns_json,
                   source_handles_json
            FROM awareness_revisions
            ORDER BY rowid DESC
            LIMIT ?
            """,
            (_bounded_limit(limit),),
        ).fetchall()
    finally:
        connection.close()
    return [_read_revision_row(context, row, include_findings=False) for row in rows]


def read_revision(context: InstanceContext, awareness_id: str) -> dict:
    connection = storage.connect(context)
    try:
        row = connection.execute(
            """
            SELECT awareness_id, created_at, basis_status, basis_signature,
                   target_signature, summary_json, limitations_json, unknowns_json,
                   source_handles_json
            FROM awareness_revisions
            WHERE awareness_id = ?
            """,
            (awareness_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise AwarenessError(f"awareness revision not found: {awareness_id}")
    return _read_revision_row(context, row)


def drill(context: InstanceContext, item_id: str) -> dict:
    connection = storage.connect(context)
    try:
        row = connection.execute(
            """
            SELECT item_id, awareness_id, item_type, title, statement, priority,
                   source_handles_json, provenance_json
            FROM awareness_items
            WHERE item_id = ?
            """,
            (item_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise AwarenessError(f"awareness item not found: {item_id}")

    item = _decode_item(row)
    nodes: dict[str, dict] = {}
    relations: list[dict] = []
    for handle in item["source_handles"]:
        if handle.startswith("claim:"):
            trace = substrate.trace(context, handle)
            for node in trace["nodes"]:
                nodes[node["id"]] = node
            relations.extend(trace["relations"])
        elif handle.startswith("path:"):
            resource = substrate.read_resource(context, handle)
            nodes[resource["resource_id"]] = {
                "id": resource["resource_id"],
                "type": "resource",
                "handle": resource["handle"],
                "path": resource["path"],
                "kind": resource["kind"],
            }
        elif handle.startswith("evidence:"):
            evidence = substrate.read_evidence(context, handle)
            nodes[evidence["evidence_id"]] = {
                "id": evidence["evidence_id"],
                "type": "evidence",
                "kind": evidence["kind"],
                "digest": evidence["digest"],
            }
    return {"item": item, "nodes": list(nodes.values()), "relations": relations}


def _read_revision_row(
    context: InstanceContext,
    row: sqlite3.Row,
    *,
    include_findings: bool = True,
) -> dict:
    revision = _decode_revision(row)
    revision["freshness"] = _freshness(revision, context)
    if include_findings:
        connection = storage.connect(context)
        try:
            rows = connection.execute(
                """
                SELECT item_id, awareness_id, item_type, title, statement, priority,
                       source_handles_json, provenance_json
                FROM awareness_items
                WHERE awareness_id = ?
                ORDER BY rowid
                """,
                (revision["awareness_id"],),
            ).fetchall()
        finally:
            connection.close()
        revision["findings"] = [_decode_item(item) for item in rows]
    return revision


def _findings_from_substrate(resources: list[dict], claims: list[dict]) -> list[dict]:
    findings: list[dict] = []
    for claim in claims[:10]:
        source_handles = [claim["claim_id"]]
        findings.append(
            {
                "item_id": _item_id(),
                "item_type": "derived_claim",
                "title": claim["claim_type"],
                "statement": claim["statement"],
                "priority": 10,
                "source_handles": source_handles,
                "provenance": {"source": "substrate.claim", "handles": source_handles},
            }
        )
    if resources:
        handles = [item["handle"] for item in resources[:20]]
        findings.append(
            {
                "item_id": _item_id(),
                "item_type": "resource_orientation",
                "title": "observed_resources",
                "statement": f"{len(resources)} target resources are present in the substrate",
                "priority": 20,
                "source_handles": handles,
                "provenance": {"source": "substrate.resources", "handles": handles},
            }
        )
    return findings


def _bounded_limit(limit: int) -> int:
    return max(1, min(int(limit), 500))
