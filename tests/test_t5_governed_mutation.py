from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from product.core import storage
from product.core.instance import load
from tests.test_phase1 import InstalledFixture


class T5GovernedMutationTests(InstalledFixture):
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

    def mutation(self, target: Path, *arguments: str) -> dict:
        process, response = self.sidecar_raw(target, "mutation", *arguments)
        self.assertEqual(process.returncode, 0, response)
        self.assertTrue(response["ok"], response)
        return response

    def mutation_refusal(self, target: Path, *arguments: str) -> dict:
        process, response = self.sidecar_raw(target, "mutation", *arguments)
        self.assertNotEqual(process.returncode, 0)
        self.assertFalse(response["ok"], response)
        return response

    def substrate(self, target: Path, *arguments: str) -> dict:
        process, response = self.sidecar_raw(target, "substrate", *arguments)
        self.assertEqual(process.returncode, 0, response)
        self.assertTrue(response["ok"], response)
        return response

    def awareness(self, target: Path, *arguments: str) -> dict:
        process, response = self.sidecar_raw(target, "awareness", *arguments)
        self.assertEqual(process.returncode, 0, response)
        self.assertTrue(response["ok"], response)
        return response

    def journal_add(self, target: Path) -> str:
        process, response = self.sidecar_raw(
            target,
            "journal",
            "add",
            "--type",
            "decision",
            "--status",
            "decided",
            "--title",
            "Approve bounded write",
            "--body",
            "Operator reviewed the preview and approved the single write.",
        )
        self.assertEqual(process.returncode, 0, response)
        return response["entry"]["entry_id"]

    def prepare_awareness(self, target: Path) -> dict:
        self.substrate(target, "refresh")
        return self.awareness(target, "refresh")["revision"]

    def test_migration_stamps_each_materialized_version_before_t5_schema(self) -> None:
        target = self.target()
        self.attach(target)
        context = load(target / ".sidecar")
        database = target / ".sidecar" / "state" / "workbench.sqlite3"
        connection = sqlite3.connect(database)
        try:
            for table in (
                "mutation_links",
                "mutation_records",
                "mutation_verifications",
                "mutation_approvals",
                "mutation_previews",
                "awareness_items",
                "awareness_revisions",
                "relations",
                "claims",
                "observations",
                "resource_versions",
                "epistemic_evidence",
                "resources",
            ):
                connection.execute(f"DROP TABLE IF EXISTS {table}")
            connection.execute("PRAGMA user_version = 2")
            connection.commit()

            storage._migrate(connection, target_version=3)
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 3)
            tables = self.table_names(connection)
            self.assertIn("resources", tables)
            self.assertNotIn("awareness_revisions", tables)
            self.assertNotIn("mutation_previews", tables)

            storage._migrate(connection, target_version=4)
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 4)
            tables = self.table_names(connection)
            self.assertIn("awareness_revisions", tables)
            self.assertNotIn("mutation_previews", tables)

            storage._migrate(connection, target_version=5)
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 5)
            tables = self.table_names(connection)
            self.assertGreaterEqual(
                tables,
                {
                    "mutation_previews",
                    "mutation_approvals",
                    "mutation_records",
                    "mutation_verifications",
                    "mutation_links",
                },
            )
        finally:
            connection.close()

        status = self.sidecar_raw(target, "status")[1]
        self.assertEqual(status["database_schema"], 5)
        self.assertEqual(context.instance_uuid, status["instance_uuid"])

    @staticmethod
    def table_names(connection: sqlite3.Connection) -> set[str]:
        return {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    def test_fresh_attach_starts_with_blank_mutation_state(self) -> None:
        target = self.target()
        self.attach(target)

        status = self.mutation(target, "status")

        self.assertEqual(
            status["counts"],
            {
                "mutation_previews": 0,
                "mutation_approvals": 0,
                "mutation_records": 0,
                "mutation_verifications": 0,
                "mutation_links": 0,
            },
        )
        process, journal = self.sidecar_raw(target, "journal", "list")
        self.assertEqual(process.returncode, 0, journal)
        self.assertEqual(journal["entries"], [])

    def test_preview_records_reviewed_write_without_applying(self) -> None:
        target = self.target()
        self.attach(target)
        revision = self.prepare_awareness(target)

        preview = self.mutation(
            target,
            "preview-write",
            "--path",
            "docs/note.txt",
            "--content",
            "reviewed payload\n",
        )["preview"]

        self.assertTrue(preview["preview_id"].startswith("mutation:preview:"))
        self.assertEqual(preview["path"], "docs/note.txt")
        self.assertEqual(preview["operation"], "write_file")
        self.assertEqual(preview["expected_changed_paths"], ["docs/note.txt"])
        self.assertEqual(preview["awareness_id"], revision["awareness_id"])
        self.assertEqual(preview["basis_signature"], revision["basis"]["signature"])
        self.assertTrue(preview["target_signature"])
        self.assertFalse((target / "docs" / "note.txt").exists())
        self.assertEqual(self.sidecar_raw(target, "receipts", "list")[1]["receipts"], [])

    def test_approval_is_bound_to_exact_preview_and_journal_link_is_deliberate(self) -> None:
        target = self.target()
        self.attach(target)
        self.prepare_awareness(target)
        decision = self.journal_add(target)
        first = self.mutation(
            target,
            "preview-write",
            "--path",
            "first.txt",
            "--content",
            "first\n",
        )["preview"]
        second = self.mutation(
            target,
            "preview-write",
            "--path",
            "second.txt",
            "--content",
            "second\n",
        )["preview"]

        approval = self.mutation(
            target,
            "approve",
            first["preview_id"],
            "--journal-entry",
            decision,
        )["approval"]

        self.assertTrue(approval["approval_id"].startswith("mutation:approval:"))
        self.assertEqual(approval["preview_id"], first["preview_id"])
        self.assertEqual(approval["preview_digest"], first["preview_digest"])
        self.assertNotEqual(approval["preview_digest"], second["preview_digest"])

        mismatched = self.mutation_refusal(
            target,
            "apply",
            approval["approval_id"],
            "--preview",
            second["preview_id"],
        )
        self.assertEqual(mismatched["error"]["code"], "approval_preview_mismatch")
        self.assertFalse((target / "first.txt").exists())
        self.assertFalse((target / "second.txt").exists())

        links = self.mutation(target, "links", first["preview_id"])["links"]
        self.assertIn(decision, {item["target_id"] for item in links})

    def test_apply_without_approval_and_stale_apply_refuse_before_launch(self) -> None:
        target = self.target()
        self.attach(target)
        self.prepare_awareness(target)

        preview = self.mutation(
            target,
            "preview-write",
            "--path",
            "created.txt",
            "--content",
            "must wait\n",
        )["preview"]
        without_approval = self.mutation_refusal(target, "apply", preview["preview_id"])
        self.assertEqual(without_approval["error"]["code"], "approval_not_found")
        self.assertFalse((target / "created.txt").exists())
        self.assertEqual(self.sidecar_raw(target, "receipts", "list")[1]["receipts"], [])

        approval = self.mutation(target, "approve", preview["preview_id"])["approval"]
        (target / "outside-change.txt").write_text("basis drift\n", encoding="utf-8")
        stale = self.mutation_refusal(target, "apply", approval["approval_id"])
        self.assertEqual(stale["error"]["code"], "stale_target")
        self.assertFalse((target / "created.txt").exists())
        self.assertEqual(self.sidecar_raw(target, "receipts", "list")[1]["receipts"], [])

    def test_successful_apply_uses_host_measures_refreshes_and_links_records(self) -> None:
        target = self.target()
        self.attach(target)
        before_revision = self.prepare_awareness(target)
        decision = self.journal_add(target)
        preview = self.mutation(
            target,
            "preview-write",
            "--path",
            "notes/result.txt",
            "--content",
            "governed write\n",
        )["preview"]
        approval = self.mutation(
            target,
            "approve",
            preview["preview_id"],
            "--journal-entry",
            decision,
        )["approval"]

        applied = self.mutation(target, "apply", approval["approval_id"])["mutation"]

        self.assertTrue(applied["mutation_id"].startswith("mutation:record:"))
        self.assertEqual(applied["status"], "applied")
        self.assertEqual(applied["receipt_id"], self.sidecar_raw(target, "receipts", "list")[1]["receipts"][0]["receipt_id"])
        self.assertEqual(applied["measurement"]["changed_paths"], ["notes/result.txt"])
        self.assertEqual(applied["measurement"]["source"], "independent_target_snapshot")
        self.assertEqual(applied["verification"]["status"], "unavailable")
        self.assertIn("No target-native verification", applied["verification"]["detail"])
        self.assertEqual((target / "notes" / "result.txt").read_text(encoding="utf-8"), "governed write\n")

        after_revision = self.awareness(target, "current")["revision"]
        self.assertNotEqual(after_revision["awareness_id"], before_revision["awareness_id"])
        self.assertEqual(after_revision["freshness"], "current")
        self.assertIn("path:notes/result.txt", after_revision["source_handles"])

        old_revision = self.awareness(
            target,
            "revisions",
            "read",
            before_revision["awareness_id"],
        )["revision"]
        self.assertEqual(old_revision["awareness_id"], before_revision["awareness_id"])

        links = self.mutation(target, "links", applied["mutation_id"])["links"]
        targets = {item["target_id"] for item in links}
        self.assertIn(applied["receipt_id"], targets)
        self.assertIn(applied["artifact_id"], targets)
        self.assertIn(applied["verification"]["verification_id"], targets)
        self.assertIn(applied["post_awareness_id"], targets)
        self.assertIn(decision, targets)

    def test_child_process_environment_does_not_inherit_identity_or_operator_tokens(self) -> None:
        target = self.target()
        self.attach(target)
        tool_root = target / ".sidecar" / "tools" / "env_probe"
        tool_root.mkdir()
        (tool_root / "__init__.py").write_text("", encoding="utf-8")
        (tool_root / "tool.py").write_text(
            "import json, os\n"
            "print(json.dumps({\n"
            "  'ok': True,\n"
            "  'tool': 'env_probe',\n"
            "  'saw_identity': any(k.startswith('SIDECAR_IDENTITY_') for k in os.environ),\n"
            "  'saw_operator_token': 'OPERATOR_TOKEN' in os.environ,\n"
            "  'has_pythonpath': 'PYTHONPATH' in os.environ,\n"
            "}))\n",
            encoding="utf-8",
        )
        (tool_root / "manifest.json").write_text(
            json.dumps(
                {
                    "contract_version": 1,
                    "id": "env_probe",
                    "description": "test-only environment probe",
                    "authority": "observe",
                    "input_schema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "ok": {"type": "boolean"},
                            "tool": {"type": "string"},
                            "saw_identity": {"type": "boolean"},
                            "saw_operator_token": {"type": "boolean"},
                            "has_pythonpath": {"type": "boolean"},
                        },
                        "required": ["ok", "saw_identity", "saw_operator_token", "has_pythonpath"],
                        "additionalProperties": False,
                    },
                    "reads": ["target"],
                    "writes": [],
                    "applicability": {"domains": ["test"]},
                    "path_arguments": {},
                    "invocation": {"kind": "python", "entry": "tools/env_probe/tool.py"},
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        process, response = self.sidecar_raw(
            target,
            "call",
            "env_probe",
            "--args",
            "{}",
            environment={
                "SIDECAR_IDENTITY_SECRET": "must-not-cross",
                "OPERATOR_TOKEN": "must-not-cross",
            },
        )

        self.assertEqual(process.returncode, 0, response)
        self.assertFalse(response["result"]["saw_identity"])
        self.assertFalse(response["result"]["saw_operator_token"])
        self.assertTrue(response["result"]["has_pythonpath"])

    def test_mutation_loop_is_generic_and_separate_from_app_journal_projection(self) -> None:
        target = self.target()
        (target / "plain.records").write_text("alpha\n", encoding="utf-8")
        self.attach(target)
        self.prepare_awareness(target)
        preview = self.mutation(
            target,
            "preview-write",
            "--path",
            "plain.records",
            "--content",
            "beta\n",
            "--overwrite",
        )["preview"]
        approval = self.mutation(target, "approve", preview["preview_id"])["approval"]
        self.mutation(target, "apply", approval["approval_id"])

        process, journal = self.sidecar_raw(target, "journal", "list")
        self.assertEqual(process.returncode, 0, journal)
        self.assertEqual(journal["entries"], [])
        self.assertEqual((target / "plain.records").read_text(encoding="utf-8"), "beta\n")


if __name__ == "__main__":
    raise SystemExit(sys.exit(0))
