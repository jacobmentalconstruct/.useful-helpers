"""
FILE:       src/interfaces/cli.py
ROLE:       CLI entrance  -  one-shot subcommand dispatch for humans and scripts.
DOMAIN:     interface
DOES:       version | tool-list | registry-refresh | tool-call --tool <id>
            (--args-json <json> | --args-file <path|->). Maps onto core.registry /
            core.invoke; prints structured JSON to stdout. --args-file/- (stdin) is the
            reliable route for programmatic callers (no shell-escaping of nested JSON).
DEPENDS ON: src.core.registry, src.core.invoke, src.lib.common
WIRES TO:   core.registry, core.invoke
NOTES:      Every reusable surface must be reachable from the CLI, not only the GUI/MCP.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from src.core import docs as docs_mod
from src.core import invoke as invoke_mod
from src.core import playbook, registry
from src.core.config import Paths
from src.lib.common import safe_json_dumps

VERSION = "0.1.0"


def _print(obj) -> None:
    print(safe_json_dumps(obj, indent=2))


def dispatch(paths: Paths, argv: list[str]) -> int:
    """Map argv to a subcommand and run it."""
    if not argv or argv[0] in ("version", "--version", "-v"):
        _print({"suite": "usefulhelpers", "version": VERSION})
        return 0

    cmd, rest = argv[0], argv[1:]

    if cmd == "tool-list":
        tools = [asdict(t) for t in registry.list_tools(paths)]
        _print({"count": len(tools), "tools": tools})
        return 0

    if cmd == "registry-refresh":
        manifest = registry.generate_manifest(paths)
        _print({"ok": True, "count": manifest["count"], "written": "config/registry.json"})
        return 0

    if cmd == "docs-refresh":
        report = docs_mod.generate_tools_md(paths)
        _print({"ok": True, **report})
        return 0

    if cmd == "tool-call":
        opts = _parse_opts(rest)
        tool_id = opts.get("tool")
        if not tool_id:
            _print({"ok": False, "error": "tool-call requires --tool <id>"})
            return 2
        args = _load_call_args(opts)
        if isinstance(args, tuple):  # (error dict,) passthrough
            _print(args[0])
            return 2
        result = invoke_mod.invoke(paths, tool_id, args)
        _print(asdict(result))
        return 0 if result.ok else 1

    if cmd == "run-playbook":
        opts = _parse_opts(rest)
        steps = _load_playbook_steps(opts)
        if steps is None:
            _print({"ok": False, "error": "run-playbook needs --file <path> or --playbook-json '<json>'"})
            return 2
        if isinstance(steps, dict):  # error passthrough
            _print(steps)
            return 2
        report = playbook.run_playbook(paths, steps,
                                       stop_on_error=(opts.get("continue-on-error") != "true"))
        _print(report)
        return 0 if report["ok"] else 1

    _print({"ok": False, "error": f"unknown subcommand: {cmd}",
            "available": ["version", "tool-list", "registry-refresh", "docs-refresh",
                          "tool-call", "run-playbook"]})
    return 2


def _load_call_args(opts: dict):
    """Resolve tool-call args from --args-file <path|-> (file or stdin; the reliable route for
    programmatic callers  -  no shell-escaping of nested JSON, field report F0) or --args-json.
    Returns the args dict, or a 1-tuple wrapping an error dict."""
    import sys
    src = opts.get("args-file")
    if src and opts.get("args-json"):
        return ({"ok": False, "error": "use --args-json OR --args-file, not both"},)
    try:
        if src == "-":
            raw = sys.stdin.read()
        elif src:
            raw = Path(src).read_text(encoding="utf-8")
        else:
            raw = opts.get("args-json", "{}")
        args = json.loads(raw or "{}")
    except (OSError, json.JSONDecodeError) as e:
        which = "--args-file" if src else "--args-json"
        return ({"ok": False, "error": f"invalid {which}: {e}"},)
    if not isinstance(args, dict):
        return ({"ok": False, "error": "args must be a JSON object"},)
    return args


def _load_playbook_steps(opts: dict):
    """Return a steps list, None (no source given), or an error dict."""
    if opts.get("file"):
        try:
            raw = json.loads(Path(opts["file"]).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            return {"ok": False, "error": f"cannot read playbook file: {e}"}
    elif opts.get("playbook-json"):
        try:
            raw = json.loads(opts["playbook-json"])
        except json.JSONDecodeError as e:
            return {"ok": False, "error": f"bad --playbook-json: {e}"}
    else:
        return None
    steps = raw.get("steps") if isinstance(raw, dict) else raw
    if not isinstance(steps, list):
        return {"ok": False, "error": "playbook must be a list of steps or {steps:[...]}"}
    return steps


def _parse_opts(rest: list[str]) -> dict:
    """Minimal --key value parser (keys stored without leading --)."""
    opts: dict = {}
    i = 0
    while i < len(rest):
        token = rest[i]
        if token.startswith("--"):
            key = token[2:]
            if i + 1 < len(rest) and not rest[i + 1].startswith("--"):
                opts[key] = rest[i + 1]
                i += 2
            else:
                opts[key] = "true"
                i += 1
        else:
            i += 1
    return opts
