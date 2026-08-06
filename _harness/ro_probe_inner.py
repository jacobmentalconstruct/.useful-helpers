"""
FILE:       _harness/ro_probe_inner.py
ROLE:       The payload that runs INSIDE the read-only mount namespace and reports what happened.
DOMAIN:     harness (factory only; never ships)
DOES:       Given a writable sidecar and $RO_TARGET (a read-only view of the work target):
            (1) confirm a violating Observe tool is PREVENTED, not merely detected;
            (2) confirm legitimate Observe tools still WORK against a target they cannot write.
DEPENDS ON: (stdlib) json, os, subprocess, sys
WIRES TO:   invoked by _harness/ro_mount.run_under_read_only, driven by harness.py `mount`.
NOTES:      This runs as a separate process because a user namespace dies with the process that
            created it - the mount cannot outlive `unshare`, so the whole measurement has to
            happen inside. Prints ONE json object on stdout; the parent parses it.

            Check (2) is the half that is easy to forget and the half that matters most. A
            read-only mount that PREVENTS violations but also breaks the toolkit has proven
            nothing worth having. Together the two checks are the real statement of the roots
            contract: the sidecar reads the target, writes only its own home, and the OS - not
            the author's discipline - is what enforces it.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

EVIL_TOOL = "_harness_ro_violator"
EVIL_MARK = "_HARNESS_RO_VIOLATION.txt"


def call(sidecar: str, target: str, tool: str, args: dict, timeout: int = 180) -> dict:
    env = dict(os.environ, SUITE_PROJECT_ROOT=target)
    argf = os.path.join(sidecar, "_ro_args.json")
    with open(argf, "w", encoding="utf-8") as fh:
        json.dump(args, fh)
    try:
        p = subprocess.run(
            [sys.executable, "-m", "src.app", "cli", "tool-call", "--tool", tool,
             "--args-file", argf],
            cwd=sidecar, capture_output=True, text=True, timeout=timeout, env=env)
        try:
            env_out = json.loads(p.stdout)
        except ValueError:
            return {"ok": False, "error": (p.stderr or p.stdout)[:300], "output": {}}
        return {"ok": bool(env_out.get("ok")), "error": env_out.get("error"),
                "output": env_out.get("output") or {}}
    except (OSError, subprocess.SubprocessError) as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "output": {}}
    finally:
        try:
            os.unlink(argf)
        except OSError:
            pass


def plant_violator(sidecar: str) -> None:
    tdir = os.path.join(sidecar, "tools", EVIL_TOOL)
    os.makedirs(tdir, exist_ok=True)
    with open(os.path.join(tdir, "tool.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "id": EVIL_TOOL, "summary": "harness M1 probe (tries to write the target)",
            "category": "introspection", "authority": "Observe", "operates_on": "project",
            "invocation": {"interpreter": "${ROOT_VENV_PYTHON}",
                           "entry": f"tools/{EVIL_TOOL}/cli.py"},
            "input_schema": {"type": "object", "properties": {}},
        }, fh)
    with open(os.path.join(tdir, "cli.py"), "w", encoding="utf-8") as fh:
        fh.write(
            "from __future__ import annotations\n"
            "from pathlib import Path\n"
            "from tools._toolkit import tool_main\n\n\n"
            "@tool_main\n"
            "def run(args: dict) -> dict:\n"
            "    # An Observe tool has no business writing the target. Try anyway.\n"
            f"    Path({EVIL_MARK!r}).write_text('i should not exist', encoding='utf-8')\n"
            "    return {'ok': True, 'did': 'wrote to the target'}\n")


def main() -> int:
    sidecar = sys.argv[1]
    target = os.environ.get("RO_TARGET") or ""
    result: dict = {"target": target, "sidecar": sidecar}

    # The mount must actually be sealed, independently of anything the toolkit does.
    try:
        with open(os.path.join(target, "_direct_write_probe"), "w", encoding="utf-8") as fh:
            fh.write("x")
        result["mount_sealed"] = False
        result["mount_note"] = "a plain open(w) SUCCEEDED - the mount is not read-only"
    except OSError as e:
        result["mount_sealed"] = True
        result["mount_errno"] = getattr(e, "errno", None)
        result["mount_note"] = str(e)[:200]

    plant_violator(sidecar)
    subprocess.run([sys.executable, "-m", "src.app", "cli", "registry-refresh"],
                   cwd=sidecar, capture_output=True, text=True)

    # (1) PREVENTION: the violating Observe tool must fail, and the file must never appear.
    v = call(sidecar, target, EVIL_TOOL, {})
    mark = os.path.join(target, EVIL_MARK)
    result["violation_call_ok"] = v["ok"]
    result["violation_error"] = (v.get("error") or "")[:300]
    result["violation_file_exists"] = os.path.exists(mark)
    result["prevented"] = (not v["ok"]) and (not os.path.exists(mark))

    # (2) STILL USABLE: legitimate Observe work must succeed against a target it cannot write.
    usable = {}
    a = call(sidecar, target, "attach", {"refresh": True})
    usable["attach"] = {"ok": a["ok"],
                        "domain": ((a.get("output") or {}).get("project_map") or {}).get("domain"),
                        "error": (a.get("error") or "")[:200]}
    g = call(sidecar, target, "glob", {"pattern": "**/*"})
    usable["glob"] = {"ok": g["ok"], "count": (g.get("output") or {}).get("count"),
                      "error": (g.get("error") or "")[:200]}
    s = call(sidecar, target, "repo_search", {"query": "def ", "root": "."})
    usable["repo_search"] = {"ok": s["ok"], "error": (s.get("error") or "")[:200]}
    r = call(sidecar, target, "report", {"path": "."})
    usable["report"] = {"ok": r["ok"], "error": (r.get("error") or "")[:200]}
    result["usable"] = usable
    result["still_usable"] = all(v["ok"] for v in usable.values())

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
