"""
FILE:       tools/write_file/cli.py
ROLE:       Create or overwrite a file through the governed seam (the sidecar's `Write`).
DOMAIN:     tool
DOES:       Preview-first: report what would be written (path, bytes, exists, overwrite). On
            write:true (or apply:true) it creates parent dirs and writes the content. Refuses
            paths outside the work target / toolkit home.
DEPENDS ON: tools._toolkit, (stdlib) pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Declares writes:target so writing into the work target is the SANCTIONED, audited
            path  -  not a Bash end-run around the precept. Preview-first; refuses to clobber an
            existing file unless overwrite is left on (default true)  -  pass overwrite:false to
            create-only.
"""
from __future__ import annotations

from datetime import datetime

from tools._toolkit import apply_with, confirmed, resolve_within_roots, tool_main


def _unique_path(path):
    """A timestamp-suffixed sibling that does not exist yet.

    PARITY ROW 6.4. `overwrite:false` REFUSES when the name is taken; the donor's useful
    outcome is that a uniquely named file gets CREATED. Those are different outcomes for
    the caller - one produces a file and one does not - so the refusal could not stand in
    for it. `stamp` was proven unrelated (it generates tool skeletons), so the behaviour
    lands on the tool that actually produces files, not on the donor's tool name.

    The counter exists because a timestamp is not a uniqueness guarantee: two writes
    inside the same second would otherwise collide, and "unique" would be a claim rather
    than a property. It is bounded because an unbounded search for a free name is a hang
    dressed as robustness.
    """
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = path.with_name(f"{path.stem}-{stamp}{path.suffix}")
    if not candidate.exists():
        return candidate, None
    for n in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{stamp}-{n}{path.suffix}")
        if not candidate.exists():
            return candidate, None
    return None, f"could not find a free name beside {path.name} after 999 attempts"


@tool_main
def run(args: dict) -> dict:
    if "content" not in args:
        return {"ok": False, "error": "content is required"}
    path, err = resolve_within_roots(args.get("path", ""))
    if err:
        return {"ok": False, "error": err}
    content = str(args["content"])
    overwrite = bool(args.get("overwrite", True))
    unique = bool(args.get("unique"))

    if path.exists() and path.is_dir():
        return {"ok": False, "error": f"path is a directory: {path}"}

    # UNIQUE IS RESOLVED BEFORE THE PLAN, so the preview names the path that will actually
    # be written. Deferring it to the apply would let a preview show `note.txt` and a write
    # land on `note-20260820-015043.txt` - the exact "approved one thing, did another"
    # failure T8 spent a tranche closing.
    requested = path
    uniquified = False
    if unique and path.is_file():
        path, uerr = _unique_path(path)
        if uerr:
            return {"ok": False, "error": uerr}
        uniquified = True

    exists = path.is_file()
    # `unique` supersedes the refusal rather than fighting it: with a free name in hand
    # there is nothing to clobber. Without `unique`, behaviour is byte-for-byte what it
    # was - this row must not change what existing callers get.
    if exists and not overwrite:
        return {"ok": False, "error": f"file exists and overwrite is false: {path}"}

    plan = {
        "tool": "write_file",
        "path": path.as_posix(),
        "bytes": len(content.encode("utf-8")),
        "exists": exists,
        "would_overwrite": exists,
    }
    if uniquified:
        plan["requested_path"] = requested.as_posix()
        plan["uniquified"] = True
    if not confirmed(args, legacy=("write", "confirm")):
        # The APPROVAL CARRIES THE RESOLVED PATH. Sending `apply_with` back unmodified
        # writes the reviewed file, not a freshly-timestamped one computed a second later.
        hint = apply_with()
        if uniquified:
            hint = {**hint, "path": path.as_posix(), "unique": False}
        return {**plan, "dry_run": True, "written": False, "apply_with": hint}

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {**plan, "dry_run": False, "written": True}
