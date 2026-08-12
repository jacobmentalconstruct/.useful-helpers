"""
FILE:       tools/_toolkit.py
ROLE:       Shared tool runtime  -  the ONE place the --args-json + JSON-envelope boilerplate lives.
DOMAIN:     tool (shared substrate)
DOES:       tool_main: decorate a run(args:dict)->dict. When the tool module is the entrypoint,
            parse --args-json, call run, print a JSON envelope ({"ok":true, ...} or
            {"ok":false,"error":...}), and exit with the right code. When imported (e.g. by a
            test), return run unchanged so it can be called directly.
DEPENDS ON: (stdlib) argparse, inspect, json, sys
WIRES TO:   used by tools/*/cli.py and apps/*/cli.py; executed by src/core/invoke.py
NOTES:      Fix the envelope here once -> every tool inherits it (anti-duplication;
            token-saving substrate). Tools stay subprocess-invoked; this is an in-project shared
            lib (tools -> tools._toolkit), not a cross-reservoir dependency.
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Callable


def _normalize_apply(args: dict) -> dict:
    """THE universal Apply confirmation (field report F1): `apply: true` executes for real on
    every gated Apply tool, whatever its historical flag was. Normalized here ONCE  -  the
    envelope every tool passes through  -  so each tool's legacy gate (`confirm`, `write`,
    `dry_run`) keeps working untouched and future tools inherit the convention for free.
    No `apply` key -> args pass through unchanged."""
    if args.get("apply"):
        args = dict(args)
        args["dry_run"] = False
        args["confirm"] = True
        args["write"] = True
    return args


def _hint_apply(result: dict) -> dict:
    """Preview/refusal responses state the exact flag that executes for real (F1: no more
    guessing which of confirm/write/dry_run a tool wants)."""
    is_preview = result.get("dry_run") is True or result.get("written") is False
    refused = (not result.get("ok", True)
               and any(k in str(result.get("error", "")) for k in ("confirm", "write", "dry_run")))
    if is_preview or refused:
        result.setdefault("apply_with", {"apply": True})
    return result


def confirmed(args: dict, legacy: tuple = ("confirm", "write")) -> bool:
    """For NEW tools: one confirmation check honoring the universal `apply` flag and the
    tool's legacy flag(s). Existing tools need no change  -  run_cli normalizes `apply` into
    the legacy flags before they see the args."""
    return bool(args.get("apply")) or any(bool(args.get(k)) for k in legacy)


def apply_with() -> dict:
    """The standard preview fragment: `{"apply": true}`  -  what a caller passes to execute."""
    return {"apply": True}


def run_cli(run: Callable[[dict], dict], argv: list[str]) -> int:
    """Parse --args-json, call run(args), print the JSON envelope, return an exit code."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--args-json", default="{}")
    ns = parser.parse_args(argv)
    try:
        args = json.loads(ns.args_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"bad --args-json: {e}"}))
        return 2
    if not isinstance(args, dict):
        print(json.dumps({"ok": False, "error": "args must be a JSON object"}))
        return 2
    try:
        result = run(_normalize_apply(args)) or {}
    except Exception as e:  # tool logic must not leak a traceback to the seam
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}))
        return 1
    if not isinstance(result, dict):
        result = {"value": result}
    if "ok" not in result:
        result = {"ok": True, **result}
    result = _hint_apply(result)
    print(json.dumps(result))
    # A produced result (ok true OR false) is a successful invocation  -  exit 0 and let the
    # caller read business success from result["ok"]. Only envelope errors above exit non-zero
    # (bad --args-json -> 2, unhandled exception -> 1), so structured payloads are never lost.
    return 0


def tool_main(run: Callable[[dict], dict]) -> Callable[[dict], dict]:
    """Decorator. If the defining module is the entrypoint, run it as a CLI and exit; otherwise
    return `run` unchanged so tests/other code can import and call it directly."""
    caller_globals = inspect.stack()[1].frame.f_globals
    if caller_globals.get("__name__") == "__main__":
        sys.exit(run_cli(run, sys.argv[1:]))
    return run


