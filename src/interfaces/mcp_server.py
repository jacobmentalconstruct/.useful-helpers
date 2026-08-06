"""
FILE:       src/interfaces/mcp_server.py
ROLE:       Agent entrance  -  MCP JSON-RPC 2.0 server over stdio.
DOMAIN:     interface
DOES:       initialize / tools/list / tools/call / ping. tools/list reads the registry;
            tools/call routes through core.invoke(). Newline-delimited JSON on stdin/stdout.
DEPENDS ON: src.core.registry, src.core.invoke, src.lib.{common,logging_setup}
WIRES TO:   driven by an external MCP client; dispatches into core.invoke()
NOTES:      Lean JSON-RPC 2.0 stdio server: tools/list + tools/call only. Takes native
            JSON, so it sidesteps shell-escaping entirely  -  this is the entrance
            programmatic callers should use.

"""
from __future__ import annotations

import json
import sys

from src.core import invoke as invoke_mod
from src.core import registry
from src.core.config import Paths
from src.core.playbook import run_playbook
from src.lib.common import safe_json_dumps
from src.lib.logging_setup import get_logger

log = get_logger("interfaces.mcp")

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "usefulhelpers-suite"
SERVER_VERSION = "0.1.0"


class MCPHandler:
    """Stateless JSON-RPC 2.0 dispatcher. Testable without stdio."""

    def __init__(self, paths: Paths):
        self._paths = paths

    def handle_message(self, message: dict) -> "dict | None":
        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params") or {}
        is_notification = msg_id is None
        try:
            result = self._dispatch(method, params)
        except _MCPError as e:
            if is_notification:
                return None
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": e.code, "message": e.message}}
        except Exception as e:  # defensive: never crash the loop
            log.exception("MCP unexpected error in %s", method)
            if is_notification:
                return None
            return {"jsonrpc": "2.0", "id": msg_id,
                    "error": {"code": -32603, "message": f"internal: {type(e).__name__}: {e}"}}
        if is_notification:
            return None
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def _dispatch(self, method: str, params: dict) -> dict:
        if method == "initialize":
            return self._initialize()
        if method in ("initialized", "notifications/initialized", "ping"):
            return {}
        if method == "tools/list":
            return self._tools_list()
        if method == "tools/call":
            return self._tools_call(params)
        if method == "playbook/run":
            return self._playbook_run(params)
        raise _MCPError(-32601, f"method not found: {method}")

    def _initialize(self) -> dict:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "instructions": "Suite control plane. Use tools/list then tools/call; every call "
                            "routes through the invoke() seam and is logged.",
        }

    def _tools_list(self) -> dict:
        tools = []
        for t in registry.list_tools(self._paths):
            tools.append({
                "name": t.id,
                "description": t.summary,
                "inputSchema": t.input_schema or {"type": "object"},
                "_meta": {"category": t.category, "authority": t.authority},
            })
        return {"tools": tools}

    def _tools_call(self, params: dict) -> dict:
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not name:
            raise _MCPError(-32602, "tools/call requires 'name'")
        result = invoke_mod.invoke(self._paths, name, arguments)
        if not result.ok:
            return {"isError": True, "content": [{"type": "text", "text": result.error or "tool failed"}]}
        return {
            "isError": False,
            "content": [{"type": "text", "text": safe_json_dumps(result.output, indent=2)}],
            "_meta": {"tool_id": result.tool_id, "exit_code": result.exit_code},
        }

    def _playbook_run(self, params: dict) -> dict:
        steps = params.get("steps")
        if not isinstance(steps, list):
            raise _MCPError(-32602, "playbook/run requires 'steps' (a list)")
        return run_playbook(self._paths, steps, stop_on_error=bool(params.get("stopOnError", True)))


class _MCPError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def serve_stdio(paths: Paths) -> int:
    """Newline-delimited JSON-RPC 2.0 loop on stdin/stdout."""
    handler = MCPHandler(paths)
    log.info("MCP stdio server starting: %s v%s", SERVER_NAME, SERVER_VERSION)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as e:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None,
                             "error": {"code": -32700, "message": f"parse error: {e}"}}) + "\n")
            sys.stdout.flush()
            continue
        response = handler.handle_message(message)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    log.info("MCP stdio server exiting")
    return 0
