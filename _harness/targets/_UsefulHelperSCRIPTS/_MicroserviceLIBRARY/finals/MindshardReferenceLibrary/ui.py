from __future__ import annotations

from typing import Any, Dict


def run_headless(runtime) -> Dict[str, Any]:
    return {"app": "MindshardReferenceLibrary", "mode": "headless", "health": runtime.health()}


def launch_ui(runtime) -> None:
    raise RuntimeError("MindshardReferenceLibrary is packaged as a headless vendored tool. Use app.py --no-ui or mcp_server.py.")
