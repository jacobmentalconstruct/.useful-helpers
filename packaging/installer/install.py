"""
FILE:       packaging/installer/install.py
ROLE:       Friendly sidecar installer - pick a project folder, confirm, drop in .useful-helpers/.
DOMAIN:     packaging (ships NEXT TO the product zip, not inside it)
DOES:       GUI path: a folder picker chooses the target project; an HITL dialog confirms; if a
            sidecar already exists it offers Reinstall (wipe) / Update (keep memory) / Cancel.
            Then it installs a clean copy of the toolkit into <target>/.useful-helpers/ and nothing
            else. Headless path (--target/--mode): the same install LOGIC with no GUI, so it is
            testable and scriptable.
DEPENDS ON: (stdlib only) argparse, os, shutil, sys, tempfile, zipfile, pathlib; tkinter for GUI.
WIRES TO:   assembled by the installer package (installer.bat / installer.sh call this); the
            payload is a sibling `useful-helpers-toolkit/` folder or `useful-helpers-toolkit.zip`.
NOTES:      Self-contained BY DESIGN: it runs on a fresh machine with only stdlib Python, and it
            copies rather than depending on the toolkit being runnable yet. It upholds the precept
            mechanically - it writes exactly ONE directory (<target>/.useful-helpers) and refuses
            any overlap between the payload and the target. GUI and logic are split so the health
            path can be proven without a display (the same pattern as the toolkit's ui-probe).
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

SIDECAR_DIR = ".useful-helpers"
PAYLOAD_FOLDER = "useful-helpers-toolkit"
PAYLOAD_ZIP = "useful-helpers-toolkit.zip"
# Defensive: the vended zip is already clean, but never carry these into a target regardless.
EXCLUDES = ("__pycache__", ".venv", "venv", ".pytest_cache", ".ruff_cache",
            "_artifacts", "_state", ".git", "*.pyc", "*.pyo")
_STATE = "_state"


# ---------------------------------------------------------------- payload resolution
def resolve_payload(here: Path) -> "tuple[Path | None, Path | None, str]":
    """Find the toolkit to install. Returns (payload_dir, temp_to_cleanup, error).

    Prefers a sibling `useful-helpers-toolkit/` folder; falls back to unzipping
    `useful-helpers-toolkit.zip` into a temp dir. The zip may wrap the tree in a top folder, so
    we descend to the directory that actually contains `src/`.
    """
    folder = here / PAYLOAD_FOLDER
    if folder.is_dir() and (folder / "src").is_dir():
        return folder, None, ""
    zip_path = here / PAYLOAD_ZIP
    if zip_path.is_file():
        tmp = Path(tempfile.mkdtemp(prefix="uh-payload-"))
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmp)
        except (OSError, zipfile.BadZipFile) as e:
            shutil.rmtree(tmp, ignore_errors=True)
            return None, None, f"could not unpack {PAYLOAD_ZIP}: {e}"
        root = _find_toolkit_root(tmp)
        if root is None:
            shutil.rmtree(tmp, ignore_errors=True)
            return None, None, f"{PAYLOAD_ZIP} does not contain a toolkit (no src/ found)"
        return root, tmp, ""
    return None, None, (f"no payload found next to the installer: expected a "
                        f"'{PAYLOAD_FOLDER}/' folder or '{PAYLOAD_ZIP}'")


def _find_toolkit_root(base: Path) -> "Path | None":
    if (base / "src").is_dir():
        return base
    for child in sorted(base.iterdir()):
        if child.is_dir() and (child / "src").is_dir():
            return child
    return None


# ---------------------------------------------------------------- install logic (headless-safe)
def sidecar_status(target: Path) -> str:
    """'new' if no sidecar, 'exists' if one is already installed at <target>/.useful-helpers."""
    return "exists" if (target / SIDECAR_DIR).is_dir() else "new"


def validate(target: Path, payload: Path) -> str:
    """Precept + safety guardrails. Returns '' if OK, else a reason to refuse."""
    if not target.is_dir():
        return f"target is not a directory: {target}"
    dest = (target / SIDECAR_DIR).resolve()
    pay = payload.resolve()
    # The one directory we write must not overlap the source we read.
    if pay == dest or _within(pay, dest) or _within(dest, pay):
        return "refusing to install: the target overlaps the installer payload"
    return ""


def _within(inner: Path, outer: Path) -> bool:
    try:
        inner.relative_to(outer)
        return True
    except ValueError:
        return False


def _ignore(_dir, names):
    out = set()
    for n in names:
        if n in EXCLUDES:
            out.add(n)
        elif n.endswith((".pyc", ".pyo")):
            out.add(n)
    return out


def _instance_module(dest: Path):
    """The identity authority, imported FROM THE PAYLOAD JUST INSTALLED.

    Deliberately not from the installer's own tree: the installer is deliverable #1
    and ships beside the payload, so the identity format that governs an instance is
    the one that shipped WITH that instance - not whatever version the installer
    happens to be.
    """
    import importlib.util
    import sys
    name = "_uh_instance"
    spec = importlib.util.spec_from_file_location(
        name, dest / "src" / "core" / "instance.py")
    mod = importlib.util.module_from_spec(spec)
    # REGISTERED BEFORE EXECUTION. `@dataclass` resolves its own module through
    # `sys.modules[cls.__module__]`, so a module loaded by path but never registered
    # raises AttributeError on the decorator - not at import, but inside dataclasses,
    # which reads as a stdlib bug rather than a loader mistake.
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


def _read_identity(dest: Path) -> "str | None":
    """The existing UUID, or None if this is not a canonical instance.

    RAISES if the manifest is PRESENT and BROKEN. That is the whole contract, and it
    used to be inverted here: this function caught `Exception` and returned None, which
    `create(identity=None)` then read as "no identity supplied" and answered by minting
    a fresh UUID. `instance.read_identity()` raises `InstanceError` precisely so that
    cannot happen - and its caller was converting the authority's loud failure into a
    silent success, orphaning every durable record keyed to the old identity on the
    first upgrade over a corrupt manifest. Journal 0028, defect 1.

    Absent is still not an error: no manifest returns None, and the caller decides.
    """
    return _instance_module(dest).read_identity(dest)


def _next_steps(target: Path, dest: Path) -> str:
    """What to actually type. Verified to run - it used to name a command that could not.

    The old message said `python .useful-helpers/src/app.py cli tool-list`, which put
    `.../src` on sys.path instead of the instance root and died with
    ModuleNotFoundError. A freshly installed sidecar could not be started by following
    its own success message.
    """
    rel = dest.name
    if os.name == "nt":
        return (f"cd {target}\n"
                f"  {rel}\\run.bat attach     (what is this target, and what next)\n"
                f"  {rel}\\run.bat list       (every tool available here)")
    return (f"cd {target}\n"
            f"  sh {rel}/run.sh attach     (what is this target, and what next)\n"
            f"  sh {rel}/run.sh list       (every tool available here)")


def install(payload: Path, target: Path, mode: str) -> dict:
    """Do the install. mode: install (new) | reinstall (wipe) | update (keep memory).
    Writes exactly one directory: <target>/.useful-helpers."""
    err = validate(target, payload)
    if err:
        return {"ok": False, "error": err}
    dest = target / SIDECAR_DIR
    exists = dest.is_dir()

    if exists and mode == "install":
        return {"ok": False, "error": "a sidecar already exists here; "
                "choose reinstall (wipe) or update (keep memory)", "status": "exists"}
    if not exists and mode in ("reinstall", "update"):
        mode = "install"  # nothing to replace; treat as a fresh install

    # LIFECYCLE POLICY LIVES HERE, identity mechanics live in src/core/instance.py.
    #
    #   fresh install  -> a new identity
    #   update         -> the SAME identity. An update is this instance with newer
    #                     code; minting a new one would orphan every durable record
    #                     keyed to the old, silently, on the first upgrade.
    #   reinstall      -> a new identity. A clean reinstall is deliberately a
    #                     different instance in the same place.
    #
    # Read BEFORE the tree is replaced, because that is the only moment the old
    # manifest still exists.
    carried_identity = None
    if mode == "update" and exists:
        try:
            carried_identity = _read_identity(dest)
        except Exception as e:
            # A manifest that is PRESENT and INVALID stops the update. The alternative
            # - continue with identity=None - is how continuity breaks silently.
            return {"ok": False, "status": "identity-broken", "sidecar": dest.as_posix(),
                    "error": f"refusing to update: the installed instance's identity is "
                             f"unreadable ({type(e).__name__}: {e}). Nothing has been "
                             f"changed. Choose reinstall to install a clean copy, "
                             f"accepting that it is a NEW instance and durable records "
                             f"keyed to the old identity will not be associated with it."}

    # BUILD BESIDE, THEN SWAP. Journal 0028, defect 2.
    #
    # The standard is RECOVERABILITY, not "do not lose _state": a failed update must
    # not leave the instance less recoverable than it was before the update began.
    # Keeping the journal beside an unstartable instance still fails that.
    #
    # The old shape moved `_state` to a system temp directory, deleted the instance
    # root, copied, moved `_state` back - and cleaned the temp directory in a `finally`
    # that could not tell "cleanup after success" from "this is the last copy". Any
    # failure inside the copy destroyed the instance AND its durable memory together.
    #
    # Now nothing is destroyed until the replacement is complete. Every failure below
    # returns with the ORIGINAL instance still in place and still startable.
    staging = target / f"{SIDECAR_DIR}.staging"
    backup = target / f"{SIDECAR_DIR}.old"
    shutil.rmtree(staging, ignore_errors=True)
    shutil.rmtree(backup, ignore_errors=True)
    try:
        shutil.copytree(payload, staging, ignore=_ignore)
        # Durable memory is COPIED forward, never moved out of the tree that owns it.
        if mode == "update" and (dest / _STATE).is_dir():
            shutil.copytree(dest / _STATE, staging / _STATE, dirs_exist_ok=True)
        # Identity is written into the staged tree before it becomes the instance, so
        # a half-installed directory is never left claiming to be one.
        ctx = _instance_module(staging).create(staging, target, identity=carried_identity)
    except Exception as e:
        shutil.rmtree(staging, ignore_errors=True)
        return {"ok": False, "status": "update-failed", "sidecar": dest.as_posix(),
                "memory_preserved": (dest / _STATE).is_dir(),
                "error": f"{mode} failed while preparing the new copy "
                         f"({type(e).__name__}: {e}). The existing instance was not "
                         f"modified."}

    try:
        if exists:
            shutil.move(str(dest), str(backup))
        shutil.move(str(staging), str(dest))
    except OSError as e:
        # The swap is the only irreversible moment, and it is two renames on one
        # filesystem. If it still fails, say exactly where the old instance is rather
        # than cleaning it away.
        return {"ok": False, "status": "swap-failed",
                "error": f"{mode} failed during the final swap ({type(e).__name__}: {e}). "
                         f"The previous instance is intact at {backup.as_posix()} and "
                         f"the new copy at {staging.as_posix()}; move one into place.",
                "previous_instance": backup.as_posix() if backup.is_dir() else None}
    shutil.rmtree(backup, ignore_errors=True)

    file_count = sum(1 for _ in dest.rglob("*") if _.is_file())
    return {"ok": True, "mode": mode, "sidecar": dest.as_posix(),
            "instance": ctx.uuid, "target": ctx.target_root.as_posix(),
            "file_count": file_count,
            # OBSERVED, not declared. This used to read `mode == "update"`, which
            # restates the request: it reported true when there was no state to keep,
            # and would have reported true on the run that lost it.
            "memory_preserved": (dest / _STATE).is_dir(),
            "next": _next_steps(target, dest)}


# ---------------------------------------------------------------- GUI (Tkinter)
def _gui_flow(payload: Path) -> dict:
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.withdraw()
    try:
        target_str = filedialog.askdirectory(title="Choose the project to install the sidecar into")
        if not target_str:
            return {"ok": False, "cancelled": True, "error": "no folder chosen"}
        target = Path(target_str)

        status = sidecar_status(target)
        if status == "new":
            if not messagebox.askokcancel(
                    "Install sidecar",
                    f"Install the Useful Helpers sidecar into:\n\n{target}\n\n"
                    f"This creates one folder: {SIDECAR_DIR}\\ and changes nothing else."):
                return {"ok": False, "cancelled": True, "error": "cancelled at confirm"}
            mode = "install"
        else:
            mode = _existing_dialog(root, target)
            if mode == "cancel":
                return {"ok": False, "cancelled": True, "error": "cancelled at existing-sidecar"}

        result = install(payload, target, mode)
        if result["ok"]:
            messagebox.showinfo("Done", f"Sidecar {result['mode']} complete.\n\n"
                                f"{result['file_count']} files at:\n{result['sidecar']}"
                                + ("\n\nExisting memory (journal/evidence) was kept."
                                   if result.get("memory_preserved") else ""))
        else:
            messagebox.showerror("Install failed", result.get("error", "unknown error"))
        return result
    finally:
        root.destroy()


def _existing_dialog(root, target: Path) -> str:
    """A 3-button HITL for an already-installed sidecar: Reinstall / Update / Cancel."""
    import tkinter as tk

    choice = {"v": "cancel"}
    win = tk.Toplevel(root)
    win.title("Sidecar already installed")
    win.grab_set()
    msg = (f"A sidecar already exists in:\n{target}\n\n"
           "Reinstall  -  delete it and install a clean copy (its memory is lost).\n"
           "Update     -  replace the code but KEEP its journal/evidence memory.\n"
           "Cancel     -  do nothing.")
    tk.Label(win, text=msg, justify="left", padx=16, pady=12).pack()
    bar = tk.Frame(win)
    bar.pack(pady=(0, 12))

    def pick(v):
        choice["v"] = v
        win.destroy()

    tk.Button(bar, text="Reinstall (wipe)", width=16,
              command=lambda: pick("reinstall")).pack(side="left", padx=6)
    tk.Button(bar, text="Update (keep memory)", width=18,
              command=lambda: pick("update")).pack(side="left", padx=6)
    tk.Button(bar, text="Cancel", width=10,
              command=lambda: pick("cancel")).pack(side="left", padx=6)
    win.wait_window()
    return choice["v"]


# ---------------------------------------------------------------- entry
def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(description="Install the Useful Helpers sidecar into a project.")
    ap.add_argument("--target", help="headless: the project directory to install into")
    ap.add_argument("--mode", choices=["install", "reinstall", "update"], default="install",
                    help="headless: install (new) | reinstall (wipe) | update (keep memory)")
    ap.add_argument("--payload", help="headless: path to an unpacked toolkit (skips zip search)")
    ns = ap.parse_args(argv)

    here = Path(__file__).resolve().parent
    if ns.payload:
        payload, tmp, err = Path(ns.payload), None, ""
        if not (payload / "src").is_dir():
            err = f"--payload has no src/: {payload}"
    else:
        payload, tmp, err = resolve_payload(here)
    if err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2

    try:
        if ns.target:  # headless
            import json
            result = install(payload, Path(ns.target), ns.mode)
            print(json.dumps(result, indent=2))
            return 0 if result["ok"] else 1
        # GUI
        try:
            result = _gui_flow(payload)
        except Exception as e:  # no display, tkinter missing, etc.
            print(f"ERROR: GUI unavailable ({e}). Use --target <dir> for a headless install.",
                  file=sys.stderr)
            return 2
        if result.get("cancelled"):
            print("Cancelled.")
            return 0
        return 0 if result.get("ok") else 1
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
