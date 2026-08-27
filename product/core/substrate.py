from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import storage
from .instance import InstanceContext


class SubstrateError(RuntimeError):
    pass


TABLES = (
    "resources",
    "resource_versions",
    "observations",
    "epistemic_evidence",
    "claims",
    "relations",
)

_TEXT_SUFFIXES = {
    ".cfg",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".rst",
    ".toml",
    ".tsv",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json_bytes(document: dict) -> bytes:
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _evidence_id(digest: str) -> str:
    return f"evidence:{digest}"


def _uuid_handle(prefix: str) -> str:
    return f"{prefix}:{uuid.uuid4().hex}"


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def _decode(row: sqlite3.Row, field: str = "data_json") -> dict:
    document = _row_to_dict(row)
    document[field.replace("_json", "")] = json.loads(document.pop(field))
    return document


def _resource_handle(relative: str, kind: str) -> str:
    if relative == ".":
        return "path:."
    suffix = "/" if kind == "directory" and not relative.endswith("/") else ""
    return f"path:{relative}{suffix}"


def _resource_id(handle: str) -> str:
    return handle


def _version_id(handle: str, evidence_id: str, mtime_ns: int | None) -> str:
    digest = hashlib.sha256(f"{handle}\0{evidence_id}\0{mtime_ns}".encode("utf-8")).hexdigest()
    return f"version:{digest[:32]}"


def _is_text_like(path: str) -> bool:
    return Path(path).suffix.lower() in _TEXT_SUFFIXES


def _insert_evidence(
    connection: sqlite3.Connection,
    *,
    kind: str,
    body: dict,
    created_at: str,
) -> str:
    payload = _json_bytes(body)
    digest = hashlib.sha256(payload).hexdigest()
    evidence_id = _evidence_id(digest)
    connection.execute(
        """
        INSERT OR IGNORE INTO epistemic_evidence
            (evidence_id, digest, created_at, kind, media_type, body_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (evidence_id, digest, created_at, kind, "application/json", payload.decode("utf-8")),
    )
    return evidence_id


def _insert_relation(
    connection: sqlite3.Connection,
    *,
    subject_type: str,
    subject_id: str,
    predicate: str,
    object_type: str,
    object_id: str,
    created_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO relations
            (created_at, subject_type, subject_id, predicate, object_type, object_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (created_at, subject_type, subject_id, predicate, object_type, object_id),
    )


def _resource_records(context: InstanceContext) -> list[dict]:
    records: list[dict] = []
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
            kind = "symlink" if path.is_symlink() else "directory"
            records.append(_describe_resource(context, path, kind))
        for name in sorted(file_names):
            path = here / name
            if _inside_or_equal(path.resolve(strict=False), excluded):
                continue
            kind = "symlink" if path.is_symlink() else "file"
            records.append(_describe_resource(context, path, kind))
    return records


def _inside_or_equal(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _describe_resource(context: InstanceContext, path: Path, kind: str) -> dict:
    relative = path.relative_to(context.target_root).as_posix()
    stat = path.lstat()
    content_hash = None
    if kind == "file":
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "handle": _resource_handle(relative, kind),
        "path": relative,
        "kind": kind,
        "size_bytes": stat.st_size if kind == "file" else None,
        "mtime_ns": stat.st_mtime_ns,
        "content_hash": content_hash,
        "text_like": kind == "file" and _is_text_like(relative),
    }


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
    observed_at = _now()
    records = _resource_records(context)
    connection = storage.connect(context)
    try:
        with connection:
            inventory_evidence = _insert_evidence(
                connection,
                kind="resource_inventory",
                body={
                    "producer": "substrate.resource_inventory",
                    "target": "path:.",
                    "resource_count": len(records),
                    "handles": [record["handle"] for record in records],
                    "limitations": [],
                },
                created_at=observed_at,
            )
            inventory_observation = _uuid_handle("observation")
            connection.execute(
                """
                INSERT INTO observations
                    (observation_id, producer, observed_at, subject_handle,
                     observation_type, data_json, evidence_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inventory_observation,
                    "substrate.resource_inventory",
                    observed_at,
                    "path:.",
                    "resource_inventory",
                    json.dumps(
                        {
                            "resource_count": len(records),
                            "limitations": [],
                            "unknown": "anything not observed by this refresh remains unknown",
                        },
                        sort_keys=True,
                    ),
                    inventory_evidence,
                ),
            )
            _insert_relation(
                connection,
                subject_type="observation",
                subject_id=inventory_observation,
                predicate="supported_by",
                object_type="evidence",
                object_id=inventory_evidence,
                created_at=observed_at,
            )

            text_observations: list[str] = []
            last_digest = None
            for record in records:
                evidence_id = _insert_evidence(
                    connection,
                    kind="resource_version",
                    body={
                        "producer": "substrate.resource_inventory",
                        "observed_at": observed_at,
                        "resource": record,
                    },
                    created_at=observed_at,
                )
                last_digest = record.get("content_hash") or evidence_id.removeprefix("evidence:")
                resource_id = _resource_id(record["handle"])
                version_id = _version_id(record["handle"], evidence_id, record.get("mtime_ns"))
                existing = connection.execute(
                    "SELECT first_seen_at FROM resources WHERE resource_id = ?",
                    (resource_id,),
                ).fetchone()
                first_seen = existing["first_seen_at"] if existing else observed_at
                connection.execute(
                    """
                    INSERT INTO resources
                        (resource_id, handle, path, kind, first_seen_at, last_seen_at,
                         latest_version_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(resource_id) DO UPDATE SET
                        kind = excluded.kind,
                        last_seen_at = excluded.last_seen_at,
                        latest_version_id = excluded.latest_version_id
                    """,
                    (
                        resource_id,
                        record["handle"],
                        record["path"],
                        record["kind"],
                        first_seen,
                        observed_at,
                        version_id,
                    ),
                )
                connection.execute(
                    """
                    INSERT OR IGNORE INTO resource_versions
                        (version_id, resource_id, observed_at, kind, content_hash,
                         size_bytes, mtime_ns, evidence_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        version_id,
                        resource_id,
                        observed_at,
                        record["kind"],
                        record.get("content_hash"),
                        record.get("size_bytes"),
                        record.get("mtime_ns"),
                        evidence_id,
                    ),
                )
                _insert_relation(
                    connection,
                    subject_type="version",
                    subject_id=version_id,
                    predicate="version_of",
                    object_type="resource",
                    object_id=resource_id,
                    created_at=observed_at,
                )
                _insert_relation(
                    connection,
                    subject_type="version",
                    subject_id=version_id,
                    predicate="supported_by",
                    object_type="evidence",
                    object_id=evidence_id,
                    created_at=observed_at,
                )
                observation_id = _uuid_handle("observation")
                observation_type = "file_hash" if record["kind"] == "file" else "resource_seen"
                connection.execute(
                    """
                    INSERT INTO observations
                        (observation_id, producer, observed_at, subject_handle,
                         observation_type, data_json, evidence_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        observation_id,
                        "substrate.resource_inventory",
                        observed_at,
                        record["handle"],
                        observation_type,
                        json.dumps(record, sort_keys=True),
                        evidence_id,
                    ),
                )
                _insert_relation(
                    connection,
                    subject_type="observation",
                    subject_id=observation_id,
                    predicate="concerns",
                    object_type="resource",
                    object_id=resource_id,
                    created_at=observed_at,
                )
                _insert_relation(
                    connection,
                    subject_type="observation",
                    subject_id=observation_id,
                    predicate="supported_by",
                    object_type="evidence",
                    object_id=evidence_id,
                    created_at=observed_at,
                )
                if record["text_like"]:
                    text_observations.append(observation_id)

            claim_count = 0
            if not records:
                claim_id = _uuid_handle("claim")
                connection.execute(
                    """
                    INSERT INTO claims
                        (claim_id, created_at, claim_type, statement, derivation_method,
                         confidence, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        claim_id,
                        observed_at,
                        "target_empty",
                        "target observed empty during explicit substrate refresh",
                        "deterministic.resource_count",
                        1.0,
                        json.dumps({"resource_count": 0}, sort_keys=True),
                    ),
                )
                _insert_relation(
                    connection,
                    subject_type="claim",
                    subject_id=claim_id,
                    predicate="derived_from",
                    object_type="observation",
                    object_id=inventory_observation,
                    created_at=observed_at,
                )
                _insert_relation(
                    connection,
                    subject_type="claim",
                    subject_id=claim_id,
                    predicate="supported_by",
                    object_type="evidence",
                    object_id=inventory_evidence,
                    created_at=observed_at,
                )
                claim_count = 1
            elif text_observations:
                claim_id = _uuid_handle("claim")
                connection.execute(
                    """
                    INSERT INTO claims
                        (claim_id, created_at, claim_type, statement, derivation_method,
                         confidence, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        claim_id,
                        observed_at,
                        "target_has_text_files",
                        "target contains text-like files observed by deterministic refresh",
                        "deterministic.suffix_classification",
                        0.8,
                        json.dumps({"text_like_file_count": len(text_observations)}, sort_keys=True),
                    ),
                )
                for observation_id in text_observations:
                    _insert_relation(
                        connection,
                        subject_type="claim",
                        subject_id=claim_id,
                        predicate="derived_from",
                        object_type="observation",
                        object_id=observation_id,
                        created_at=observed_at,
                    )
                if text_observations:
                    first_observation = connection.execute(
                        "SELECT evidence_id, subject_handle FROM observations WHERE observation_id = ?",
                        (text_observations[0],),
                    ).fetchone()
                    if first_observation is not None:
                        _insert_relation(
                            connection,
                            subject_type="claim",
                            subject_id=claim_id,
                            predicate="supported_by",
                            object_type="evidence",
                            object_id=first_observation["evidence_id"],
                            created_at=observed_at,
                        )
                claim_count = 1
    finally:
        connection.close()
    return {
        "ok": True,
        "observed": {
            "resource_count": len(records),
            "observation_count": len(records) + 1,
            "claim_count": claim_count,
            "digest": last_digest,
            "limitations": [],
            "unknown": "anything not observed by this refresh remains unknown",
        },
    }


def list_resources(context: InstanceContext, limit: int = 100) -> list[dict]:
    connection = storage.connect(context)
    try:
        rows = connection.execute(
            """
            SELECT resource_id, handle, path, kind, first_seen_at, last_seen_at,
                   latest_version_id
            FROM resources
            ORDER BY path
            LIMIT ?
            """,
            (_bounded_limit(limit),),
        ).fetchall()
    finally:
        connection.close()
    return [_row_to_dict(row) for row in rows]


def read_resource(context: InstanceContext, handle: str) -> dict:
    connection = storage.connect(context)
    try:
        row = connection.execute(
            """
            SELECT resource_id, handle, path, kind, first_seen_at, last_seen_at,
                   latest_version_id
            FROM resources
            WHERE resource_id = ? OR handle = ?
            """,
            (handle, handle),
        ).fetchone()
        if row is None:
            raise SubstrateError(f"resource not found: {handle}")
        resource = _row_to_dict(row)
        if resource["latest_version_id"]:
            version = connection.execute(
                """
                SELECT version_id, resource_id, observed_at, kind, content_hash,
                       size_bytes, mtime_ns, evidence_id
                FROM resource_versions
                WHERE version_id = ?
                """,
                (resource["latest_version_id"],),
            ).fetchone()
            resource["latest"] = _row_to_dict(version) if version else None
    finally:
        connection.close()
    return resource


def list_versions(context: InstanceContext, resource_handle: str | None = None) -> list[dict]:
    connection = storage.connect(context)
    try:
        if resource_handle:
            rows = connection.execute(
                """
                SELECT version_id, resource_id, observed_at, kind, content_hash,
                       size_bytes, mtime_ns, evidence_id
                FROM resource_versions
                WHERE resource_id = ?
                ORDER BY rowid
                """,
                (resource_handle,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT version_id, resource_id, observed_at, kind, content_hash,
                       size_bytes, mtime_ns, evidence_id
                FROM resource_versions
                ORDER BY rowid
                LIMIT 100
                """
            ).fetchall()
    finally:
        connection.close()
    return [_row_to_dict(row) for row in rows]


def list_observations(context: InstanceContext, limit: int = 100) -> list[dict]:
    connection = storage.connect(context)
    try:
        rows = connection.execute(
            """
            SELECT observation_id, producer, observed_at, subject_handle, observation_type,
                   data_json, evidence_id
            FROM observations
            ORDER BY rowid
            LIMIT ?
            """,
            (_bounded_limit(limit),),
        ).fetchall()
    finally:
        connection.close()
    return [_decode(row) for row in rows]


def read_evidence(context: InstanceContext, evidence_id: str) -> dict:
    connection = storage.connect(context)
    try:
        row = connection.execute(
            """
            SELECT evidence_id, digest, created_at, kind, media_type, body_json
            FROM epistemic_evidence
            WHERE evidence_id = ?
            """,
            (evidence_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise SubstrateError(f"epistemic evidence not found: {evidence_id}")
    document = _row_to_dict(row)
    document["body"] = json.loads(document.pop("body_json"))
    return document


def list_claims(context: InstanceContext, limit: int = 100) -> list[dict]:
    connection = storage.connect(context)
    try:
        rows = connection.execute(
            """
            SELECT claim_id, created_at, claim_type, statement, derivation_method,
                   confidence, data_json
            FROM claims
            ORDER BY rowid
            LIMIT ?
            """,
            (_bounded_limit(limit),),
        ).fetchall()
    finally:
        connection.close()
    return [_decode(row) for row in rows]


def read_claim(context: InstanceContext, claim_id: str) -> dict:
    connection = storage.connect(context)
    try:
        row = connection.execute(
            """
            SELECT claim_id, created_at, claim_type, statement, derivation_method,
                   confidence, data_json
            FROM claims
            WHERE claim_id = ?
            """,
            (claim_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise SubstrateError(f"claim not found: {claim_id}")
    return _decode(row)


def trace(context: InstanceContext, start_id: str) -> dict:
    connection = storage.connect(context)
    try:
        start = _load_node(connection, start_id)
        nodes: dict[str, dict] = {start_id: start}
        relations: list[dict] = []
        frontier = [start_id]
        seen = {start_id}
        while frontier:
            subject_id = frontier.pop(0)
            rows = connection.execute(
                """
                SELECT relation_id, created_at, subject_type, subject_id, predicate,
                       object_type, object_id
                FROM relations
                WHERE subject_id = ?
                ORDER BY relation_id
                """,
                (subject_id,),
            ).fetchall()
            for row in rows:
                relation = _row_to_dict(row)
                relations.append(relation)
                object_id = relation["object_id"]
                if object_id not in nodes:
                    nodes[object_id] = _load_node(connection, object_id, relation["object_type"])
                if object_id not in seen:
                    seen.add(object_id)
                    frontier.append(object_id)
        return {"start": start, "nodes": list(nodes.values()), "relations": relations}
    finally:
        connection.close()


def _load_node(
    connection: sqlite3.Connection,
    identifier: str,
    kind: str | None = None,
) -> dict[str, Any]:
    if kind is None:
        kind = identifier.split(":", 1)[0]
        if kind == "path":
            kind = "resource"
    table_sql = {
        "resource": (
            "resources",
            "SELECT resource_id AS id, 'resource' AS type, handle, path, kind FROM resources "
            "WHERE resource_id = ? OR handle = ?",
        ),
        "version": (
            "resource_versions",
            "SELECT version_id AS id, 'version' AS type, resource_id, kind, content_hash, "
            "evidence_id FROM resource_versions WHERE version_id = ?",
        ),
        "observation": (
            "observations",
            "SELECT observation_id AS id, 'observation' AS type, observation_type, "
            "subject_handle, evidence_id FROM observations WHERE observation_id = ?",
        ),
        "evidence": (
            "epistemic_evidence",
            "SELECT evidence_id AS id, 'evidence' AS type, kind, digest FROM epistemic_evidence "
            "WHERE evidence_id = ?",
        ),
        "claim": (
            "claims",
            "SELECT claim_id AS id, 'claim' AS type, claim_type, statement FROM claims "
            "WHERE claim_id = ?",
        ),
    }
    if kind not in table_sql:
        raise SubstrateError(f"unsupported trace node type: {kind}")
    _, sql = table_sql[kind]
    parameters: tuple[str, ...] = (identifier, identifier) if kind == "resource" else (identifier,)
    row = connection.execute(sql, parameters).fetchone()
    if row is None:
        raise SubstrateError(f"trace node not found: {identifier}")
    return _row_to_dict(row)


def _bounded_limit(limit: int) -> int:
    return max(1, min(int(limit), 500))