# --- THE ROOTS CONTRACT (shared API  -  no tool re-derives these ad hoc) -----------------
# FOUR distinct roots exist the moment the toolkit is installed as a sidecar:
#   * WORK TARGET  (project_root)   -  the project the tools operate ON. The invoke() seam runs
#     every tool with cwd = work target, so relative inputs default to the project.
#   * TOOLKIT HOME (suite_home)     -  where the instrument LIVES: its code, config, registry.
#   * STATE ROOT   (state_root)     -  where DURABLE MEMORY lives: journal, evidence, the event
#     log, the workbench. Survives an update-in-place; a clean must never touch it.
#   * OUTPUT ROOT  (output_root)    -  where DISPOSABLE artifacts default. Safe to delete.
# THE RULE: inputs read from the work target; state and generated output write to the toolkit
# home; an explicit path argument always overrides. Standalone (no sidecar) the work target and
# toolkit home coincide, so behavior is unchanged. Each tool.json declares
# `operates_on: project|toolkit`.
# Enforced end-to-end by tests/test_smoke.py::test_sidecar_conditions.
#
# WHY state_root is separate from output_root: they have opposite lifecycles. Artifacts are
# regenerable exhaust; state is the memory that makes the next agent's session continuous. They
# were conflated (state lived under `_docs/_AppJOURNAL/`  -  a database inside the docs folder),
# which meant every consumer hardcoded that path independently, and `attach` had to enumerate
# six locations to answer "did the target change, or was that just me breathing?".


class MissingRuntimeContext(RuntimeError):
    """This tool was launched outside the governed seam, so it has no context.

    Deliberately fatal. The predecessor of this module fell back to cwd, to a
    basename, and to a hardcoded `.useful-helpers`, which meant a tool run from the
    wrong directory silently operated on the wrong tree and reported success. Failing
    clearly is worth more than a convenient direct invocation.
    """


def _required(name: str) -> Path:
    """Read one TRANSPORTED root. Transport, never inference.

    `invoke()` resolves the InstanceContext once and exports it. This reads what it
    was given. It does not consult cwd, the folder name, or a default - if the value
    is absent the caller is outside the supported execution architecture and should
    be told so.
    """
    raw = os.environ.get(name)
    if not raw or not raw.strip():
        raise MissingRuntimeContext(
            f"{name} was not supplied. Useful Helpers tools receive their canonical "
            "instance and target roots from the governed seam; invoke this capability "
            "through the registered seam (`python -m src.app cli tool-call ...`) or, "
            "in a test, populate the runtime context explicitly.")
    return Path(raw).resolve()


def project_root() -> Path:
    """The WORK TARGET, as resolved by the runtime and transported to this process."""
    return _required("SUITE_PROJECT_ROOT")


def instance_root() -> Path:
    """This sidecar's own home (INSTANCE_ROOT), as transported.

    Replaces `toolkit_home_names()`, which returned a set of NAMES seeded with a
    hardcoded `.useful-helpers`. A name is not an identity: rename the installed
    folder and a name-based exclusion silently stops excluding the sidecar, so a
    project scan starts reporting the sidecar's own internals as target content.
    """
    return _required("SUITE_HOME")


def output_root() -> Path:
    """Where DISPOSABLE generated artifacts default: the toolkit home's _artifacts/. Explicit
    destination args override (a caller may deliberately write into the project).

    Everything under here is regenerable exhaust  -  `artifact_cleaner` may delete it freely.
    Durable memory does NOT live here; see state_root()."""
    return suite_home() / "_artifacts"


def state_root() -> Path:
    """Where DURABLE MEMORY lives: journal, evidence, the event log, the workbench.

    The state root is the toolkit's memory of this engagement. Unlike output_root it is NOT
    disposable: an update-in-place must preserve it, and a clean must never touch it. That
    lifecycle difference is the whole reason it is its own root.

    Overridable via SUITE_STATE_ROOT (tests isolate with it; it also lets an operator park
    memory outside the sidecar so a re-vend cannot lose it)."""
    override = os.environ.get("SUITE_STATE_ROOT")
    return Path(override).resolve() if override else suite_home() / "_state"


