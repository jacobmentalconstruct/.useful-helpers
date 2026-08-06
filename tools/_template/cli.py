"""
FILE:       tools/_template/cli.py
ROLE:       Exemplar headless tool  -  the shape `tools/stamp` generates.
DOMAIN:     tool
DOES:       Implements run(args)->dict; the --args-json parsing and ok/error envelope come from
            tools._toolkit, so a tool is just its logic.
DEPENDS ON: tools._toolkit
WIRES TO:   invoked as a subprocess by src/core/invoke.py; described by sibling tool.json
STATUS:     SCAFFOLD
NOTES:      Prefer `tools/stamp` to create a new tool rather than copying this by hand. The
            invoke() seam runs `<interpreter> cli.py --args-json <json>` with the project root
            on PYTHONPATH, so the `tools._toolkit` import resolves. See tools/ping for a minimal
            reference and tools/host_probe for a fuller one.
"""
from __future__ import annotations

from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    raise NotImplementedError("per-tool tranche: return a JSON-able dict")
