from __future__ import annotations

import json
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path

from tests.test_phase1 import InstalledFixture
from tests.test_t6_mcp_entrance import McpSession


class T8ReleaseStopTests(InstalledFixture):
    def build_release(self) -> tuple[Path, Path]:
        output = self.root / "release-output"
        process = subprocess.run(
            [sys.executable, "-B", "-m", "factory", "release", "build", "--output", str(output)],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr or process.stdout)
        document = json.loads(process.stdout)
        artifact = Path(document["artifact"])
        self.assertTrue(artifact.is_file())
        manifest = Path(document["manifest"])
        self.assertTrue(manifest.is_file())
        return artifact, manifest

    def extract_release(self, artifact: Path) -> Path:
        extracted = self.root / "extracted-release"
        extracted.mkdir()
        with zipfile.ZipFile(artifact) as bundle:
            bundle.extractall(extracted)
        return extracted

    def release_factory(self, extracted: Path, *arguments: str) -> dict:
        process = subprocess.run(
            [sys.executable, "-B", "-m", "factory", *arguments],
            cwd=extracted,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        try:
            document = json.loads(process.stdout)
        except json.JSONDecodeError as exc:
            self.fail(f"factory did not emit JSON: {exc}\n{process.stdout}\n{process.stderr}")
        self.assertEqual(process.returncode, 0, document)
        self.assertTrue(document["ok"], document)
        return document

    def release_sidecar(self, target: Path, *arguments: str) -> dict:
        process, document = self.sidecar(target, *arguments)
        self.assertEqual(process.returncode, 0, document)
        self.assertTrue(document["ok"], document)
        return document

    @staticmethod
    def write_software_target(target: Path) -> None:
        (target / "pyproject.toml").write_text("[project]\nname = 'sealed'\n", encoding="utf-8")
        (target / "README.md").write_text("# sealed software\n", encoding="utf-8")
        (target / "src").mkdir()
        (target / "src" / "app.py").write_text("def main():\n    return 1\n", encoding="utf-8")
        (target / "tests").mkdir()
        (target / "tests" / "test_app.py").write_text("def test_app():\n    assert True\n", encoding="utf-8")

    @staticmethod
    def write_mixed_document_target(target: Path) -> None:
        (target / "tools").mkdir()
        (target / "tools" / "export.py").write_text("print('export')\n", encoding="utf-8")
        (target / "records").mkdir()
        (target / "records" / "clients.csv").write_text("id,name\n1,Ada\n", encoding="utf-8")
        (target / "records" / "invoices.csv").write_text("id,total\n1,10\n", encoding="utf-8")
        (target / "contracts").mkdir()
        (target / "contracts" / "agreement.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

    def test_sealed_artifact_positive_boundary_and_no_construction_history(self) -> None:
        artifact, manifest_path = self.build_release()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        with zipfile.ZipFile(artifact) as bundle:
            names = set(bundle.namelist())
            embedded = json.loads(bundle.read("RELEASE_MANIFEST.json").decode("utf-8"))

        self.assertIn("product/bin/sidecar.py", names)
        self.assertIn("factory/__main__.py", names)
        self.assertIn("factory/release.py", names)
        self.assertIn("product/core/mcp.py", names)
        self.assertIn("product/core/mutation.py", names)
        self.assertIn("RELEASE_MANIFEST.json", names)
        self.assertEqual(manifest["artifact"]["sha256"], _sha256(artifact))
        self.assertEqual(embedded["product"], "sidecar-workbench")
        forbidden_fragments = (
            ".builder/",
            "tests/",
            ".git/",
            "release/",
            "_projectmapper/",
            "_exports/",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
        )
        leaked = sorted(name for name in names if any(fragment in name for fragment in forbidden_fragments))
        self.assertEqual(leaked, [])
        for member in names:
            self.assertNotIn(str(REPOSITORY_ROOT), member)
            self.assertNotIn("C:\\", member)

    def test_sealed_install_blank_state_relocation_update_and_removal(self) -> None:
        artifact, _ = self.build_release()
        extracted = self.extract_release(artifact)
        target = self.target("consumer")
        (target / "note.txt").write_text("hello\n", encoding="utf-8")

        attached = self.release_factory(extracted, "attach", str(target))
        first_uuid = attached["instance_uuid"]
        self.assertEqual(set(path.name for path in target.iterdir()), {"note.txt", ".sidecar"})
        self.assertFalse((target / ".gitignore").exists())

        status = self.release_sidecar(target, "status")
        self.assertEqual(status["instance_uuid"], first_uuid)
        self.assertEqual(status["target_relation"], "..")
        self.assertEqual(self.release_sidecar(target, "journal", "list")["entries"], [])
        self.assertEqual(self.release_sidecar(target, "receipts", "list")["receipts"], [])

        moved = self.root / "moved-consumer"
        target.rename(moved)
        self.assertEqual(self.release_sidecar(moved, "status")["instance_uuid"], first_uuid)

        self.release_sidecar(
            moved,
            "journal",
            "add",
            "--type",
            "decision",
            "--status",
            "decided",
            "--title",
            "Keep state",
            "--body",
            "State should survive update.",
        )
        self.release_factory(extracted, "update", str(moved))
        self.assertEqual(self.release_sidecar(moved, "status")["instance_uuid"], first_uuid)
        self.assertEqual(self.release_sidecar(moved, "journal", "list")["entries"][0]["title"], "Keep state")

        self.release_factory(extracted, "uninstall", str(moved))
        self.assertFalse((moved / ".sidecar").exists())
        self.assertEqual((moved / "note.txt").read_text(encoding="utf-8"), "hello\n")

    def test_sealed_update_replaces_installed_payload_while_preserving_state(self) -> None:
        artifact, _ = self.build_release()
        extracted = self.extract_release(artifact)
        target = self.target("replace-payload")
        (target / "note.txt").write_text("payload replacement witness\n", encoding="utf-8")
        attached = self.release_factory(extracted, "attach", str(target))
        first_uuid = attached["instance_uuid"]

        self.release_sidecar(
            target,
            "journal",
            "add",
            "--type",
            "decision",
            "--status",
            "decided",
            "--title",
            "Preserve me",
            "--body",
            "Runtime state survives payload replacement.",
        )
        installed_payload = target / ".sidecar" / "core" / "constants.py"
        release_payload = extracted / "product" / "core" / "constants.py"
        stale_marker = target / ".sidecar" / "core" / "stale_payload_marker.py"
        original_release_bytes = release_payload.read_bytes()
        self.assertEqual(installed_payload.read_bytes(), original_release_bytes)

        installed_payload.write_text("BROKEN_PAYLOAD = True\n", encoding="utf-8")
        stale_marker.write_text("SHOULD_NOT_SURVIVE_UPDATE = True\n", encoding="utf-8")
        self.release_factory(extracted, "update", str(target))

        self.assertEqual(installed_payload.read_bytes(), original_release_bytes)
        self.assertFalse(stale_marker.exists())
        self.assertEqual(self.release_sidecar(target, "status")["instance_uuid"], first_uuid)
        entries = self.release_sidecar(target, "journal", "list")["entries"]
        self.assertEqual(entries[0]["title"], "Preserve me")

    def test_sealed_cli_orients_empty_software_and_mixed_document_targets(self) -> None:
        artifact, _ = self.build_release()
        extracted = self.extract_release(artifact)
        cases = {
            "empty": ("empty_or_nascent", lambda target: None),
            "software": ("software", self.write_software_target),
            "mixed": ("mixed", self.write_mixed_document_target),
        }
        for name, (expected_profile, writer) in cases.items():
            with self.subTest(name=name):
                target = self.target(f"sealed-{name}")
                writer(target)
                self.release_factory(extracted, "attach", str(target))
                self.release_sidecar(target, "substrate", "refresh")
                refreshed = self.release_sidecar(target, "awareness", "refresh")["revision"]
                current = self.release_sidecar(target, "awareness", "current")["revision"]
                self.assertEqual(current["awareness_id"], refreshed["awareness_id"])
                self.assertEqual(current["freshness"], "current")
                self.assertEqual(current["summary"]["domain_profile"], expected_profile)
                self.assertTrue(refreshed["findings"])
                drill = self.release_sidecar(
                    target,
                    "awareness",
                    "drill",
                    refreshed["findings"][0]["item_id"],
                )["drill"]
                self.assertEqual(drill["item"]["awareness_id"], refreshed["awareness_id"])
                self.assertTrue(drill["nodes"])

    def test_sealed_cli_and_mcp_complete_the_same_governed_mutation_walk(self) -> None:
        artifact, _ = self.build_release()
        extracted = self.extract_release(artifact)
        target = self.target("work")
        (target / "notes").mkdir()
        (target / "notes" / "a.md").write_text("# A\n", encoding="utf-8")
        self.release_factory(extracted, "attach", str(target))

        self.release_sidecar(target, "substrate", "refresh")
        self.release_sidecar(target, "awareness", "refresh")
        preview = self.release_sidecar(
            target,
            "mutation",
            "preview-write",
            "--path",
            "notes/a.md",
            "--content",
            "# B\n",
            "--overwrite",
        )["preview"]
        approval = self.release_sidecar(target, "mutation", "approve", preview["preview_id"])["approval"]
        stale_target = target / "stale"
        stale_target.write_text("stale\n", encoding="utf-8")
        refused = subprocess.run(
            [
                sys.executable,
                str(target / ".sidecar" / "bin" / "sidecar.py"),
                "mutation",
                "apply",
                approval["approval_id"],
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        stale = json.loads(refused.stdout)
        self.assertNotEqual(refused.returncode, 0)
        self.assertEqual(stale["error"]["code"], "stale_target")
        stale_target.unlink()
        self.release_sidecar(target, "substrate", "refresh")
        self.release_sidecar(target, "awareness", "refresh")

        session = McpSession(target / ".sidecar" / "bin" / "sidecar.py", self.root)
        closed = False
        try:
            initialized = session.request("initialize", {"clientInfo": {"name": "t8-fixture"}}, 41)
            listed = session.request("tools/list", request_id=42)
            previewed = session.request(
                "tools/call",
                {
                    "name": "mutation.preview_write",
                    "arguments": {
                        "path": "notes/a.md",
                        "content": "# C\n",
                        "overwrite": True,
                    },
                },
                43,
            )
            approved = session.request(
                "tools/call",
                {
                    "name": "mutation.approve",
                    "arguments": {
                        "preview_id": previewed["result"]["structuredContent"]["preview"]["preview_id"]
                    },
                },
                44,
            )
            applied = session.request(
                "tools/call",
                {
                    "name": "mutation.apply",
                    "arguments": {
                        "approval_id": approved["result"]["structuredContent"]["approval"]["approval_id"]
                    },
                },
                45,
            )
            history = session.request(
                "tools/call",
                {"name": "mutation.history", "arguments": {"limit": 10}},
                46,
            )
            invalid = session.request(
                "tools/call",
                {
                    "name": "mutation.preview_write",
                    "arguments": {"path": "notes/a.md"},
                },
                47,
            )
            shutdown = session.request("shutdown", request_id=48)
            closed = True
        finally:
            if closed:
                assert session.process.stdin is not None
                session.process.stdin.close()
                session.process.wait(timeout=5)
            else:
                session.close()

        tools = {tool["name"] for tool in listed["result"]["tools"]}
        self.assertEqual(initialized["result"]["protocolVersion"], "2024-11-05")
        self.assertIn("mutation.preview_write", tools)
        self.assertIn("mutation.approve", tools)
        self.assertIn("mutation.apply", tools)
        structured = applied["result"]["structuredContent"]
        self.assertTrue(structured["ok"], structured)
        self.assertEqual(structured["mutation"]["measurement"]["changed_paths"], ["notes/a.md"])
        self.assertEqual(structured["mutation"]["verification"]["status"], "unavailable")
        self.assertTrue(structured["mutation"]["receipt_id"].startswith("operation:"))
        self.assertTrue(structured["mutation"]["post_awareness_id"].startswith("awareness:"))
        self.assertEqual((target / "notes" / "a.md").read_text(encoding="utf-8"), "# C\n")
        self.assertTrue(history["result"]["structuredContent"]["mutations"])
        self.assertEqual(invalid["error"]["code"], -32602)
        self.assertIn("content is required", invalid["error"]["message"])
        self.assertTrue(shutdown["result"]["shutdown"])

        receipts = self.release_sidecar(target, "receipts", "list", "--limit", "10")["receipts"]
        self.assertIn(structured["mutation"]["receipt_id"], {item["receipt_id"] for item in receipts})

    def test_sealed_cli_survives_when_mcp_adapter_is_removed(self) -> None:
        artifact, _ = self.build_release()
        extracted = self.extract_release(artifact)
        target = self.target("no-mcp")
        (target / "note.txt").write_text("mcp removal witness\n", encoding="utf-8")
        self.release_factory(extracted, "attach", str(target))
        (target / ".sidecar" / "core" / "mcp.py").unlink()

        status = self.release_sidecar(target, "status")
        tools = self.release_sidecar(target, "tools")["tools"]
        process, read = self.call(target, "read_file", {"path": "note.txt"})
        self.assertEqual(process.returncode, 0, read)
        self.assertEqual(read["result"]["content"].splitlines(), ["mcp removal witness"])
        self.assertTrue(status["instance_uuid"])
        self.assertIn("read_file", {tool["id"] for tool in tools})

        failed = subprocess.run(
            [sys.executable, "-B", str(target / ".sidecar" / "bin" / "sidecar.py"), "mcp"],
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertNotEqual(failed.returncode, 0)
        document = json.loads(failed.stdout)
        self.assertFalse(document["ok"])
        self.assertEqual(document["error"]["code"], "mcp_unavailable")


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
