"""
FILE:       tools/dep_install/cli.py
ROLE:       Governed dependency install behind an HITL BATCH gate (the sidecar's pip).
DOMAIN:     tool
DOES:       Resolve the COMPLETE dependency set (explicit packages + requirements.txt +
            pyproject [project].dependencies), report it as ONE list with its sources and the
            target venv, and install the WHOLE batch on a single apply. Never one prompt per dep.
DEPENDS ON: tools._toolkit, (stdlib) subprocess, sys, tomllib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
NOTES:      Installs into the TARGET's own venv  -  that is what actually revives a project, and a
            virtualenv is regenerable ENVIRONMENT, not project content (both precept measures
            already skip-list .venv/venv). Rails: never the system/global interpreter, the venv is
            confined to the roots, and a missing venv is only created with create_venv:true.
"""
from __future__ import annotations

import os
import subprocess
import sys

from tools._toolkit import apply_with, confirmed, project_root, resolve_within_roots, tool_main

_TIMEOUT = 600


def _venv_python(venv):
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _from_requirements(path, seen=None, unresolved=None, depth=0):
    """Specs from a requirements file, EXPANDING nested `-r`/`--requirement` includes.

    The batch gate promises one COMPLETE list to approve, so a `-r base.txt` must be followed  -
    silently dropping its packages would have the operator approve a list that isn't the truth.
    Anything we genuinely cannot expand (`-e .`, `--index-url`, ...) is returned in `unresolved`
    and surfaced in the plan, so the gap is visible rather than hidden.
    """
    out: list[tuple[str, str]] = []
    seen = seen if seen is not None else set()
    unresolved = unresolved if unresolved is not None else []
    if not path.is_file() or depth > 5:
        return out, unresolved
    key = str(path.resolve())
    if key in seen:  # cycle guard
        return out, unresolved
    seen.add(key)

    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith(("-r ", "--requirement ", "-r=", "--requirement=")):
            ref = line.split("=", 1)[1] if "=" in line.split(None, 1)[0] else line.split(None, 1)[1]
            nested, err = resolve_within_roots(ref.strip(), base=path.parent)
            if err or not nested.is_file():
                unresolved.append({"directive": line, "in": path.name,
                                   "reason": err or "file not found"})
                continue
            sub, _ = _from_requirements(nested, seen, unresolved, depth + 1)
            out.extend(sub)
            continue
        if line.startswith("-"):
            unresolved.append({"directive": line, "in": path.name,
                               "reason": "not expandable (pass it explicitly if needed)"})
            continue
        out.append((line, path.name))
    return out, unresolved


def _from_pyproject(path) -> list[tuple[str, str]]:
    if not path.is_file():
        return []
    try:
        import tomllib
    except ModuleNotFoundError:
        return []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    deps = ((data.get("project") or {}).get("dependencies")) or []
    return [(str(d), path.name) for d in deps if str(d).strip()]


@tool_main
def run(args: dict) -> dict:
    root = project_root()
    # ---- resolve the COMPLETE set (this is the list the operator says yes to, once) ----
    resolved: list[tuple[str, str]] = [(str(p), "explicit") for p in (args.get("packages") or [])]
    unresolved: list[dict] = []
    if args.get("requirements"):
        req, err = resolve_within_roots(args["requirements"])
        if err:
            return {"ok": False, "error": err}
        specs, unresolved = _from_requirements(req)
        resolved += specs
    else:
        specs, unresolved = _from_requirements(root / "requirements.txt")
        resolved += specs
        resolved += _from_pyproject(root / "pyproject.toml")

    seen, packages = set(), []
    for spec, source in resolved:
        if spec not in seen:
            seen.add(spec)
            packages.append({"package": spec, "source": source})
    if not packages:
        return {"ok": False, "error": "no dependencies found (no packages, requirements.txt, "
                                      "or pyproject [project].dependencies)"}

    # ---- resolve the venv (never the system interpreter) ----
    venv, err = resolve_within_roots(args.get("venv") or ".venv")
    if err:
        return {"ok": False, "error": err}
    venv_exists = _venv_python(venv).is_file()
    create_venv = bool(args.get("create_venv"))

    plan = {
        "tool": "dep_install",
        "venv": venv.as_posix(),
        "venv_exists": venv_exists,
        "would_create_venv": (not venv_exists) and create_venv,
        "count": len(packages),
        "packages": packages,
    }
    if unresolved:
        # Visible, never silent: the operator sees exactly what the list could NOT account for.
        plan["unresolved"] = unresolved
        plan["unresolved_note"] = ("these requirement directives were not expanded; the package "
                                   "list above may be incomplete")
    if not venv_exists and not create_venv:
        return {**plan, "ok": False,
                "error": f"no virtualenv at {venv.as_posix()}: pass create_venv:true to make one "
                         f"(refusing to install into the system interpreter)"}

    if not confirmed(args):
        return {**plan, "dry_run": True, "installed": False, "apply_with": apply_with()}

    # ---- one batch, one command ----
    if not venv_exists:
        made = subprocess.run([sys.executable, "-m", "venv", str(venv)],
                              capture_output=True, text=True, timeout=_TIMEOUT)
        if made.returncode != 0:
            return {**plan, "ok": False, "installed": False,
                    "error": f"could not create venv: {(made.stderr or '').strip()[:400]}"}
    cmd = [str(_venv_python(venv)), "-m", "pip", "install", "--no-input",
           *[p["package"] for p in packages]]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {**plan, "ok": False, "installed": False, "error": f"timeout after {_TIMEOUT}s"}
    return {**plan, "dry_run": False, "ok": proc.returncode == 0,
            "installed": proc.returncode == 0, "exit_code": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-4000:], "stderr_tail": (proc.stderr or "")[-4000:]}
