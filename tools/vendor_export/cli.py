"""
FILE:       tools/vendor_export/cli.py
ROLE:       Dry-run-first clean workspace exporter.
DOMAIN:     tool
DOES:       Plans or creates a clean export folder/zip for selected project files, excluding
            donor bins, git/runtime artifacts, caches, and local databases by default.
DEPENDS ON: tools._toolkit, (stdlib) hashlib, os, shutil, zipfile, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      REHOME/PATTERN from ProjectMapper vendor export; adapted to suite root.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from tools._toolkit import suite_home, tool_main

EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "_artifacts", ".pytest_cache",
                ".mypy_cache", ".ruff_cache", "node_modules", "build", "dist"}
EXCLUDE_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".pyc", ".pyo", ".log"}

# clean_app profile: also strip this toolkit's *build scaffolding* so the export is the tool
# itself, not the WIP project that produced it. State (_state/: journal/evidence/event-log/
# workbench) is left empty on purpose  -  once installed it becomes the TARGET's history.
CLEAN_APP_STRIP = {
    "_exports", "_tmp_sqlite_probe",
    "_state",  # durable memory: the TARGET's history, never the toolkit's to ship
    "tools/vendor_export/clean_app_docs",  # the override templates ship AS the docs, not verbatim
    "packaging",  # build/packaging tooling (the installer wraps the product from OUTSIDE the zip)

    # --- development scaffolding: never vended -------------------------------
    # These became reachable when the sidecar was collapsed to the repository root.
    # Previously the ship boundary was the nested toolkit/ folder, so everything here
    # sat outside it and no exclusion was needed. Afterwards it was all in scope, and
    # an install copied 4,009 files - the operator's entire reference library and this
    # project's own build records - into every target. That breaks the precept (the
    # target must learn nothing about the sidecar) and the blank-vend condition.
    "_harness",     # the proving ground; also a RECURSION guard, its targets live inside
    ".bcc",         # builder contract, charter, plan, evidence
    "_docs",        # the sidecar's own journal - the TARGET's record starts empty
    "gates",        # tranche gates
    "_trash",       # removal staging
    ".plans-and-parts_FOR-REFERENCE-ONLY",  # parts bin: predecessor apps and their plans
    ".useful-helpers-test-tmp",             # suite scratch
    "requirements-dev.txt",                 # dev-only dependency declaration
}

# clean_app: after copy, these export files are replaced by the tool-focused templates so the
# clean app never links to stripped build docs. (source_rel_in_toolkit -> dest_rel_in_export)
CLEAN_APP_DOC_OVERRIDES = {
    "tools/vendor_export/clean_app_docs/README.md": "README.md",
    "tools/vendor_export/clean_app_docs/ONBOARDING.md": "_docs/ONBOARDING.md",
}


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _safe_name(value: str) -> str:
    out = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value).strip("-")
    return out or "export"


def _fingerprint(rows: list[dict]) -> str:
    h = hashlib.sha256()
    for row in rows:
        h.update(row["path"].encode("utf-8"))
        h.update(str(row["size_bytes"]).encode("ascii"))
    return h.hexdigest()


@tool_main
def run(args: dict) -> dict:
    workspace = Path.cwd().resolve()
    source = (workspace / str(args.get("root") or ".")).resolve()
    if not source.is_dir():
        return {"ok": False, "error": f"root is not a directory: {source}"}
    if not _inside(workspace, source):
        return {"ok": False, "error": "root must stay inside the workspace"}
    dry_run = bool(args.get("dry_run", True))
    confirm = bool(args.get("confirm", False))
    if not dry_run and not confirm:
        return {"ok": False, "error": "vendor_export requires confirm:true when dry_run is false"}

    name = _safe_name(str(args.get("name") or f"{source.name}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"))
    # Default the export under the toolkit home (generated artifact); an explicit out_root writes
    # wherever it points, as long as it stays inside the work target.
    out_arg = args.get("out_root")
    if out_arg:
        out_root = (workspace / str(out_arg)).resolve()
        if not _inside(workspace, out_root):
            return {"ok": False, "error": "out_root must stay inside the workspace"}
    else:
        out_root = suite_home() / "_artifacts" / "vendor_exports"
    export_dir = out_root / name
    make_zip = bool(args.get("zip", True))
    limit = max(1, min(int(args.get("limit", 5000)), 50_000))

    # Path-based exclusion (root-relative posix): a dir prunes its subtree, a file drops it.
    # The clean_app profile folds in the build-scaffolding strip list.
    exclude_paths = {str(p).strip().replace("\\", "/").strip("/")
                     for p in (args.get("exclude_paths") or []) if str(p).strip()}
    if args.get("clean_app"):
        exclude_paths |= CLEAN_APP_STRIP

    rows = []
    skipped = []
    for current, dir_names, file_names in os.walk(source):
        here = Path(current)
        rel_here = here.relative_to(source) if here != source else Path("")
        kept = []
        for dirname in sorted(dir_names):
            rel_dir = (rel_here / dirname).as_posix()
            if dirname in EXCLUDE_DIRS:
                skipped.append({"path": rel_dir, "reason": "excluded_dir"})
                continue
            if rel_dir in exclude_paths:
                skipped.append({"path": rel_dir, "reason": "excluded_path"})
                continue
            kept.append(dirname)
        dir_names[:] = kept
        for filename in sorted(file_names):
            path = here / filename
            rel = (rel_here / filename).as_posix()
            if path.suffix.lower() in EXCLUDE_SUFFIXES:
                skipped.append({"path": rel, "reason": "excluded_suffix"})
                continue
            if rel in exclude_paths:
                skipped.append({"path": rel, "reason": "excluded_path"})
                continue
            try:
                size = path.stat().st_size
            except OSError:
                skipped.append({"path": rel, "reason": "stat_failed"})
                continue
            rows.append({"path": rel, "size_bytes": size})
            if len(rows) >= limit:
                break
        if len(rows) >= limit:
            break

    written = []
    zip_path = None
    if not dry_run:
        if export_dir.exists() and not bool(args.get("overwrite", False)):
            return {"ok": False, "error": f"export_dir exists; use overwrite:true: {export_dir}"}
        if export_dir.exists():
            shutil.rmtree(export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        for row in rows:
            src = source / row["path"]
            dst = export_dir / row["path"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            written.append(row["path"])
        if args.get("clean_app"):
            for src_rel, dst_rel in CLEAN_APP_DOC_OVERRIDES.items():
                tmpl = source / src_rel
                if tmpl.is_file():
                    dst = export_dir / dst_rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(tmpl, dst)
        # Record only the source dir NAME, never the builder's absolute path (a vended artifact
        # must not leak the build machine's layout  -  roots contract / field report A5).
        manifest = {"name": name, "source": source.name, "file_count": len(rows),
                    "skipped_count": len(skipped), "fingerprint": _fingerprint(rows)}
        (export_dir / "VENDOR_EXPORT_MANIFEST.json").write_text(
            __import__("json").dumps(manifest, indent=2), encoding="utf-8")
        if make_zip:
            zip_path = out_root / f"{name}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file in export_dir.rglob("*"):
                    if file.is_file():
                        zf.write(file, file.relative_to(out_root).as_posix())

    return {"tool": "vendor_export", "root": source.as_posix(), "dry_run": dry_run,
            "export_dir": export_dir.as_posix(), "zip_path": zip_path.as_posix() if zip_path else "",
            "files": rows[:200], "skipped": skipped[:200], "written_count": len(written),
            "summary": {"file_count": len(rows), "skipped_count": len(skipped),
                        "fingerprint": _fingerprint(rows), "truncated": len(rows) >= limit,
                        "written": not dry_run}}

