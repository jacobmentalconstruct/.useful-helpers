from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from . import registry, storage
from .control import ControlPlane
from .instance import InstanceError, load


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sidecar")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("tools")

    call = commands.add_parser("call")
    call.add_argument("tool_id")
    call.add_argument("--args", default="{}", help="JSON object of tool arguments")
    call.add_argument("--authority", choices=("observe", "sandbox", "apply"), default="observe")
    call.add_argument("--client", default="cli")
    call.add_argument("--timeout", type=int, default=30)
    return parser


def _emit(document: dict) -> None:
    print(json.dumps(document, indent=2, sort_keys=True))


def _status(context) -> dict:
    db_path = storage.bootstrap(context)
    connection = sqlite3.connect(db_path)
    try:
        database_uuid = connection.execute("SELECT instance_uuid FROM instances").fetchone()[0]
        database_schema = connection.execute("PRAGMA user_version").fetchone()[0]
    finally:
        connection.close()
    tool_count = len(registry.discover(context))
    return {
        "ok": True,
        "bound": True,
        "instance_uuid": context.instance_uuid,
        "instance_schema": context.schema_version,
        "database_schema": database_schema,
        "database_identity_matches": database_uuid == context.instance_uuid,
        "product_version": context.product_version,
        "target_relation": context.target_relation,
        "target_root": str(context.target_root),
        "state_database": "state/workbench.sqlite3",
        "tool_count": tool_count,
    }


def main(instance_root: str | Path, argv: list[str] | None = None) -> int:
    try:
        arguments = _parser().parse_args(argv)
        context = load(instance_root)
        if arguments.command == "status":
            response = _status(context)
        elif arguments.command == "tools":
            response = {"ok": True, "tools": ControlPlane(context).tools()}
        elif arguments.command == "call":
            try:
                tool_arguments = json.loads(arguments.args)
            except json.JSONDecodeError as exc:
                _emit({"ok": False, "error": {"code": "bad_json", "message": str(exc)}})
                return 2
            response = ControlPlane(context).invoke(
                arguments.tool_id,
                tool_arguments,
                client=arguments.client,
                authority=arguments.authority,
                timeout_seconds=arguments.timeout,
            )
        else:
            response = {"ok": False, "error": {"code": "unknown_command"}}
    except (InstanceError, storage.StorageError, registry.RegistryError) as exc:
        _emit(
            {
                "ok": False,
                "error": {"code": type(exc).__name__, "message": str(exc)},
            }
        )
        return 1

    _emit(response)
    return 0 if response.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main(Path(__file__).resolve().parents[1], sys.argv[1:]))
