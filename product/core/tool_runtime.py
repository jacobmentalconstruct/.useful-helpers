from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class ToolContext:
    instance_root: Path
    target_root: Path
    state_root: Path
    instance_uuid: str

    @classmethod
    def from_document(cls, document: object) -> "ToolContext":
        if not isinstance(document, dict):
            raise ValueError("tool context must be an object")
        required = ("instance_root", "target_root", "state_root", "instance_uuid")
        if any(not isinstance(document.get(name), str) for name in required):
            raise ValueError("tool context is incomplete")
        return cls(
            instance_root=Path(document["instance_root"]),
            target_root=Path(document["target_root"]),
            state_root=Path(document["state_root"]),
            instance_uuid=document["instance_uuid"],
        )

    def target_relative(self, path: str | Path) -> str:
        return Path(path).resolve(strict=False).relative_to(self.target_root.resolve()).as_posix()

    def is_instance_path(self, path: str | Path) -> bool:
        candidate = Path(path).resolve(strict=False)
        root = self.instance_root.resolve()
        try:
            candidate.relative_to(root)
            return True
        except ValueError:
            return False


def run_tool(function: Callable[[dict, ToolContext], dict]) -> int:
    """Read one JSON request from stdin and emit exactly one JSON result object."""
    try:
        request = json.loads(sys.stdin.read())
        if not isinstance(request, dict) or not isinstance(request.get("args"), dict):
            raise ValueError("request must contain an args object")
        context = ToolContext.from_document(request.get("context"))
        result = function(request["args"], context)
        if not isinstance(result, dict):
            raise TypeError("tool function must return an object")
        if "ok" not in result:
            result = {"ok": True, **result}
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "error_kind": "tool_exception",
                },
                sort_keys=True,
            )
        )
        return 1
