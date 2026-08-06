"""
FILE:       tools/stamp/cli.py
ROLE:       Generator  -  stamp a new tool/app skeleton (cli.py + tool.json) from a template.
DOMAIN:     tool
DOES:       Creates tools/<id>/ or apps/<id>/ with a cli.py already wired to tools._toolkit and
            a filled-in tool.json manifest. Refuses to overwrite an existing target.
DEPENDS ON: tools._toolkit, (stdlib) json, re, pathlib
WIRES TO:   invoked by src/core/invoke.py; writes into tools/ or apps/ (Apply authority)
NOTES:      The "tool that spits out boilerplate"  -  first Apply-authority tool. Validates `id`
            as a slug (no path traversal). Dogfooded by using it to stamp the next tool.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from tools._toolkit import tool_main

_SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_AUTHORITIES = ("Observe", "Sandbox", "Apply")

_CLI_TEMPLATE = '''"""
FILE:       __RELPATH__/cli.py
ROLE:       __SUMMARY__
DOMAIN:     __DOMAIN__
DOES:       TODO  -  implement run(args).
DEPENDS ON: tools._toolkit
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
STATUS:     SCAFFOLD
NOTES:      Generated skeleton. Implement run(args) to return a JSON-able dict; the ok/error
            envelope and --args-json parsing are provided by tools._toolkit.
"""
from __future__ import annotations

from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    raise NotImplementedError("implement __ID__: return a JSON-able dict")
'''


@tool_main
def run(args: dict) -> dict:
    tool_id = str(args.get("id", "")).strip()
    if not _SLUG.match(tool_id):
        return {"ok": False, "error": f"invalid id {tool_id!r}; use [a-z0-9][a-z0-9_-]*"}

    kind = str(args.get("kind", "tool")).lower()
    if kind not in ("tool", "app"):
        return {"ok": False, "error": f"kind must be 'tool' or 'app', got {kind!r}"}

    authority = str(args.get("authority", "Observe"))
    if authority not in _AUTHORITIES:
        return {"ok": False, "error": f"authority must be one of {_AUTHORITIES}"}

    summary = str(args.get("summary", "")).strip() or f"TODO: describe {tool_id}"
    category = str(args.get("category", "uncategorized")).strip() or "uncategorized"

    kind_dir = "tools" if kind == "tool" else "apps"
    target = Path.cwd() / kind_dir / tool_id
    if target.exists():
        return {"ok": False, "error": f"already exists: {kind_dir}/{tool_id}"}

    rel = f"{kind_dir}/{tool_id}"
    target.mkdir(parents=True, exist_ok=False)

    cli_text = (_CLI_TEMPLATE
                .replace("__RELPATH__", rel)
                .replace("__SUMMARY__", summary)
                .replace("__DOMAIN__", kind)
                .replace("__ID__", tool_id))
    (target / "cli.py").write_text(cli_text, encoding="utf-8")

    manifest = {
        "id": tool_id,
        "summary": summary,
        "category": category,
        "authority": authority,
        "invocation": {"interpreter": "${ROOT_VENV_PYTHON}", "entry": f"{rel}/cli.py"},
        "input_schema": {"type": "object", "properties": {}},
        "output_shape": {"type": "object", "properties": {"ok": {"type": "boolean"}}},
        "provenance": {"donor": "none", "treatment": "GENERATED", "note": "stamped by tools/stamp"},
    }
    (target / "tool.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    return {"tool": "stamp", "created_id": tool_id, "kind": kind,
            "created": [f"{rel}/cli.py", f"{rel}/tool.json"]}
