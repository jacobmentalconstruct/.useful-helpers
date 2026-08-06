"""
FILE:       _harness/ro_mount.py
ROLE:       Turn the precept from DETECTION into PREVENTION - a genuinely read-only target.
DOMAIN:     harness (factory only; never ships)
DOES:       capability(): can this host mount a read-only view, and by which strategy.
            read_only(src): context manager yielding a path whose contents are `src` and whose
            filesystem physically refuses writes (EROFS).
DEPENDS ON: (stdlib) contextlib, os, platform, shutil, subprocess, tempfile
WIRES TO:   _harness/harness.py `mount` command (the M1 scored dimension).
NOTES:      Phase 4 shipped DETECTION: snapshot the target before/after an Observe call and
            report a diff. That catches a violation after it happened. This closes the other
            20% - the OS refuses the write, so a violation cannot happen at all.

            TWO STRATEGIES, both measured on this machine before shipping:
            - `bind` (privileged): `mount --bind` + `remount,ro,bind`. Mounts the REAL target,
              no copy. What CI does, where the runner has root.
            - `userns-tmpfs` (unprivileged): `unshare -rm`, tmpfs inside the namespace, copy in,
              `remount,ro`. Needed because mounts INHERITED by a user namespace are locked -
              you cannot remount them ro - but a tmpfs created inside it is yours to seal.
              Measured: plain bind+remount and unprivileged overlayfs BOTH fail in a userns.

            The honest-skip contract matters more than the feature: on Windows/macOS, or a Linux
            host with neither strategy, capability() returns available=False WITH A REASON and
            the harness reports `unavailable`. A skipped dimension must never read as a pass -
            that is the exact class of lie this project exists to eliminate.
"""
from __future__ import annotations

import contextlib
import os
import platform
import shutil
import subprocess
import tempfile

_PROBE_TIMEOUT = 60


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=_PROBE_TIMEOUT, **kw)


def _has(binary: str) -> bool:
    return shutil.which(binary) is not None


def _userns_works() -> bool:
    """Can we get a user+mount namespace where we are root? Probed, not assumed."""
    if not _has("unshare"):
        return False
    try:
        p = _run(["unshare", "-rm", "sh", "-c", "id -u"])
        return p.returncode == 0 and p.stdout.strip() == "0"
    except (OSError, subprocess.SubprocessError):
        return False


def capability() -> dict:
    """{available, strategy, reason}. Never raises; a negative answer always carries a reason."""
    system = platform.system()
    if system != "Linux":
        return {"available": False, "strategy": None,
                "reason": f"read-only bind mounts are Linux-only; this host is {system}"}
    if not _has("mount"):
        return {"available": False, "strategy": None,
                "reason": "no `mount` binary on PATH"}
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        return {"available": True, "strategy": "bind",
                "reason": "running as root: real bind mount of the target, no copy"}
    if _userns_works():
        return {"available": True, "strategy": "userns-tmpfs",
                "reason": ("unprivileged: user namespace + tmpfs (inherited mounts are locked "
                           "in a userns, so a bind cannot be remounted read-only)")}
    return {"available": False, "strategy": None,
            "reason": "not root and no usable user namespace (unshare -rm failed)"}


def _bind_script(src: str, dest: str) -> str:
    return (f"mount --bind {src!r} {dest!r} && "
            f"mount -o remount,ro,bind {dest!r}")


def _tmpfs_script(src: str, dest: str, inner: str) -> str:
    # Copy THEN seal. `cp -a` preserves the tree; the remount is what makes it a real test.
    return (f"mount -t tmpfs tmpfs {dest!r} && "
            f"cp -a {src!r}/. {dest!r}/ && "
            f"mount -o remount,ro tmpfs {dest!r} && "
            f"{inner}")


def run_under_read_only(src: str, command: str, *, strategy: str) -> dict:
    """Run `command` (sh) with $RO_TARGET pointing at a read-only view of `src`.

    The whole operation happens inside one shell because a user namespace dies with its
    process - the mount cannot outlive the `unshare` that made it, so the payload has to run
    inside. Returns {ok, returncode, stdout, stderr}.
    """
    dest = tempfile.mkdtemp(prefix="ro-target-")
    payload = f"export RO_TARGET={dest!r}; {command}"
    if strategy == "bind":
        script = _bind_script(src, dest) + f" && ( {payload} ); rc=$?; umount {dest!r}; exit $rc"
        argv = ["sh", "-c", script]
    elif strategy == "userns-tmpfs":
        script = _tmpfs_script(src, dest, f"( {payload} )")
        argv = ["unshare", "-rm", "sh", "-c", script]
    else:
        return {"ok": False, "returncode": -1, "stdout": "",
                "stderr": f"unknown strategy {strategy!r}"}
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=900)
        return {"ok": p.returncode == 0, "returncode": p.returncode,
                "stdout": p.stdout, "stderr": p.stderr}
    except (OSError, subprocess.SubprocessError) as e:
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": f"{type(e).__name__}: {e}"}
    finally:
        if strategy == "bind":
            with contextlib.suppress(OSError, subprocess.SubprocessError):
                _run(["umount", dest])
        with contextlib.suppress(OSError):
            os.rmdir(dest)


def self_test() -> dict:
    """Prove the mount is REALLY read-only before trusting any result built on it.

    A probe that assumes its own instrument works is how you ship a green light over a broken
    rig. This writes a file, seals the mount, and demands the write fail with EROFS.
    """
    cap = capability()
    if not cap["available"]:
        return {"tested": False, **cap}
    src = tempfile.mkdtemp(prefix="ro-src-")
    try:
        with open(os.path.join(src, "canary.txt"), "w", encoding="utf-8") as fh:
            fh.write("readable")
        cmd = ('cat "$RO_TARGET/canary.txt" >/dev/null 2>&1 && echo READ_OK; '
               'if echo x > "$RO_TARGET/violation" 2>/dev/null; then echo WRITE_ALLOWED; '
               'else echo WRITE_REFUSED; fi')
        r = run_under_read_only(src, cmd, strategy=cap["strategy"])
        out = r["stdout"]
        sealed = "WRITE_REFUSED" in out and "WRITE_ALLOWED" not in out
        readable = "READ_OK" in out
        return {"tested": True, "strategy": cap["strategy"], "reason": cap["reason"],
                "readable": readable, "write_refused": sealed,
                "ok": bool(sealed and readable), "raw": out.strip(),
                "stderr": r["stderr"].strip()[:400]}
    finally:
        shutil.rmtree(src, ignore_errors=True)
