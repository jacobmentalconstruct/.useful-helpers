from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from tests.test_phase1 import InstalledFixture


BAD_TOOL_MANIFEST = {
    "contract_version": 1,
    "description": "test-only malformed output tool",
    "authority": "observe",
    "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    "output_schema": {
        "type": "object",
        "properties": {"ok": {"type": "boolean"}, "error": {"type": "string"}},
        "required": ["ok"],
        "additionalProperties": False,
    },
    "reads": ["target"],
    "writes": [],
    "applicability": {"domains": ["test"]},
    "path_arguments": {},
    "invocation": {"kind": "python", "entry": ""},
}


class T2RuntimeMemoryTests(InstalledFixture):
    def sidecar_raw(
        self,
        target: Path,
        *arguments: str,
        environment: dict[str, str] | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict]:
        front_door = target / ".sidecar" / "bin" / "sidecar.py"
        env = dict(os.environ)
        if environment:
            env.update(environment)
        process = subprocess.run(
            [sys.executable, str(front_door), *arguments],
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            check=False,
        )
        try:
            document = json.loads(process.stdout)
        except json.JSONDecodeError as exc:
            self.fail(
                f"sidecar did not emit JSON: {exc}\n"
                f"stdout={process.stdout!r}\nstderr={process.stderr!r}"
            )
        return process, document

    def receipts(self, target: Path) -> list[dict]:
        process, response = self.sidecar_raw(target, "receipts", "list")
        self.assertEqual(process.returncode, 0, response)
        return response["receipts"]

    def artifacts(self, target: Path) -> list[dict]:
        process, response = self.sidecar_raw(target, "artifacts", "list")
        self.assertEqual(process.returncode, 0, response)
        return response["artifacts"]

    def journal_entries(self, target: Path) -> list[dict]:
        process, response = self.sidecar_raw(target, "journal", "list")
        self.assertEqual(process.returncode, 0, response)
        return response["entries"]

    def install_test_tool(self, target: Path, tool_id: str, source: str) -> None:
        tool_root = target / ".sidecar" / "tools" / tool_id
        tool_root.mkdir()
        (tool_root / "__init__.py").write_text("", encoding="utf-8")
        (tool_root / "tool.py").write_text(source, encoding="utf-8")
        manifest = dict(BAD_TOOL_MANIFEST)
        manifest["id"] = tool_id
        manifest["invocation"] = {"kind": "python", "entry": f"tools/{tool_id}/tool.py"}
        (tool_root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def test_fresh_attach_starts_with_blank_runtime_memory(self) -> None:
        target = self.target()
        self.attach(target)

        self.assertEqual(self.receipts(target), [])
        self.assertEqual(self.artifacts(target), [])
        self.assertEqual(self.journal_entries(target), [])
        self.assertFalse((target / ".sidecar" / ".builder").exists())

        database = target / ".sidecar" / "state" / "workbench.sqlite3"
        connection = sqlite3.connect(database)
        try:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            self.assertIn("operation_receipts", tables)
            self.assertIn("operational_artifacts", tables)
            self.assertIn("app_journal_entries", tables)
            self.assertIn("app_journal_links", tables)
            counts = {
                name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                for name in (
                    "operation_receipts",
                    "operational_artifacts",
                    "app_journal_entries",
                    "app_journal_links",
                )
            }
        finally:
            connection.close()
        self.assertEqual(counts, {name: 0 for name in counts})

    def test_receipts_record_success_refusal_malformed_output_and_process_failure(self) -> None:
        target = self.target()
        (target / "note.txt").write_bytes(b"hello receipts\n")
        self.attach(target)

        process, read_response = self.call(target, "read_file", {"path": "note.txt"})
        self.assertEqual(process.returncode, 0, read_response)

        process, denied = self.call(
            target,
            "write_file",
            {"path": "created.txt", "content": "no", "confirm": True},
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(denied["error"]["code"], "authority_denied")

        self.install_test_tool(target, "bad_json", "print('not-json')\n")
        process, malformed = self.call(target, "bad_json", {})
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(malformed["error"]["code"], "output_contract")

        self.install_test_tool(
            target,
            "process_fail",
            "import json, sys\nprint(json.dumps({'ok': False, 'error': 'boom'}))\nsys.exit(3)\n",
        )
        process, failed = self.call(target, "process_fail", {})
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(failed["error"]["code"], "tool_process_failed")

        receipts = self.receipts(target)
        self.assertEqual(
            [(item["tool_id"], item["status"], item.get("error_code")) for item in receipts],
            [
                ("read_file", "success", None),
                ("write_file", "refusal", "authority_denied"),
                ("bad_json", "failure", "output_contract"),
                ("process_fail", "failure", "tool_process_failed"),
            ],
        )
        for receipt in receipts:
            self.assertTrue(receipt["receipt_id"].startswith("operation:"))
            self.assertTrue(receipt["artifact_id"].startswith("artifact:"))

        process, artifact = self.sidecar_raw(target, "artifacts", "read", receipts[0]["artifact_id"])
        self.assertEqual(process.returncode, 0, artifact)
        self.assertEqual(artifact["artifact"]["kind"], "tool_result")
        self.assertEqual(artifact["artifact"]["body"]["envelope"]["tool_id"], "read_file")
        self.assertEqual(artifact["artifact"]["body"]["envelope"]["result"]["content"], "hello receipts\n")

    def test_app_journal_is_deliberate_memory_not_receipt_projection(self) -> None:
        target = self.target()
        (target / "note.txt").write_bytes(b"journal witness\n")
        self.attach(target)

        _, read_response = self.call(target, "read_file", {"path": "note.txt"})
        receipt_id = self.receipts(target)[0]["receipt_id"]
        artifact_id = self.receipts(target)[0]["artifact_id"]
        self.assertEqual(self.journal_entries(target), [])

        process, created = self.sidecar_raw(
            target,
            "journal",
            "add",
            "--type",
            "decision",
            "--status",
            "decided",
            "--title",
            "Keep runtime history separate",
            "--body",
            "Receipts are event provenance; journal entries are deliberate memory.",
        )
        self.assertEqual(process.returncode, 0, created)
        entry_id = created["entry"]["entry_id"]
        self.assertTrue(entry_id.startswith("journal:"))

        for target_id in (receipt_id, artifact_id):
            process, linked = self.sidecar_raw(target, "journal", "link", entry_id, target_id)
            self.assertEqual(process.returncode, 0, linked)

        process, reread = self.sidecar_raw(target, "journal", "read", entry_id)
        self.assertEqual(process.returncode, 0, reread)
        self.assertEqual(reread["entry"]["entry_type"], "decision")
        self.assertEqual(reread["entry"]["status"], "decided")
        self.assertEqual(
            {link["target_id"] for link in reread["links"]},
            {receipt_id, artifact_id},
        )
        self.assertEqual(read_response["result"]["content"], "journal witness\n")

    def test_state_changing_call_refuses_when_receipt_creation_fails(self) -> None:
        target = self.target()
        self.attach(target)
        database = target / ".sidecar" / "state" / "workbench.sqlite3"
        connection = sqlite3.connect(database)
        try:
            connection.execute(
                """
                CREATE TRIGGER refuse_receipts
                BEFORE INSERT ON operation_receipts
                BEGIN
                    SELECT RAISE(ABORT, 'forced receipt insert failure');
                END
                """
            )
            connection.commit()
        finally:
            connection.close()

        process, response = self.call(
            target,
            "write_file",
            {"path": "created.txt", "content": "must not appear\n", "confirm": True},
            authority="apply",
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(response["error"]["code"], "receipt_persistence_failed")
        self.assertFalse(response["durably_governed"])
        self.assertFalse((target / "created.txt").exists())

    def test_receipts_and_journal_persist_across_process_reentry(self) -> None:
        target = self.target()
        (target / "note.txt").write_text("restart witness\n", encoding="utf-8")
        self.attach(target)
        self.call(target, "read_file", {"path": "note.txt"})
        process, created = self.sidecar_raw(
            target,
            "journal",
            "add",
            "--type",
            "backlog",
            "--status",
            "open",
            "--title",
            "Follow up",
            "--body",
            "This should survive a new CLI process.",
        )
        self.assertEqual(process.returncode, 0, created)

        process, receipts = self.sidecar_raw(target, "receipts", "list")
        self.assertEqual(process.returncode, 0)
        process, entries = self.sidecar_raw(target, "journal", "list")
        self.assertEqual(process.returncode, 0)
        self.assertEqual(len(receipts["receipts"]), 1)
        self.assertEqual(entries["entries"][0]["title"], "Follow up")
        self.assertEqual(entries["entries"][0]["status"], "open")


if __name__ == "__main__":
    raise SystemExit(sys.exit(0))
