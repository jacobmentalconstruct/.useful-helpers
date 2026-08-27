from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from tests.test_phase1 import InstalledFixture


class T3EpistemicSubstrateTests(InstalledFixture):
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

    def substrate(self, target: Path, *arguments: str) -> dict:
        process, response = self.sidecar_raw(target, "substrate", *arguments)
        self.assertEqual(process.returncode, 0, response)
        self.assertTrue(response["ok"], response)
        return response

    def test_fresh_attach_starts_with_blank_epistemic_substrate(self) -> None:
        target = self.target()
        self.attach(target)

        status = self.substrate(target, "status")
        self.assertEqual(status["counts"]["resources"], 0)
        self.assertEqual(status["counts"]["resource_versions"], 0)
        self.assertEqual(status["counts"]["observations"], 0)
        self.assertEqual(status["counts"]["epistemic_evidence"], 0)
        self.assertEqual(status["counts"]["claims"], 0)
        self.assertEqual(status["counts"]["relations"], 0)

        process, receipts = self.sidecar_raw(target, "receipts", "list")
        self.assertEqual(process.returncode, 0, receipts)
        process, journal = self.sidecar_raw(target, "journal", "list")
        self.assertEqual(process.returncode, 0, journal)
        self.assertEqual(receipts["receipts"], [])
        self.assertEqual(journal["entries"], [])

    def test_empty_target_refresh_records_thin_truth_without_fake_richness(self) -> None:
        target = self.target()
        self.attach(target)

        refresh = self.substrate(target, "refresh")
        self.assertEqual(refresh["observed"]["resource_count"], 0)
        self.assertEqual(refresh["observed"]["claim_count"], 1)

        claims = self.substrate(target, "claims", "list")["claims"]
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["claim_type"], "target_empty")
        self.assertLessEqual(claims[0]["confidence"], 1.0)
        self.assertIn("observed empty", claims[0]["statement"])

        resources = self.substrate(target, "resources", "list")["resources"]
        self.assertEqual(resources, [])
        observations = self.substrate(target, "observations", "list")["observations"]
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]["observation_type"], "resource_inventory")

    def test_non_empty_refresh_records_resources_versions_evidence_and_handles(self) -> None:
        target = self.target()
        (target / "docs").mkdir()
        (target / "docs" / "note.txt").write_text("hello substrate\n", encoding="utf-8")
        self.attach(target)

        refresh = self.substrate(target, "refresh")
        self.assertEqual(refresh["observed"]["resource_count"], 2)

        resources = self.substrate(target, "resources", "list")["resources"]
        handles = {item["handle"] for item in resources}
        self.assertEqual(handles, {"path:docs/", "path:docs/note.txt"})
        self.assertFalse(any(item["path"].startswith(".sidecar") for item in resources))

        file_resource = self.substrate(target, "resources", "read", "path:docs/note.txt")[
            "resource"
        ]
        self.assertEqual(file_resource["kind"], "file")
        self.assertEqual(file_resource["latest"]["content_hash"], refresh["observed"]["digest"])

        versions = self.substrate(target, "versions", "list", "path:docs/note.txt")["versions"]
        self.assertEqual(len(versions), 1)
        evidence = self.substrate(target, "evidence", "read", versions[0]["evidence_id"])[
            "evidence"
        ]
        self.assertTrue(evidence["evidence_id"].startswith("evidence:"))
        self.assertEqual(evidence["body"]["resource"]["handle"], "path:docs/note.txt")

    def test_changed_file_refresh_preserves_prior_version_and_evidence(self) -> None:
        target = self.target()
        note = target / "note.txt"
        note.write_text("first\n", encoding="utf-8")
        self.attach(target)
        self.substrate(target, "refresh")
        first_versions = self.substrate(target, "versions", "list", "path:note.txt")["versions"]
        first_id = first_versions[0]["version_id"]
        first_evidence = first_versions[0]["evidence_id"]

        note.write_text("second\n", encoding="utf-8")
        self.substrate(target, "refresh")

        versions = self.substrate(target, "versions", "list", "path:note.txt")["versions"]
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0]["version_id"], first_id)
        self.assertNotEqual(versions[1]["version_id"], first_id)
        self.assertNotEqual(versions[1]["evidence_id"], first_evidence)

        old_evidence = self.substrate(target, "evidence", "read", first_evidence)["evidence"]
        self.assertEqual(old_evidence["body"]["resource"]["content_hash"], first_versions[0]["content_hash"])

    def test_claim_trace_resolves_to_observation_evidence_and_resource(self) -> None:
        target = self.target()
        (target / "alpha.txt").write_text("alpha\n", encoding="utf-8")
        self.attach(target)
        self.substrate(target, "refresh")

        claims = self.substrate(target, "claims", "list")["claims"]
        text_claim = next(item for item in claims if item["claim_type"] == "target_has_text_files")
        trace = self.substrate(target, "trace", text_claim["claim_id"])["trace"]

        self.assertEqual(trace["start"]["id"], text_claim["claim_id"])
        predicates = {edge["predicate"] for edge in trace["relations"]}
        self.assertIn("derived_from", predicates)
        self.assertIn("supported_by", predicates)
        self.assertIn("concerns", predicates)
        self.assertTrue(any(node["id"].startswith("observation:") for node in trace["nodes"]))
        self.assertTrue(any(node["id"].startswith("evidence:") for node in trace["nodes"]))
        self.assertTrue(any(node["id"] == "path:alpha.txt" for node in trace["nodes"]))

    def test_substrate_does_not_collapse_into_t2_receipts_or_app_journal(self) -> None:
        target = self.target()
        (target / "note.txt").write_text("separation\n", encoding="utf-8")
        self.attach(target)
        self.substrate(target, "refresh")

        process, receipts = self.sidecar_raw(target, "receipts", "list")
        self.assertEqual(process.returncode, 0, receipts)
        process, journal = self.sidecar_raw(target, "journal", "list")
        self.assertEqual(process.returncode, 0, journal)
        process, artifacts = self.sidecar_raw(target, "artifacts", "list")
        self.assertEqual(process.returncode, 0, artifacts)

        self.assertEqual(journal["entries"], [])
        self.assertEqual(artifacts["artifacts"], [])

        database = target / ".sidecar" / "state" / "workbench.sqlite3"
        connection = sqlite3.connect(database)
        try:
            counts = {
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in (
                    "resources",
                    "resource_versions",
                    "observations",
                    "epistemic_evidence",
                    "claims",
                    "relations",
                    "operation_receipts",
                    "app_journal_entries",
                )
            }
        finally:
            connection.close()
        self.assertGreater(counts["resources"], 0)
        self.assertGreater(counts["resource_versions"], 0)
        self.assertGreater(counts["observations"], 0)
        self.assertGreater(counts["epistemic_evidence"], 0)
        self.assertGreater(counts["claims"], 0)
        self.assertGreater(counts["relations"], 0)
        self.assertEqual(counts["operation_receipts"], 0)
        self.assertEqual(counts["app_journal_entries"], 0)


if __name__ == "__main__":
    raise SystemExit(sys.exit(0))
