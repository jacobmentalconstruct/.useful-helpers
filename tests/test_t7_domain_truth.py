from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest import mock
from pathlib import Path

from product.core import substrate
from tests.test_phase1 import InstalledFixture
from tests.test_t6_mcp_entrance import McpSession


class T7DomainTruthTests(InstalledFixture):
    def sidecar_raw(self, target: Path, *arguments: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        process = subprocess.run(
            [sys.executable, str(target / ".sidecar" / "bin" / "sidecar.py"), *arguments],
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

    def awareness(self, target: Path, *arguments: str) -> dict:
        process, response = self.sidecar_raw(target, "awareness", *arguments)
        self.assertEqual(process.returncode, 0, response)
        self.assertTrue(response["ok"], response)
        return response

    def claims(self, target: Path) -> list[dict]:
        return self.substrate(target, "claims", "list", "--limit", "200")["claims"]

    def claim(self, target: Path, claim_type: str) -> dict:
        for claim in self.claims(target):
            if claim["claim_type"] == claim_type:
                return claim
        self.fail(f"missing claim type {claim_type!r}")

    def test_unobserved_and_observed_empty_are_not_collapsed(self) -> None:
        target = self.target()
        self.attach(target)

        unobserved = self.awareness(target, "refresh")["revision"]
        self.assertEqual(unobserved["summary"]["target_state"], "unknown_unobserved")
        self.assertEqual(unobserved["findings"], [])
        self.assertTrue(any("unobserved remains unknown" in item for item in unobserved["unknowns"]))

        self.substrate(target, "refresh")
        observed = self.awareness(target, "refresh")["revision"]
        self.assertEqual(observed["summary"]["target_state"], "observed_empty")
        self.assertEqual(observed["summary"]["domain_profile"], "empty_or_nascent")
        self.assertTrue(any(item["title"] == "target_empty" for item in observed["findings"]))
        self.assertFalse(any("software" in item["title"] for item in observed["findings"]))

    def write_realistic_software_project(self, target: Path) -> None:
        """A small but realistic software project: docs, config, VCS internals, vendor tree."""
        (target / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
        (target / "README.md").write_text("# demo\n\nA realistic project.\n", encoding="utf-8")
        (target / "LICENSE").write_text("MIT\n", encoding="utf-8")
        (target / "CHANGELOG.md").write_text("## 0.1.0\n", encoding="utf-8")
        (target / "config.json").write_text('{"debug": false}\n', encoding="utf-8")
        (target / "NOTES.txt").write_text("todo: ship\n", encoding="utf-8")
        (target / "src").mkdir()
        (target / "src" / "app.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
        (target / "src" / "worker.py").write_text("from .app import main\n", encoding="utf-8")
        (target / "src" / "settings.yaml").write_text("level: info\n", encoding="utf-8")
        (target / "tests").mkdir()
        (target / "tests" / "test_app.py").write_text("def test_main():\n    assert True\n", encoding="utf-8")
        (target / "docs").mkdir()
        (target / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
        git = target / ".git"
        (git / "objects" / "ab").mkdir(parents=True)
        (git / "refs" / "heads").mkdir(parents=True)
        (git / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
        (git / "config").write_text("[core]\n\trepositoryformatversion = 0\n", encoding="utf-8")
        (git / "objects" / "ab" / "cdef0123").write_bytes(b"x\x9c" + bytes(range(64)))
        (git / "refs" / "heads" / "main").write_text("0" * 40 + "\n", encoding="utf-8")
        vendor = target / "node_modules" / "left-pad"
        vendor.mkdir(parents=True)
        (vendor / "index.js").write_text("module.exports = 1;\n", encoding="utf-8")
        (vendor / "package.json").write_text('{"name": "left-pad"}\n', encoding="utf-8")

    def test_substantial_software_fixture_produces_traceable_domain_truth(self) -> None:
        target = self.target()
        self.write_realistic_software_project(target)
        self.attach(target)

        self.substrate(target, "refresh")
        software = self.claim(target, "target_profile_software")
        self.assertEqual(software["derivation_method"], "deterministic.domain_signals")
        self.assertGreaterEqual(software["confidence"], 0.8)
        self.assertIn("software", software["statement"])
        self.assertIn("path:pyproject.toml", software["data"]["supporting_handles"])
        self.assertGreaterEqual(software["data"]["ancillary_document_count"], 4)
        self.assertGreaterEqual(software["data"]["ancillary_config_count"], 2)
        claim_types = {claim["claim_type"] for claim in self.claims(target)}
        self.assertNotIn("target_profile_records_documents", claim_types)

        trace = self.substrate(target, "trace", software["claim_id"])["trace"]
        self.assertTrue(any(node["type"] == "observation" for node in trace["nodes"]))
        self.assertTrue(any(node["type"] == "evidence" for node in trace["nodes"]))
        self.assertTrue(any(node["id"] == "path:pyproject.toml" for node in trace["nodes"]))

        revision = self.awareness(target, "refresh")["revision"]
        self.assertEqual(revision["summary"]["domain_profile"], "software")
        self.assertTrue(any(item["title"] == "target_profile_software" for item in revision["findings"]))
        handles = {handle for item in revision["findings"] for handle in item["source_handles"]}
        self.assertIn(software["claim_id"], handles)

    def test_true_mixed_fixture_reports_mixed_for_substantive_records(self) -> None:
        target = self.target()
        (target / "tools").mkdir()
        (target / "tools" / "export.py").write_text("print('export')\n", encoding="utf-8")
        (target / "tools" / "clean.py").write_text("print('clean')\n", encoding="utf-8")
        (target / "README.md").write_text("# Client records\n", encoding="utf-8")
        (target / "records").mkdir()
        (target / "records" / "clients.csv").write_text("id,name\n1,Ada\n", encoding="utf-8")
        (target / "records" / "invoices.csv").write_text("id,total\n1,10\n", encoding="utf-8")
        (target / "contracts").mkdir()
        (target / "contracts" / "agreement.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
        self.attach(target)

        self.substrate(target, "refresh")
        profile = self.claim(target, "target_profile_records_documents")
        self.assertEqual(profile["data"]["decision"], "mixed_by_count")
        self.assertIn("path:records/clients.csv", profile["data"]["supporting_handles"])
        self.assertNotIn("path:README.md", profile["data"]["supporting_handles"])
        self.claim(target, "target_profile_software")

        revision = self.awareness(target, "refresh")["revision"]
        self.assertEqual(revision["summary"]["domain_profile"], "mixed")

    def test_subordinate_document_beside_software_does_not_produce_mixed(self) -> None:
        target = self.target()
        for name in ("a.py", "b.py", "c.py"):
            (target / name).write_text("x = 1\n", encoding="utf-8")
        (target / "docs").mkdir()
        (target / "docs" / "spec.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
        self.attach(target)

        self.substrate(target, "refresh")
        software = self.claim(target, "target_profile_software")
        self.assertEqual(software["data"]["subordinate_records_document_count"], 1)
        self.assertTrue(any("subordinate" in item for item in software["data"]["limitations"]))
        claim_types = {claim["claim_type"] for claim in self.claims(target)}
        self.assertNotIn("target_profile_records_documents", claim_types)
        self.assertIn("target_has_weak_material", claim_types)
        revision = self.awareness(target, "refresh")["revision"]
        self.assertEqual(revision["summary"]["domain_profile"], "software")

    def test_generated_and_vendor_subtrees_are_metadata_only_and_not_traversed(self) -> None:
        target = self.target()
        self.write_realistic_software_project(target)
        git_object = target / ".git" / "objects" / "ab" / "cdef0123"
        vendor_file = target / "node_modules" / "left-pad" / "index.js"
        original_read_bytes = Path.read_bytes

        def reject_generated_read(path: Path) -> bytes:
            if path in {git_object, vendor_file}:
                raise AssertionError(f"generated or vendor material was read: {path}")
            return original_read_bytes(path)

        with mock.patch.object(Path, "read_bytes", reject_generated_read):
            records = substrate._resource_records(SimpleNamespace(
                target_root=target,
                instance_root=target / ".sidecar",
            ))

        handles = {record["handle"] for record in records}
        self.assertIn("path:.git/", handles)
        self.assertIn("path:node_modules/", handles)
        self.assertFalse(any(handle.startswith("path:.git/") and handle != "path:.git/" for handle in handles))
        self.assertFalse(
            any(handle.startswith("path:node_modules/") and handle != "path:node_modules/" for handle in handles)
        )
        git_record = next(record for record in records if record["handle"] == "path:.git/")
        self.assertTrue(git_record["domain"]["weak_material"])
        self.assertIn("generated", git_record["domain"]["categories"])
        self.assertTrue(any("not traversed" in item for item in git_record["domain"]["limitations"]))

        self.attach(target)
        refresh = self.substrate(target, "refresh")["observed"]
        self.assertTrue(any("not traversed" in item for item in refresh["limitations"]))
        weak = self.claim(target, "target_has_weak_material")
        self.assertIn("path:.git/", weak["data"]["supporting_handles"])
        self.assertIn("path:node_modules/", weak["data"]["supporting_handles"])
        self.assertTrue(any("vendor/dependency-like" in item for item in weak["data"]["limitations"]))
        revision = self.awareness(target, "refresh")["revision"]
        self.assertTrue(any("not traversed" in item for item in revision["limitations"]))
        self.assertLess(revision["summary"]["resource_count"], 25)

    def test_unchanged_refresh_does_not_grow_evidence_or_versions(self) -> None:
        target = self.target()
        for index in range(5):
            (target / f"f{index}.txt").write_text(f"file {index}\n", encoding="utf-8")
        self.attach(target)
        self.substrate(target, "refresh")
        first = self.substrate(target, "status")["counts"]
        self.substrate(target, "refresh")
        self.substrate(target, "refresh")
        third = self.substrate(target, "status")["counts"]
        self.assertEqual(third["resource_versions"], first["resource_versions"])
        self.assertEqual(third["epistemic_evidence"], first["epistemic_evidence"])
        self.assertEqual(len(self.substrate(target, "versions", "list", "path:f0.txt")["versions"]), 1)

        (target / "f0.txt").write_text("changed\n", encoding="utf-8")
        self.substrate(target, "refresh")
        self.assertEqual(len(self.substrate(target, "versions", "list", "path:f0.txt")["versions"]), 2)
        self.assertEqual(
            self.substrate(target, "status")["counts"]["resource_versions"],
            first["resource_versions"] + 1,
        )

    def test_awareness_discloses_truncated_projection(self) -> None:
        target = self.target()
        (target / "many").mkdir()
        for index in range(30):
            (target / "many" / f"r{index}.txt").write_text("row\n", encoding="utf-8")
        self.attach(target)
        self.substrate(target, "refresh")
        revision = self.awareness(target, "refresh")["revision"]
        projection = revision["summary"]["projection"]
        self.assertEqual(projection["resource_handles"]["shown"], 20)
        self.assertEqual(projection["resource_handles"]["total"], 31)
        self.assertEqual(projection["source_handles"]["shown"], 100)
        self.assertGreater(projection["source_handles"]["total"], 100)
        self.assertEqual(len(revision["source_handles"]), 100)
        self.assertTrue(any("100 of " in item and "source handles" in item for item in revision["limitations"]))
        self.assertTrue(any("20 of 31 resource handles" in item for item in revision["limitations"]))
        current = self.awareness(target, "current")["revision"]
        self.assertEqual(current["summary"]["projection"], projection)

    def test_mixed_records_documents_fixture_reports_limited_basis(self) -> None:
        target = self.target()
        (target / "records").mkdir()
        (target / "records" / "clients.csv").write_text("id,name\n1,Ada\n", encoding="utf-8")
        (target / "docs").mkdir()
        (target / "docs" / "agreement.pdf").write_bytes(b"%PDF-1.4\nnot parsed by T7\n%%EOF\n")
        (target / "notes.md").write_text("# Notes\nContract follow-up\n", encoding="utf-8")
        self.attach(target)

        self.substrate(target, "refresh")
        profile = self.claim(target, "target_profile_records_documents")
        weak = self.claim(target, "target_has_weak_material")
        self.assertIn("records/document", profile["statement"])
        self.assertIn("path:docs/agreement.pdf", weak["data"]["supporting_handles"])
        self.assertTrue(any("unparsed document" in item for item in weak["data"]["limitations"]))
        self.assertFalse(any("parsed text" in item.lower() for item in weak["data"]["limitations"]))

        revision = self.awareness(target, "refresh")["revision"]
        self.assertEqual(revision["summary"]["domain_profile"], "records_documents")
        self.assertTrue(any("metadata-only" in item for item in revision["limitations"]))
        self.assertTrue(any(item["title"] == "target_has_weak_material" for item in revision["findings"]))

    def test_weak_material_fixture_does_not_overclaim_or_dominate_orientation(self) -> None:
        target = self.target()
        (target / "node_modules" / "package").mkdir(parents=True)
        (target / "node_modules" / "package" / "index.js").write_text("module.exports = 1;\n", encoding="utf-8")
        (target / "media").mkdir()
        (target / "media" / "image.bin").write_bytes(bytes(range(256)) * 8)
        (target / "large.dat").write_bytes(b"x" * 1_100_000)
        (target / "README.md").write_text("# Mixed weak material\n", encoding="utf-8")
        self.attach(target)

        refresh = self.substrate(target, "refresh")["observed"]
        self.assertLessEqual(refresh["claim_count"], 4)
        weak = self.claim(target, "target_has_weak_material")
        self.assertEqual(weak["data"]["content_basis"], "metadata_only")
        self.assertTrue(any("large file" in item for item in weak["data"]["limitations"]))
        self.assertTrue(any("vendor/dependency-like" in item for item in weak["data"]["limitations"]))
        self.assertTrue(any("binary/media" in item for item in weak["data"]["limitations"]))
        self.assertNotIn("semantic_summary", weak["data"])

        revision = self.awareness(target, "refresh")["revision"]
        self.assertLessEqual(len(revision["findings"]), 5)
        self.assertTrue(any("weak material" in item for item in revision["limitations"]))
        self.assertFalse(any("parsed" in item["statement"].lower() for item in revision["findings"]))

    def test_large_weak_material_is_not_fully_read_or_hashed(self) -> None:
        target = self.target()
        large = target / "large.dat"
        large.write_bytes(b"x" * 1_100_000)

        def reject_full_read(path: Path) -> bytes:
            if path == large:
                raise AssertionError("large weak material was fully read")
            return b"unexpected"

        context = SimpleNamespace(target_root=target)
        with mock.patch.object(Path, "read_bytes", reject_full_read):
            record = substrate._describe_resource(context, large, "file")

        self.assertIsNone(record["content_hash"])
        self.assertEqual(record["domain"]["content_basis"], "metadata_only")
        self.assertTrue(record["domain"]["weak_material"])

        self.attach(target)
        self.substrate(target, "refresh")
        resource = self.substrate(target, "resources", "read", "path:large.dat")["resource"]
        self.assertIsNone(resource["latest"]["content_hash"])

        observations = self.substrate(target, "observations", "list", "--limit", "50")["observations"]
        large_observations = [item for item in observations if item["subject_handle"] == "path:large.dat"]
        self.assertTrue(any(item["observation_type"] == "file_metadata" for item in large_observations))
        self.assertFalse(any(item["observation_type"] == "file_hash" for item in large_observations))

    def test_current_domain_profile_does_not_leak_historical_software_shape(self) -> None:
        target = self.target()
        (target / "pyproject.toml").write_text("[project]\nname = 'old'\n", encoding="utf-8")
        (target / "app.py").write_text("print('old')\n", encoding="utf-8")
        self.attach(target)
        self.substrate(target, "refresh")

        (target / "pyproject.toml").unlink()
        (target / "app.py").unlink()
        (target / "records.csv").write_text("id,value\n1,new\n", encoding="utf-8")
        (target / "brief.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
        self.substrate(target, "refresh")

        revision = self.awareness(target, "refresh")["revision"]
        self.assertEqual(revision["summary"]["domain_profile"], "records_documents")
        self.assertFalse(any(item["title"] == "target_profile_software" for item in revision["findings"]))
        self.assertNotIn("path:app.py", revision["source_handles"])

    def test_domain_truth_does_not_create_runtime_memory_or_mutation_state(self) -> None:
        target = self.target()
        (target / "docs").mkdir()
        (target / "docs" / "note.md").write_text("hello\n", encoding="utf-8")
        self.attach(target)
        self.substrate(target, "refresh")
        self.awareness(target, "refresh")

        _, receipts = self.sidecar_raw(target, "receipts", "list")
        _, journal = self.sidecar_raw(target, "journal", "list")
        _, mutation = self.sidecar_raw(target, "mutation", "status")
        self.assertEqual(receipts["receipts"], [])
        self.assertEqual(journal["entries"], [])
        self.assertEqual(mutation["counts"]["mutation_records"], 0)

        database = target / ".sidecar" / "state" / "workbench.sqlite3"
        connection = sqlite3.connect(database)
        try:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM operational_artifacts").fetchone()[0],
                0,
            )
            self.assertFalse((target / ".sidecar" / "state" / "mcp.sqlite3").exists())
        finally:
            connection.close()

    def test_cli_and_mcp_read_same_domain_world_without_owning_it(self) -> None:
        target = self.target()
        (target / "pyproject.toml").write_text("[project]\nname = 'mcp-demo'\n", encoding="utf-8")
        (target / "main.py").write_text("print('hi')\n", encoding="utf-8")
        self.attach(target)
        self.substrate(target, "refresh")
        _, cli_awareness = self.sidecar_raw(target, "awareness", "refresh")

        session = McpSession(target / ".sidecar" / "bin" / "sidecar.py", self.root)
        try:
            resources = session.request(
                "tools/call",
                {"name": "substrate.resources.list", "arguments": {"limit": 20}},
                71,
            )
            current = session.request(
                "tools/call",
                {"name": "awareness.current", "arguments": {}},
                72,
            )
        finally:
            session.close()

        mcp_resources = resources["result"]["structuredContent"]["resources"]
        self.assertIn("path:pyproject.toml", {item["handle"] for item in mcp_resources})
        self.assertEqual(
            current["result"]["structuredContent"]["revision"]["awareness_id"],
            cli_awareness["revision"]["awareness_id"],
        )
        self.assertEqual(
            current["result"]["structuredContent"]["revision"]["summary"]["domain_profile"],
            "software",
        )


if __name__ == "__main__":
    unittest.main()
