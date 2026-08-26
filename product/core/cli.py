from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from . import app_journal, registry, runtime_records, storage
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

    receipts = commands.add_parser("receipts")
    receipt_commands = receipts.add_subparsers(dest="receipt_command", required=True)
    receipt_list = receipt_commands.add_parser("list")
    receipt_list.add_argument("--limit", type=int, default=50)
    receipt_read = receipt_commands.add_parser("read")
    receipt_read.add_argument("receipt_id")

    artifacts = commands.add_parser("artifacts")
    artifact_commands = artifacts.add_subparsers(dest="artifact_command", required=True)
    artifact_list = artifact_commands.add_parser("list")
    artifact_list.add_argument("--limit", type=int, default=50)
    artifact_read = artifact_commands.add_parser("read")
    artifact_read.add_argument("artifact_id")

    journal = commands.add_parser("journal")
    journal_commands = journal.add_subparsers(dest="journal_command", required=True)
    journal_list = journal_commands.add_parser("list")
    journal_list.add_argument("--limit", type=int, default=50)
    journal_add = journal_commands.add_parser("add")
    journal_add.add_argument("--type", choices=("entry", "decision", "backlog", "status"), default="entry")
    journal_add.add_argument(
        "--status",
        choices=("open", "closed", "decided", "parked", "blocked"),
        default="open",
    )
    journal_add.add_argument("--title", required=True)
    journal_add.add_argument("--body", default="")
    journal_read = journal_commands.add_parser("read")
    journal_read.add_argument("entry_id")
    journal_link = journal_commands.add_parser("link")
    journal_link.add_argument("entry_id")
    journal_link.add_argument("target_id")
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
        elif arguments.command == "receipts":
            if arguments.receipt_command == "list":
                response = {
                    "ok": True,
                    "receipts": runtime_records.list_receipts(context, arguments.limit),
                }
            else:
                response = {
                    "ok": True,
                    "receipt": runtime_records.read_receipt(context, arguments.receipt_id),
                }
        elif arguments.command == "artifacts":
            if arguments.artifact_command == "list":
                response = {
                    "ok": True,
                    "artifacts": runtime_records.list_artifacts(context, arguments.limit),
                }
            else:
                response = {
                    "ok": True,
                    "artifact": runtime_records.read_artifact(context, arguments.artifact_id),
                }
        elif arguments.command == "journal":
            if arguments.journal_command == "list":
                response = {
                    "ok": True,
                    "entries": app_journal.list_entries(context, arguments.limit),
                }
            elif arguments.journal_command == "add":
                response = {
                    "ok": True,
                    "entry": app_journal.add_entry(
                        context,
                        entry_type=arguments.type,
                        status=arguments.status,
                        title=arguments.title,
                        body=arguments.body,
                    ),
                }
            elif arguments.journal_command == "read":
                response = {"ok": True, **app_journal.read_entry(context, arguments.entry_id)}
            else:
                response = {
                    "ok": True,
                    "link": app_journal.link_entry(
                        context,
                        arguments.entry_id,
                        arguments.target_id,
                    ),
                }
        else:
            response = {"ok": False, "error": {"code": "unknown_command"}}
    except (
        InstanceError,
        storage.StorageError,
        registry.RegistryError,
        runtime_records.RecordError,
        app_journal.JournalError,
    ) as exc:
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
