"""
FILE:       apps/projectmapper/cli.py
ROLE:       Headless project snapshotter  -  scan a project tree into a portable, self-describing
            SQLite artifact (+ optional Markdown projections).
DOMAIN:     app
DOES:       action=compile: walk `root` (read-only), capture the tree + text-readable file
            contents into `_artifacts/projectmapper/<name>_snapshot.sqlite3` with an embedded
            manifest, sidecar manifest.json + .sha256, and (optional) tree/filedump Markdown.
DEPENDS ON: tools._toolkit, (stdlib) sqlite3, hashlib, json, os, datetime, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
NOTES:      Pure compile core: deterministic ordering + content checksum, so the same
            tree always produces the same snapshot.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from tools._toolkit import suite_home, tool_main

APP_VERSION = "0.1.0"
MANIFEST_VERSION = "1.0"
MAX_TEXT_FILE_SIZE_BYTES = 1_000_000

_EXCLUDED_FOLDERS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", ".mypy_cache", ".pytest_cache",
    "_logs", "logs", "_projectmapper", "_artifacts", "dist", "build",
    ".vscode", ".idea", "target", "out", "bin", "obj",
}
_FORCE_BINARY_SUFFIXES = {
    ".gz", ".zip", ".rar", ".7z", ".bz2", ".xz", ".tgz", ".png", ".jpg", ".jpeg", ".gif",
    ".bmp", ".ico", ".webp", ".tif", ".tiff", ".mp3", ".wav", ".ogg", ".flac", ".mp4", ".mkv",
    ".avi", ".mov", ".webm", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".exe",
    ".dll", ".so", ".o", ".a", ".lib", ".db", ".sqlite", ".sqlite3", ".db3", ".pyc", ".pyo",
    ".class", ".jar", ".wasm", ".ttf", ".otf", ".woff", ".woff2", ".iso", ".img", ".bin", ".bak",
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshot_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS snapshot_manifest (
  id INTEGER PRIMARY KEY CHECK (id = 1), manifest_version TEXT NOT NULL, title TEXT NOT NULL,
  summary TEXT NOT NULL, contents_markdown TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS project_tree (
  tree_order INTEGER NOT NULL, relative_path TEXT PRIMARY KEY, parent_relative_path TEXT,
  name TEXT NOT NULL, entry_type TEXT NOT NULL, depth INTEGER NOT NULL, size_bytes INTEGER,
  is_selected INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS project_files (
  dump_order INTEGER NOT NULL, relative_path TEXT PRIMARY KEY, parent_relative_path TEXT,
  size_bytes INTEGER NOT NULL, content TEXT NOT NULL, captured_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS snapshot_skipped_paths (
  id INTEGER PRIMARY KEY AUTOINCREMENT, relative_path TEXT NOT NULL, skip_reason TEXT NOT NULL,
  detail TEXT, size_bytes INTEGER, entry_type TEXT, source TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS snapshot_errors (
  id INTEGER PRIMARY KEY AUTOINCREMENT, relative_path TEXT, error TEXT NOT NULL, context TEXT,
  created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_tree_order ON project_tree(tree_order);
CREATE INDEX IF NOT EXISTS idx_files_order ON project_files(dump_order);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rel(p: Path, root: Path) -> str:
    try:
        return p.relative_to(root).as_posix()
    except Exception:
        return p.name


def _is_binary(path: Path) -> bool:
    try:
        with open(path, "rb") as h:
            return b"\0" in h.read(1024)
    except Exception:
        return True


def _safe_size(path: Path):
    try:
        return path.stat().st_size
    except OSError:
        return None


def _safe_read_text(path: Path, max_bytes: int):
    size = _safe_size(path)
    if size is None:
        return None, "stat_failed"
    if size > max_bytes:
        return None, "over_size_limit"
    if "".join(path.suffixes).lower() in _FORCE_BINARY_SUFFIXES:
        return None, "forced_binary_extension"
    if _is_binary(path):
        return None, "binary_detected"
    try:
        return path.read_text(encoding="utf-8", errors="ignore"), None
    except PermissionError:
        return None, "permission_denied"
    except Exception as exc:
        return None, f"read_failed: {exc}"


def _gitignore_dir_names(root: Path) -> set[str]:
    """Best-effort prune names from the project's root .gitignore (toggle: respect_gitignore).
    Only unambiguous single-segment names are honored (e.g. `dist`, `node_modules/`); full
    gitignore semantics  -  globs, negation, nested paths  -  are intentionally NOT interpreted,
    so the snapshot stays predictable. Default behavior (toggle off) ignores .gitignore."""
    names: set[str] = set()
    gi = root / ".gitignore"
    if not gi.exists():
        return names
    for line in gi.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("!"):
            continue
        s = s.strip("/")
        if s and "/" not in s and "*" not in s and "?" not in s:
            names.add(s)
    return names


def _scan(root: Path, excludes: set[str], max_bytes: int, exclude_paths: set[str] | None = None):
    """Walk `root`, returning (tree, captured_files, skipped).

    `exclude_paths` is the tree-picker's deselection (root-relative posix paths, model A:
    everything selected by default). A deselected DIRECTORY is recorded with is_selected=0
    and its subtree is not walked; a deselected FILE is recorded with is_selected=0 and its
    content is not captured (logged skipped as `unchecked_by_user`). This differs from name/
    dot/gitignore excludes, which prune entries out of the tree entirely."""
    exclude_paths = exclude_paths or set()
    tree, files, skipped = [], [], []
    order = dump = 0
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        parent = _rel(here, root) if here != root else None
        # Sidecar convention: dot-folders + explicit name-excludes are never scanned.
        visible = sorted(d for d in dirnames if d not in excludes and not d.startswith("."))
        descend = []
        for d in visible:
            order += 1
            rel = _rel(here / d, root)
            selected = rel not in exclude_paths
            tree.append({"o": order, "rel": rel, "parent": parent, "name": d,
                         "type": "directory", "depth": rel.count("/"), "size": None,
                         "sel": selected})
            if selected:
                descend.append(d)  # deselected dirs are recorded but their subtree is skipped
        dirnames[:] = descend
        for f in sorted(filenames):
            order += 1
            fp = here / f
            rel = _rel(fp, root)
            size = _safe_size(fp)
            selected = rel not in exclude_paths
            tree.append({"o": order, "rel": rel, "parent": parent, "name": f,
                         "type": "file", "depth": rel.count("/"), "size": size,
                         "sel": selected})
            if not selected:
                skipped.append({"rel": rel, "reason": "unchecked_by_user", "size": size})
                continue
            content, err = _safe_read_text(fp, max_bytes)
            if err:
                skipped.append({"rel": rel, "reason": err, "size": size})
            else:
                dump += 1
                files.append({"o": dump, "rel": rel, "parent": parent,
                              "size": size or 0, "content": content})
    return tree, files, skipped


def _content_checksum(files: list[dict]) -> str:
    h = hashlib.sha256()
    for r in files:  # dump_order is stable (sorted walk)
        h.update(r["rel"].encode("utf-8"))
        h.update(b"\0")
        h.update(r["content"].encode("utf-8", errors="ignore"))
        h.update(b"\0")
    return h.hexdigest()


def _tree_markdown(tree: list[dict]) -> str:
    lines = ["# Project Tree", ""]
    for r in tree:
        indent = "  " * r["depth"]
        mark = "/" if r["type"] == "directory" else ""
        sel = "" if r.get("sel", True) else "  (deselected)"
        lines.append(f"{indent}- {r['name']}{mark}{sel}")
    return "\n".join(lines) + "\n"


def _manifest_markdown(name: str, meta: dict, sidecar: dict) -> str:
    """The snapshot's manifest as a document a human reads, not as a JSON sidecar.

    Renders the SAME values already recorded in `snapshot_metadata` and the sidecar, so
    the three cannot disagree - including the capture selection (parity row 1.6) and the
    regenerate command, which is the whole point of a manifest that can describe itself.
    """
    gen = sidecar.get("generation", {})
    vol = sidecar.get("volumetrics", {})
    lines = [f"# {name} — snapshot manifest", "",
             f"- **created** {meta.get('created_at')}",
             f"- **source root** `{meta.get('source_root')}`",
             f"- **generated by** {meta.get('generated_by')}",
             f"- **content checksum** `{meta.get('content_checksum_sha256')}`",
             f"- **artifact sha256** `{sidecar.get('integrity', {}).get('artifact_sha256')}`",
             "", "## Capture selection", "",
             f"- excluded folders: `{gen.get('excluded_folders')}`",
             f"- deselected paths: `{gen.get('exclude_paths')}`",
             f"- max text file size: {gen.get('max_text_file_size_bytes')} bytes",
             f"- output: `{gen.get('output_path')}`",
             "", "## Volumetrics", "",
             f"- directories: {vol.get('dir_count')}",
             f"- files: {vol.get('file_count')}",
             f"- text files captured: {vol.get('text_file_count')}",
             f"- skipped: {vol.get('skipped_count')}",
             "", "## Reproduce", "", "```", str(gen.get("regenerate_command")), "```", ""]
    caveats = sidecar.get("caveats") or []
    if caveats:
        lines += ["## Caveats", ""] + [f"- {c}" for c in caveats] + [""]
    return "\n".join(lines)


def _filedump_markdown(files: list[dict]) -> str:
    out = ["# File Dump", ""]
    for r in files:
        out += [f"## `{r['rel']}`", "", "```", r["content"].rstrip("\n"), "```", ""]
    return "\n".join(out) + "\n"


@tool_main
def run(args: dict) -> dict:
    if str(args.get("action", "compile")).lower() != "compile":
        return {"ok": False, "error": "only action=compile is supported"}

    root_arg = args.get("root")
    if not root_arg:
        return {"ok": False, "error": "'root' (project to snapshot) is required"}
    root = Path(root_arg).resolve()
    if not root.is_dir():
        return {"ok": False, "error": f"not a directory: {root}"}

    name = str(args.get("name") or root.name)
    max_bytes = int(args.get("max_bytes", MAX_TEXT_FILE_SIZE_BYTES))
    excludes = set(_EXCLUDED_FOLDERS) | {str(x) for x in (args.get("exclude") or [])}
    if args.get("respect_gitignore"):
        excludes |= _gitignore_dir_names(root)
    # Tree-picker deselection (model A: everything selected unless listed). Normalize to
    # root-relative posix so it matches the paths _scan produces.
    exclude_paths = {str(p).strip().replace("\\", "/").strip("/")
                     for p in (args.get("exclude_paths") or []) if str(p).strip()}
    out_arg = args.get("out")
    # Default the snapshot under the toolkit home so the host project stays clean; an explicit
    # `out` writes wherever the caller points (opt-in, e.g. into the project).
    out_db = Path(out_arg).resolve() if out_arg else (
        suite_home() / "_artifacts" / "projectmapper" / f"{name}_snapshot.sqlite3")

    # Source-integrity guard (cartridge sec D): the SCANNED tree stays pristine. Output may
    # co-locate inside the project ONLY within a sidecar the scan skips  -  a dot-folder
    # (e.g. .map/) or an explicitly-excluded dir  -  so a re-scan never ingests its own output.
    try:
        rel_out = out_db.relative_to(root)
    except ValueError:
        rel_out = None
    if rel_out is not None:
        top = rel_out.parts[0] if len(rel_out.parts) > 1 else None
        if top is None:
            return {"ok": False, "error": "refusing to write the snapshot loose in the scanned "
                    "root; use a sidecar subfolder (a dot-folder like .map/) or an 'out' outside "
                    "the project"}
        if not (top.startswith(".") or top in excludes):
            return {"ok": False, "error": f"'{top}/' would be scanned into the snapshot; write the "
                    f"output into a dot-folder sidecar (e.g. .map/), add '{top}' to exclude, or "
                    "choose an 'out' outside the project"}
        excludes.add(top)  # the sidecar holding the snapshot is never scanned

    tree, files, skipped = _scan(root, excludes, max_bytes, exclude_paths)
    checksum = _content_checksum(files)
    now = _now()

    out_db.parent.mkdir(parents=True, exist_ok=True)
    if out_db.exists():
        out_db.unlink()  # deterministic rebuild
    conn = sqlite3.connect(str(out_db))
    try:
        conn.execute("PRAGMA journal_mode=OFF")
        conn.executescript(_SCHEMA)
        conn.executemany(
            "INSERT OR REPLACE INTO project_tree (tree_order, relative_path, parent_relative_path,"
            " name, entry_type, depth, size_bytes, is_selected) VALUES (?,?,?,?,?,?,?,?)",
            [(r["o"], r["rel"], r["parent"], r["name"], r["type"], r["depth"], r["size"],
              1 if r.get("sel", True) else 0) for r in tree])
        conn.executemany(
            "INSERT OR REPLACE INTO project_files (dump_order, relative_path, parent_relative_path,"
            " size_bytes, content, captured_at) VALUES (?,?,?,?,?,?)",
            [(r["o"], r["rel"], r["parent"], r["size"], r["content"], now) for r in files])
        conn.executemany(
            "INSERT INTO snapshot_skipped_paths (relative_path, skip_reason, size_bytes, entry_type,"
            " source) VALUES (?,?,?, 'file', 'scan')",
            [(s["rel"], s["reason"], s["size"]) for s in skipped])

        dir_count = sum(1 for r in tree if r["type"] == "directory")
        file_count = sum(1 for r in tree if r["type"] == "file")
        deselected_count = sum(1 for s in skipped if s["reason"] == "unchecked_by_user")
        # PARITY ROW 1.6 — the artifact must record the SELECTION that shaped it.
        #
        # `regenerate_command` carried only action/root/name, and the metadata recorded the
        # ordinary folder-exclusion set but not the user's `exclude_paths` deselection, nor
        # `out`, nor the markdown request. So a snapshot said "run this to reproduce me"
        # and the command reproduced a DIFFERENT capture scope - wider than the one the
        # artifact actually describes. A portable, self-describing artifact that cannot
        # describe its own scope is not yet portable, and a regenerate command that
        # silently regenerates something else is worse than none at all.
        #
        # Reconstructed from the same values the scan used, not from `args`: recording what
        # was ASKED FOR rather than what was APPLIED would reintroduce the same gap one
        # level down (`exclude_paths` is normalised before use).
        regen_args = {"action": "compile", "root": str(root), "name": name}
        if exclude_paths:
            regen_args["exclude_paths"] = sorted(exclude_paths)
        if args.get("exclude"):
            regen_args["exclude"] = sorted(str(x) for x in args["exclude"])
        if args.get("respect_gitignore"):
            regen_args["respect_gitignore"] = True
        if max_bytes != MAX_TEXT_FILE_SIZE_BYTES:
            regen_args["max_bytes"] = max_bytes
        if out_arg:
            regen_args["out"] = str(out_arg)
        if args.get("markdown"):
            regen_args["markdown"] = args["markdown"]
        regen = ("python -m src.app cli tool-call --tool projectmapper --args-json "
                 f"'{json.dumps(regen_args, sort_keys=True)}'")
        meta = {
            "project_name": name, "source_root": str(root), "generated_by": f"apps/projectmapper {APP_VERSION}",
            "created_at": now, "max_text_file_size_bytes": max_bytes,
            "excluded_folders": json.dumps(sorted(excludes)), "dir_count": dir_count,
            "file_count": file_count, "text_file_count": len(files), "skipped_count": len(skipped),
            "deselected_count": deselected_count,
            # The deselection itself, not merely how many there were. A count tells a
            # reader that something was dropped; only the list says WHAT.
            "exclude_paths": json.dumps(sorted(exclude_paths)),
            "output_path": str(out_db),
            "markdown_requested": json.dumps(args.get("markdown") or []),
            "content_checksum_sha256": checksum, "regenerate_command": regen,
        }
        conn.executemany("INSERT OR REPLACE INTO snapshot_metadata (key, value) VALUES (?, ?)",
                         [(k, str(v)) for k, v in meta.items()])
        contents_md = ("Tables: snapshot_metadata, snapshot_manifest, project_tree, project_files, "
                       "snapshot_skipped_paths, snapshot_errors.")
        conn.execute(
            "INSERT OR REPLACE INTO snapshot_manifest (id, manifest_version, title, summary,"
            " contents_markdown, created_at) VALUES (1,?,?,?,?,?)",
            (MANIFEST_VERSION, str(args.get("title") or f"{name} snapshot"),
             str(args.get("summary") or f"Portable snapshot of {name} ({file_count} files, "
                 f"{len(files)} captured)."), contents_md, now))
        conn.commit()
    finally:
        conn.close()

    db_sha = hashlib.sha256(out_db.read_bytes()).hexdigest()
    (out_db.parent / (out_db.name + ".sha256")).write_text(f"{db_sha}  {out_db.name}\n", encoding="utf-8")
    sidecar = {
        "identity": {"name": name, "type": "project_snapshot", "version": MANIFEST_VERSION, "created_at": now},
        "lineage": {"source_root": str(root), "content_checksum_sha256": checksum},
        # The sidecar manifest carries the same selection as the database, so neither half
        # of the artifact can describe a scope the other does not.
        "generation": {"tool": f"apps/projectmapper {APP_VERSION}", "max_text_file_size_bytes": max_bytes,
                       "excluded_folders": sorted(excludes),
                       "exclude_paths": sorted(exclude_paths),
                       "output_path": str(out_db),
                       "markdown_requested": args.get("markdown") or [],
                       "regenerate_command": meta["regenerate_command"]},
        "schema": {"tables": ["snapshot_metadata", "snapshot_manifest", "project_tree",
                              "project_files", "snapshot_skipped_paths", "snapshot_errors"]},
        "volumetrics": {"dir_count": dir_count, "file_count": file_count,
                        "text_file_count": len(files), "skipped_count": len(skipped)},
        "integrity": {"artifact_sha256": db_sha},
        "caveats": ["Binary files are not captured (recorded in snapshot_skipped_paths).",
                    f"Text files over {max_bytes} bytes are skipped.",
                    "Dot-prefixed directories (sidecars) are not scanned."],
    }
    (out_db.parent / (out_db.stem + ".manifest.json")).write_text(
        json.dumps(sidecar, indent=2), encoding="utf-8")

    outputs = {"snapshot_db": _rel(out_db, Path.cwd()), "sha256": _rel(out_db, Path.cwd()) + ".sha256",
               "manifest": _rel(out_db.parent / (out_db.stem + ".manifest.json"), Path.cwd())}
    if args.get("markdown"):
        # PARITY ROWS 1.4 AND 1.5, found by EXECUTING rows the census had marked
        # satisfied. The donor contract names four markdown exports - "project tree,
        # filedump, combined tree plus filedump, and manifest markdown" - and only two
        # were ever written. The census read the capability list and believed it; running
        # it produced `tree_md` and `filedump_md` and nothing else.
        #
        # The manifest existed only as `.manifest.json` and as a one-line `contents_markdown`
        # blurb inside the database. A JSON sidecar is not a markdown export, and a
        # table-of-contents string is not a manifest: neither is a document a human opens
        # to see what this snapshot IS.
        tree_text, dump_text = _tree_markdown(tree), _filedump_markdown(files)
        tree_md = out_db.parent / f"{name}_project_tree.md"
        dump_md = out_db.parent / f"{name}_project_filedump.md"
        comb_md = out_db.parent / f"{name}_project_combined.md"
        man_md = out_db.parent / f"{name}_project_manifest.md"
        tree_md.write_text(tree_text, encoding="utf-8")
        dump_md.write_text(dump_text, encoding="utf-8")
        # Composed from the same two strings rather than regenerated: a "combined" export
        # that could differ from its own halves would be a third artifact wearing their name.
        comb_md.write_text(f"{tree_text}\n\n---\n\n{dump_text}", encoding="utf-8")
        man_md.write_text(_manifest_markdown(name, meta, sidecar), encoding="utf-8")
        outputs["tree_md"] = _rel(tree_md, Path.cwd())
        outputs["filedump_md"] = _rel(dump_md, Path.cwd())
        outputs["combined_md"] = _rel(comb_md, Path.cwd())
        outputs["manifest_md"] = _rel(man_md, Path.cwd())

    return {
        "tool": "projectmapper", "action": "compile", "name": name,
        "source_root": str(root), "dir_count": dir_count, "file_count": file_count,
        "text_file_count": len(files), "skipped_count": len(skipped),
        "deselected_count": deselected_count,
        "content_checksum": checksum, "artifact_sha256": db_sha, "outputs": outputs,
    }
