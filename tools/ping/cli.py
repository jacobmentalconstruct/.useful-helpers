"""
FILE:       tools/ping/cli.py
ROLE:       Proof tool  -  echoes input and reports the runtime the seam invoked it under.
DOMAIN:     tool
DOES:       Returns the echoed message plus python version, platform, and cwd.
DEPENDS ON: tools._toolkit, (stdlib) os, platform
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      The end-to-end proof for the spine. Envelope (ok/error, --args-json) comes from
            tools._toolkit  -  this file is now pure logic.
"""
from __future__ import annotations

import os
import platform

from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    return {
        "tool": "ping",
        "echo": args.get("message", ""),
        "python": platform.python_version(),
        "platform": platform.system(),
        "cwd": os.getcwd(),
    }
