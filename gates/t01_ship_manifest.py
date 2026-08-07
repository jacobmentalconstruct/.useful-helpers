"""
FILE:       gates/t01_ship_manifest.py
ROLE:       Gate for T1 - One Ship Manifest.
DOMAIN:     factory
DOES:       Asserts there is exactly one declared description of what the sidecar
            ships, that every consumer derives from it, and that a real vend
            contains only the sidecar and none of its history.
NOTES:      Written during tranche declaration, BEFORE implementation, per
            .bcc/TRANCHE_PROTOCOL.md sec 3.2 rule 1. It is expected to fail until
            the tranche is done; that is the point.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

OUTCOME = "the sidecar vends only itself, and blank"

# The zones that must never reach a target. `_harness` is also a recursion guard:
# harness targets live inside it, so vending the root without excluding it would
# copy a target into itself.
MUST_NOT_SHIP = (
    "_harness", ".bcc", "_docs", "gates", "_trash",
    ".plans-and-parts_FOR-REFERENCE-ONLY", ".useful-helpers-test-tmp",
)

# Traces of this project's own history. None may survive a vend (charter E11).
HISTORY_MARKERS = (
    "AppJOURNAL", "CHARTER.md", "TRANCHE_PROTOCOL.md", "TRANCHE_PLAN.md",
    "event_log.sqlite3", "journal.sqlite3", "evidence",
)

PREDECESSOR_NAMES = ("mindshard", "parts-bin", "uimapper", "appfoundry", "bdneural")


def _manifest(root: Path):
    """Import the single source of truth. Returns the module or None."""
    sys.path.insert(0, str(root))
    try:
        from src.core import payload  # type: ignore
        return payload
    except Exception:
        return None
    finally:
        if str(root) in sys.path:
            sys.path.remove(str(root))


def check(r, root: Path) -> None:
    # --- 1. one source of truth exists -------------------------------------
    mod = _manifest(root)
    r.check("a single ship manifest module exists", mod is not None,
            "expected src/core/payload.py declaring the payload boundary")
    if mod is None:
        return

    never = set(getattr(mod, "NEVER_SHIP", ()) or ())
    r.check("the manifest names every development zone",
            set(MUST_NOT_SHIP) <= never,
            f"missing from manifest: {sorted(set(MUST_NOT_SHIP) - never)}")

    # --- 2. consumers derive from it, rather than repeating it -------------
    consumers = {
        "tools/vendor_export/cli.py": "vend and installer",
        "_harness/harness.py": "harness install",
        "tests/test_smoke.py": "test scopes",
    }
    for rel, what in consumers.items():
        p = root / rel
        text = p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""
        derives = "payload" in text and ("NEVER_SHIP" in text or "from src.core" in text)
        r.check(f"{what} derives from the manifest", derives,
                f"{rel} still declares its own exclusion list")

    # --- 3. ruff.toml cannot import, so it is checked for drift -------------
    ruff = (root / "ruff.toml").read_text(encoding="utf-8", errors="replace")
    missing = [d for d in MUST_NOT_SHIP if d not in ruff]
    r.check("ruff.toml excludes agree with the manifest", not missing,
            f"not excluded from lint: {missing}")

    # --- 4. a REAL vend, inspected ------------------------------------------
    probe = root / f".t01-unlink-probe-{os.getpid()}"
    try:
        probe.write_text("x", encoding="utf-8")
        probe.unlink()
    except OSError:
        r.skip("a vend contains only the sidecar",
               "this filesystem denies unlink, so a vend cannot be performed or "
               "cleaned up here - run on a host with normal delete semantics")
        return

    target = Path(tempfile.mkdtemp(prefix="t01-vend-"))
    out = subprocess.run(
        [sys.executable, "-m", "src.app", "cli", "tool-call", "--tool",
         "sidecar_install", "--args-json",
         json.dumps({"target": str(target), "dry_run": False, "confirm": True})],
        cwd=root, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=600,
        env={**os.environ, "SUITE_PROJECT_ROOT": str(target)},
    )
    sidecar = target / ".useful-helpers"
    r.check("the vend succeeds", sidecar.is_dir(),
            (out.stderr or out.stdout)[-200:])
    if not sidecar.is_dir():
        return

    top = {p.name for p in sidecar.iterdir()}
    leaked = sorted(top & set(MUST_NOT_SHIP))
    r.check("no development zone reached the target", not leaked, f"leaked={leaked}")

    nested = [p for p in sidecar.rglob(".useful-helpers")]
    r.check("the vend did not recurse", not nested, f"{nested[:2]}")

    # --- 5. E11: it vends blank ---------------------------------------------
    found = []
    for marker in HISTORY_MARKERS:
        hits = list(sidecar.rglob(marker))
        if hits:
            found.append(f"{marker} x{len(hits)}")
    r.check("E11 - no history of this project survives the vend", not found,
            f"found: {found}")

    r.check("no .git reached the target", not (sidecar / ".git").exists())

    # a build-machine absolute path, or a predecessor project name, in shipped text
    bleed = []
    for f in sidecar.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in {".md", ".py", ".json", ".toml", ".txt"}:
            continue
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if re.search(r"[A-Za-z]:\\\\?(Users|Jacob)\\", t) or "/sessions/" in t:
            bleed.append(f"{f.relative_to(sidecar)} (absolute path)")
        for name in PREDECESSOR_NAMES:
            if name in t.lower():
                bleed.append(f"{f.relative_to(sidecar)} ({name})")
                break
    r.check("no build-machine path or predecessor name ships", not bleed,
            f"{bleed[:4]}")

    # --- 6. the payload carries its OWN ignore file -------------------------
    gi = sidecar / ".gitignore"
    if gi.is_file():
        body = gi.read_text(encoding="utf-8", errors="replace")
        dev_only = [d for d in ("_harness", ".plans-and-parts_FOR-REFERENCE-ONLY", "gates") if d in body]
        r.check("the payload ships a minimal ignore file, not the development one",
                not dev_only, f"development rules present: {dev_only}")
    else:
        r.check("the payload ships an ignore file", False,
                "the sidecar keeps its own state; it needs its own ignore rules")

    # --- 7. the regression signal -------------------------------------------
    count = sum(1 for p in sidecar.rglob("*") if p.is_file())
    bound = int(getattr(mod, "MAX_PAYLOAD_FILES", 500))
    r.check(f"vended file count is within bound ({bound})", count <= bound,
            f"{count} files - a leak once shipped 4,009 where 275 belong")
