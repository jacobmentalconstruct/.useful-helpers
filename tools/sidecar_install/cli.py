"""
FILE:       tools/sidecar_install/cli.py
ROLE:       Install the toolkit as a self-contained sidecar inside an EXTERNAL target project.
DOMAIN:     tool
DOES:       Dry-run-first. Copies a clean-app view of the running toolkit (same exclusions as
            vendor_export's clean_app profile) into <target>/<folder> (default .useful-helpers/),
            so a host project gains ONE self-contained directory and nothing collides with its
            files or git. Writes NOTHING outside that directory  -  see NOTES.
DEPENDS ON: tools._toolkit, tools.vendor_export.cli (shared clean-export exclusion lists),
            (stdlib) os, shutil, pathlib
WIRES TO:   invoked by src/core/invoke.py; driven by the installer GUI (src/ui/installer_view.py)
NOTES:      This is the ONE tool that deliberately writes OUTSIDE the workspace  -  that is the
            whole job (install into a project you pick). It writes EXACTLY ONE directory and
            nothing else. Guarded: dry-run-first + confirm; refuses to install into itself or into
            a parent/child of the source tree. Memory ships EMPTY on purpose: once installed, the
            sidecar's journal/evidence become the TARGET project's history, not the toolkit's.

            It used to drop an AGENTS.md pointer in the host root and append itself to the host's
            .gitignore, ON BY DEFAULT  -  while the pointer's own text claimed "the project stays
            ignorant of the sidecar". Both options are GONE, not defaulted off: CHARTER.md sec 1
            disqualifies any design that edits a host file, so the switch must not exist to be
            flipped back on. There is deliberately no breadcrumb  -  a human points their agent at
            <folder>/AGENTS.md. Enforced by tests/test_smoke.py::test_target_is_never_modified.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from tools._toolkit import suite_home, tool_main
from tools.vendor_export.cli import CLEAN_APP_DOC_OVERRIDES, CLEAN_APP_STRIP, EXCLUDE_DIRS, EXCLUDE_SUFFIXES

_DEFAULT_FOLDER = ".useful-helpers"

def _clean_files(source: Path) -> list[str]:
    """Root-relative posix paths of the clean-app file set (mirrors vendor_export clean_app)."""
    rows: list[str] = []
    for current, dir_names, file_names in os.walk(source):
        here = Path(current)
        rel_here = here.relative_to(source) if here != source else Path("")
        kept = []
        for dirname in sorted(dir_names):
            rel_dir = (rel_here / dirname).as_posix()
            if dirname in EXCLUDE_DIRS or rel_dir in CLEAN_APP_STRIP:
                continue
            kept.append(dirname)
        dir_names[:] = kept
        for filename in sorted(file_names):
            rel = (rel_here / filename).as_posix()
            if Path(filename).suffix.lower() in EXCLUDE_SUFFIXES or rel in CLEAN_APP_STRIP:
                continue
            rows.append(rel)
    return rows


def _nested(a: Path, b: Path) -> bool:
    """True if a is inside b or b is inside a (or equal)."""
    a, b = a.resolve(), b.resolve()
    return a == b or _inside(a, b) or _inside(b, a)


def _inside(inner: Path, outer: Path) -> bool:
    try:
        inner.resolve().relative_to(outer.resolve())
        return True
    except ValueError:
        return False


@tool_main
def run(args: dict) -> dict:
    target_arg = args.get("target")
    if not target_arg:
        return {"ok": False, "error": "'target' (project folder to install into) is required"}
    target = Path(target_arg).expanduser().resolve()
    if not target.is_dir():
        return {"ok": False, "error": f"target is not an existing directory: {target}"}

    # Vend the RUNNING TOOLKIT (SUITE_HOME), not the work-target cwd. As a sidecar, tools run
    # with cwd = the host project, so cwd is the wrong source  -  the installer must copy itself.
    source = suite_home()
    folder = str(args.get("folder") or _DEFAULT_FOLDER).strip().strip("/\\") or _DEFAULT_FOLDER
    sidecar = (target / folder).resolve()
    if _nested(source, target):
        return {"ok": False, "error": "target overlaps the toolkit source tree; choose a "
                "separate project folder"}

    dry_run = bool(args.get("dry_run", True))
    confirm = bool(args.get("confirm", False))
    overwrite = bool(args.get("overwrite", False))
    update = bool(args.get("update", False))
    if not dry_run and not confirm:
        return {"ok": False, "error": "sidecar_install requires confirm:true when dry_run is false"}
    if sidecar.exists() and not (overwrite or update):
        return {"ok": False, "error": f"sidecar already exists; use update:true (preserve "
                f"runtime memory) or overwrite:true (clean reinstall): {sidecar}"}

    files = _clean_files(source)
    mode = "update (overlay, preserve runtime memory)" if update and sidecar.exists() else (
        "overwrite (clean reinstall)" if overwrite and sidecar.exists() else "fresh install")
    plan = {
        "tool": "sidecar_install", "dry_run": dry_run, "target": target.as_posix(),
        "sidecar": sidecar.as_posix(), "file_count": len(files), "mode": mode,
        # Stated in the tool's own output so the precept is visible at the call site.
        "host_writes": "none  -  everything lands inside the sidecar folder",
    }
    if dry_run:
        plan["sample"] = files[:25]
        return plan

    # --- apply ---
    # update overlays the code and leaves everything else untouched  -  durable memory lives in
    # the state root (_state/: journal, evidence, event-log, workbench) and artifacts in
    # _artifacts/. That lifecycle split is exactly why state_root is its own root.
    # overwrite wipes first.
    if sidecar.exists() and overwrite and not update:
        shutil.rmtree(sidecar)
    written = 0
    for rel in files:
        dst = sidecar / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / rel, dst)
        written += 1
    # tool-focused docs (same override as clean_app export)
    for src_rel, dst_rel in CLEAN_APP_DOC_OVERRIDES.items():
        tmpl = source / src_rel
        if tmpl.is_file():
            (sidecar / dst_rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(tmpl, sidecar / dst_rel)
    # Marker: tells the toolkit it is installed as a sidecar, so its work target is the parent
    # project (resolve_paths -> project_root). Robust even if the sidecar folder is not dotted.
    (sidecar / ".suite_sidecar").write_text(
        "This directory is a Useful Helpers sidecar; the project it manages is the parent.\n",
        encoding="utf-8")

    plan.update({"written_count": written})
    return plan