def suite_home() -> Path:
    """The instance's own home, where state and generated artifacts live so the target
    stays free of sidecar output. Alias of instance_root(), kept for the many call
    sites that read naturally as "the toolkit's home"."""
    return instance_root()


def is_instance_path(path: "Path | str") -> bool:
    """Is this path the sidecar's own home, or inside it?

    PATH-based, deliberately. `toolkit_home_names()` returned a set of directory
    NAMES, so a walker pruned anything called `.useful-helpers` anywhere in the tree
    - wrong twice over. It missed the real sidecar when the installed folder had been
    renamed, and it pruned unrelated target content that happened to share the name.

    The instance root is authoritative about which subtree is the sidecar.
    """
    try:
        here = Path(path).resolve()
        root = instance_root()
    except (MissingRuntimeContext, OSError):
        return False
    return here == root or root in here.parents


def excluded_from_target_view() -> set[Path]:
    """Absolute paths inside the target that belong to the SIDECAR, not the project.

    Returned as resolved PATHS, not names. That distinction is the whole point: a
    name-based exclusion stops working the moment the installed folder is renamed,
    and a project scan then reports the sidecar's own files as target content. The
    instance root is authoritative about which subtree is the sidecar.
    """
    return {instance_root()}


def attach_evidence(summary: str, body: str, kind: str = "tool_output") -> "str | None":
    """Best-effort: record a result in the Bag of Evidence and return its id.

    Shared so tools that produce citable output (project_run, web_search, ...) ground it the same
    way instead of each re-implementing the sibling call. Never raises  -  the seam has already
    audit-logged the invocation, so evidence is an enrichment, not a dependency."""
    import json as _json
    import subprocess as _sp
    import sys as _sys
    try:
        cli = suite_home() / "tools" / "evidence" / "cli.py"
        if not cli.is_file():
            return None
        proc = _sp.run(
            [_sys.executable, str(cli), "--args-json",
             _json.dumps({"action": "attach", "kind": kind,
                          "summary": str(summary)[:200], "body": str(body)})],
            capture_output=True, text=True, encoding="utf-8", timeout=30)
        return _json.loads(proc.stdout).get("evidence_id")
    except Exception:
        return None


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_within_roots(raw: str, *, base: Path | None = None) -> "tuple[Path | None, str]":
    """Resolve a user-supplied path against the work target (the default base) and confirm it
    stays within the work target OR the toolkit home. Blocks escapes so the sidecar cannot be
    turned into a reader/writer of arbitrary host files  -  a governance boundary the file/exec
    'hands' (read_file/write_file/glob/fs_op) all share. Returns (path, "") or (None, error)."""
    raw = str(raw or "").strip()
    if not raw:
        return None, "path is required"
    base = (base or project_root()).resolve()
    p = Path(raw)
    p = (base / p).resolve() if not p.is_absolute() else p.resolve()
    for root in (project_root().resolve(), suite_home().resolve()):
        if p == root or _is_within(p, root):
            return p, ""
    return None, f"path escapes the work target and toolkit home: {p}"


def first_json_object(text: str) -> "dict | None":
    """Pull the first balanced {...} object out of free text - models wrap JSON in prose or fences.
    String-aware: braces inside quoted strings do not affect nesting. Returns the parsed dict or
    None. Shared by the orchestrators that read model output (delegate, plan)."""
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    return None


def seam_call(tool: str, args: dict, *, timeout: int = 120) -> dict:
    """Invoke ANOTHER tool through the governed CLI, from within a tool. Returns
    {ok, output, error}. Tools never import each other (a tool is a subprocess, not a library);
    this is the sanctioned way for one tool to COMPOSE another - the nested call still passes
    through the seam, so it is authority-checked and audit-logged like any other. Used by the
    orchestrators (delegate, genesis, plan). Degrades to ok:False on any subprocess/parse error."""
    import subprocess

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "src.app", "cli", "tool-call", "--tool", tool,
             "--args-json", json.dumps(args)],
            cwd=str(suite_home()), capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout)
        env = json.loads(proc.stdout)
        return {"ok": bool(env.get("ok")), "output": env.get("output"), "error": env.get("error")}
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError) as e:
        return {"ok": False, "output": None, "error": f"{type(e).__name__}: {e}"}
