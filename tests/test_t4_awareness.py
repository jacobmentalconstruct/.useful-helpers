from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from tests.test_phase1 import InstalledFixture


class T4AwarenessTests(InstalledFixture):
    def sidecar_raw(self, target: Path, *arguments: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        front_door = target / ".sidecar" / "bin" / "sidecar.py"
        process = subprocess.run(
            [sys.executable, str(front_door), *arguments],
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
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

    def awareness(self, target: Path, *arguments: str) -> dict:
        process, response = self.sidecar_raw(target, "awareness", *arguments)
        self.assertEqual(process.returncode, 0, response)
        self.assertTrue(response["ok"], response)
        return response

    def substrate(self, target: Path, *arguments: str) -> dict:
        process, response = self.sidecar_raw(target, "substrate", *arguments)
        self.assertEqual(process.returncode, 0, response)
        self.assertTrue(response["ok"], response)
        return response

    def test_fresh_attach_starts_with_blank_awareness_and_runtime_state(self) -> None:
        target = self.target()
        self.attach(target)

        status = self.awareness(target, "status")
        self.assertEqual(status["counts"]["awareness_revisions"], 0)
        self.assertEqual(status["counts"]["awareness_items"], 0)

        process, receipts = self.sidecar_raw(target, "receipts", "list")
        self.assertEqual(process.returncode, 0, receipts)
        substrate_status = self.substrate(target, "status")
        self.assertEqual(receipts["receipts"], [])
        self.assertEqual(substrate_status["counts"]["resources"], 0)
        self.assertEqual(substrate_status["counts"]["claims"], 0)

    def test_unobserved_target_refresh_reports_unknown_basis_without_rich_findings(self) -> None:
        target = self.target()
        (target / "idea.py").write_text("print('not yet observed')\n", encoding="utf-8")
        self.attach(target)

        revision = self.awareness(target, "refresh")["revision"]

        self.assertEqual(revision["basis"]["status"], "missing")
        self.assertEqual(revision["freshness"], "unknown")
        self.assertEqual(revision["findings"], [])
        self.assertTrue(any("no substrate observations" in item for item in revision["limitations"]))
        self.assertTrue(any("unknown" in item for item in revision["unknowns"]))

    def test_empty_target_awareness_is_thin_and_immutable(self) -> None:
        target = self.target()
        self.attach(target)
        self.substrate(target, "refresh")

        first = self.awareness(target, "refresh")["revision"]
        second = self.awareness(target, "refresh")["revision"]

        self.assertTrue(first["awareness_id"].startswith("awareness:"))
        self.assertEqual(first["summary"]["target_state"], "observed_empty")
        self.assertEqual(first["freshness"], "current")
        self.assertTrue(first["findings"])
        self.assertTrue(any(item["source_handles"][0].startswith("claim:") for item in first["findings"]))
        self.assertNotEqual(first["awareness_id"], second["awareness_id"])

        read_back = self.awareness(target, "revisions", "read", first["awareness_id"])["revision"]
        self.assertEqual(read_back["awareness_id"], first["awareness_id"])
        self.assertEqual(read_back["summary"], first["summary"])

    def test_non_empty_awareness_exposes_resolvable_t3_handles_and_drill(self) -> None:
        target = self.target()
        (target / "docs").mkdir()
        (target / "docs" / "note.txt").write_text("hello awareness\n", encoding="utf-8")
        self.attach(target)
        self.substrate(target, "refresh")

        revision = self.awareness(target, "refresh")["revision"]
        self.assertEqual(revision["basis"]["status"], "observed")
        self.assertEqual(revision["summary"]["target_state"], "observed_non_empty")

        handles = {handle for item in revision["findings"] for handle in item["source_handles"]}
        self.assertIn("path:docs/note.txt", handles)
        self.assertTrue(any(handle.startswith("claim:") for handle in handles))

        for handle in handles:
            if handle.startswith("path:"):
                resource = self.substrate(target, "resources", "read", handle)["resource"]
                self.assertEqual(resource["handle"], handle)
            elif handle.startswith("claim:"):
                claim = self.substrate(target, "claims", "read", handle)["claim"]
                self.assertEqual(claim["claim_id"], handle)

        drill = self.awareness(target, "drill", revision["findings"][0]["item_id"])["drill"]
        self.assertEqual(drill["item"]["awareness_id"], revision["awareness_id"])
        self.assertTrue(any(node["id"].startswith(("claim:", "path:")) for node in drill["nodes"]))
        self.assertTrue(drill["relations"])

    def test_freshness_becomes_stale_after_target_change_without_refresh(self) -> None:
        target = self.target()
        note = target / "note.txt"
        note.write_text("first\n", encoding="utf-8")
        self.attach(target)
        self.substrate(target, "refresh")
        revision = self.awareness(target, "refresh")["revision"]
        self.assertEqual(revision["freshness"], "current")

        note.write_text("second\n", encoding="utf-8")

        current = self.awareness(target, "current")["revision"]
        self.assertEqual(current["awareness_id"], revision["awareness_id"])
        self.assertEqual(current["freshness"], "stale")

    def test_awareness_does_not_collapse_runtime_journal_or_substrate_owners(self) -> None:
        target = self.target()
        (target / "note.txt").write_text("separation\n", encoding="utf-8")
        self.attach(target)
        self.substrate(target, "refresh")
        self.awareness(target, "refresh")

        process, receipts = self.sidecar_raw(target, "receipts", "list")
        self.assertEqual(process.returncode, 0, receipts)
        process, journal = self.sidecar_raw(target, "journal", "list")
        self.assertEqual(process.returncode, 0, journal)
        self.assertEqual(receipts["receipts"], [])
        self.assertEqual(journal["entries"], [])

        database = target / ".sidecar" / "state" / "workbench.sqlite3"
        connection = sqlite3.connect(database)
        try:
            counts = {
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in (
                    "awareness_revisions",
                    "awareness_items",
                    "claims",
                    "epistemic_evidence",
                    "operational_artifacts",
                    "app_journal_entries",
                )
            }
        finally:
            connection.close()
        self.assertGreater(counts["awareness_revisions"], 0)
        self.assertGreater(counts["awareness_items"], 0)
        self.assertGreater(counts["claims"], 0)
        self.assertGreater(counts["epistemic_evidence"], 0)
        self.assertEqual(counts["operational_artifacts"], 0)
        self.assertEqual(counts["app_journal_entries"], 0)


if __name__ == "__main__":
    raise SystemExit(sys.exit(0))
