"""
FILE:       tools/snapshot_verify/cli.py
ROLE:       ProjectMapper snapshot verifier.
DOMAIN:     tool
DOES:       Verifies a ProjectMapper SQLite snapshot, sidecar sha256, manifest JSON, schema
            tables, and metadata/row-count consistency.
DEPENDS ON: tools._toolkit, (stdlib) hashlib, json, sqlite3, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      REHOME/PATTERN from ProjectMapper manifest + sha256 cartridge.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from tools._toolkit import tool_main

REQUIRED_TABLES = {"snapshot_metadata", "snapshot_manifest", "project_tree", "project_files",
                   "snapshot_skipped_paths", "snapshot_errors"}


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


@tool_main
def run(args: dict) -> dict:
    workspace = Path.cwd().resolve()
    db = (workspace / str(args.get("db") or args.get("snapshot") or "")).resolve()
    if not db.is_file():
        return {"ok": False, "error": f"snapshot db not found: {db}"}
    if not _inside(workspace, db):
        return {"ok": False, "error": "snapshot must stay inside the workspace"}

    actual_sha = hashlib.sha256(db.read_bytes()).hexdigest()
    sha_path = Path(str(args.get("sha256") or (str(db) + ".sha256"))).resolve()
    manifest_path = Path(str(args.get("manifest") or (str(db.with_suffix("")) + ".manifest.json"))).resolve()
    checks = []

    checks.append({"name": "sqlite_exists", "ok": True, "detail": db.as_posix()})
    if sha_path.exists():
        text = sha_path.read_text(encoding="utf-8", errors="replace").strip()
        checks.append({"name": "sha256_sidecar", "ok": actual_sha in text,
                       "detail": sha_path.as_posix(), "actual_sha256": actual_sha})
    else:
        checks.append({"name": "sha256_sidecar", "ok": False, "detail": "missing"})

    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            checks.append({"name": "manifest_json", "ok": True, "detail": manifest_path.as_posix()})
            checks.append({"name": "manifest_artifact_sha256",
                           "ok": ((manifest.get("integrity") or {}).get("artifact_sha256") == actual_sha),
                           "detail": "integrity.artifact_sha256"})
        except json.JSONDecodeError as exc:
            checks.append({"name": "manifest_json", "ok": False, "detail": str(exc)})
    else:
        checks.append({"name": "manifest_json", "ok": False, "detail": "missing"})

    with sqlite3.connect(str(db)) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        checks.append({"name": "required_tables", "ok": REQUIRED_TABLES.issubset(tables),
                       "missing": sorted(REQUIRED_TABLES - tables)})
        meta = dict(conn.execute("SELECT key, value FROM snapshot_metadata").fetchall()
                    if "snapshot_metadata" in tables else [])
        tree_count = conn.execute("SELECT COUNT(*) FROM project_tree").fetchone()[0] if "project_tree" in tables else 0
        file_count = conn.execute("SELECT COUNT(*) FROM project_files").fetchone()[0] if "project_files" in tables else 0
        skipped_count = conn.execute("SELECT COUNT(*) FROM snapshot_skipped_paths").fetchone()[0] if "snapshot_skipped_paths" in tables else 0
        if meta:
            checks.append({"name": "metadata_text_file_count", "ok": str(file_count) == str(meta.get("text_file_count")),
                           "detail": meta.get("text_file_count")})
            checks.append({"name": "metadata_skipped_count", "ok": str(skipped_count) == str(meta.get("skipped_count")),
                           "detail": meta.get("skipped_count")})

    ok = all(c["ok"] for c in checks)
    return {"ok": ok, "tool": "snapshot_verify", "db": db.as_posix(), "checks": checks,
            "artifact_sha256": actual_sha,
            "summary": {"checks": len(checks), "failed": sum(1 for c in checks if not c["ok"]),
                        "tree_rows": tree_count, "file_rows": file_count, "skipped_rows": skipped_count}}

