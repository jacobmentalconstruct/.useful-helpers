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
            [sys.executable, "-m", "factory", "release", "build", "--output", str(output)],
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
            [sys.executable, "-m", "factory", *arguments],
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
            shutdown = session.request("shutdown", request_id=47)
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
        self.assertTrue(shutdown["result"]["shutdown"])

        receipts = self.release_sidecar(target, "receipts", "list", "--limit", "10")["receipts"]
        self.assertIn(structured["mutation"]["receipt_id"], {item["receipt_id"] for item in receipts})


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
