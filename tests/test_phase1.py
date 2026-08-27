from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class InstalledFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime_root = REPOSITORY_ROOT / "tests" / ".runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.root = self.runtime_root / f"case-{uuid.uuid4().hex}"
        self.root.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        try:
            self.runtime_root.rmdir()
        except OSError:
            pass

    def target(self, name: str = "target") -> Path:
        path = self.root / name
        path.mkdir()
        return path

    def attach(self, target: Path) -> dict:
        process = subprocess.run(
            [sys.executable, "-m", "factory", "attach", str(target)],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr or process.stdout)
        return json.loads(process.stdout)

    def sidecar(self, target: Path, *arguments: str, cwd: Path | None = None) -> tuple[subprocess.CompletedProcess, dict]:
        front_door = target / ".sidecar" / "bin" / "sidecar.py"
        process = subprocess.run(
            [sys.executable, str(front_door), *arguments],
            cwd=cwd or self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        try:
            document = json.loads(process.stdout)
        except json.JSONDecodeError as exc:
            self.fail(f"sidecar did not emit JSON: {exc}\nstdout={process.stdout!r}\nstderr={process.stderr!r}")
        return process, document

    def call(
        self,
        target: Path,
        tool: str,
        arguments: dict,
        authority: str = "observe",
    ) -> tuple[subprocess.CompletedProcess, dict]:
        return self.sidecar(
            target,
            "call",
            tool,
            "--authority",
            authority,
            "--args",
            json.dumps(arguments, separators=(",", ":")),
        )

    @staticmethod
    def target_snapshot(target: Path) -> dict[str, tuple[str, int]]:
        snapshot = {}
        for path in sorted(target.rglob("*")):
            try:
                path.relative_to(target / ".sidecar")
                continue
            except ValueError:
                pass
            relative = path.relative_to(target).as_posix()
            if path.is_file():
                snapshot[relative] = (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
            elif path.is_dir():
                snapshot[relative + "/"] = ("directory", path.stat().st_mtime_ns)
        return snapshot


class PhaseOneAcceptanceTests(InstalledFixture):
    def test_normal_target_uses_discovered_tools_and_sqlite_state(self) -> None:
        target = self.target()
        (target / "docs").mkdir()
        (target / "docs" / "hello.txt").write_bytes(b"Alpha\nneedle here\n")

        attached = self.attach(target)
        self.assertTrue(attached["ok"])
        manifest = json.loads((target / ".sidecar" / "instance.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["target_relation"], "..")
        self.assertNotIn("target_root", manifest)
        self.assertFalse(any(str(target) in str(value) for value in manifest.values()))

        process, status = self.sidecar(target, "status")
        self.assertEqual(process.returncode, 0)
        self.assertTrue(status["database_identity_matches"])
        self.assertEqual(status["tool_count"], 5)

        database = target / ".sidecar" / "state" / "workbench.sqlite3"
        connection = sqlite3.connect(database)
        try:
            row = connection.execute("SELECT instance_uuid, target_relation FROM instances").fetchone()
            schema = connection.execute("PRAGMA user_version").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(row, (manifest["instance_uuid"], ".."))
        self.assertEqual(schema, 4)

        _, catalog = self.sidecar(target, "tools")
        self.assertEqual(
            {tool["id"] for tool in catalog["tools"]},
            {"inventory", "read_file", "search_text", "hash_file", "write_file"},
        )

        _, inventory = self.call(target, "inventory", {})
        resources = inventory["result"]["resources"]
        self.assertIn("path:docs/hello.txt", {item["handle"] for item in resources})
        self.assertFalse(any(item["path"].startswith(".sidecar") for item in resources))

        _, read = self.call(target, "read_file", {"path": "docs/hello.txt"})
        self.assertEqual(read["result"]["content"], "Alpha\nneedle here\n")
        _, search = self.call(target, "search_text", {"query": "needle"})
        self.assertEqual(search["result"]["matches"][0]["handle"], "path:docs/hello.txt#L2")
        _, hashed = self.call(target, "hash_file", {"path": "docs/hello.txt"})
        self.assertEqual(
            hashed["result"]["digest"],
            hashlib.sha256(b"Alpha\nneedle here\n").hexdigest(),
        )

    def test_empty_target_is_a_successful_thin_observation(self) -> None:
        target = self.target()
        self.attach(target)
        process, inventory = self.call(target, "inventory", {})
        self.assertEqual(process.returncode, 0)
        self.assertTrue(inventory["ok"])
        self.assertEqual(inventory["result"]["resources"], [])
        self.assertEqual(inventory["result"]["limitations"], [])
        self.assertFalse(inventory["result"]["truncated"])

    def test_path_traversal_absolute_paths_and_private_subtree_are_refused(self) -> None:
        target = self.target()
        outside = self.root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        self.attach(target)

        cases = {
            "../outside.txt": "escapes",
            str(outside.resolve()): "absolute",
            ".sidecar/instance.json": "private subtree",
        }
        for raw, witness in cases.items():
            with self.subTest(path=raw):
                process, response = self.call(target, "read_file", {"path": raw})
                self.assertNotEqual(process.returncode, 0)
                self.assertEqual(response["error"]["code"], "containment_refusal")
                self.assertIn(witness, response["error"]["message"])

        process, response = self.call(
            target,
            "write_file",
            {"path": "../outside.txt", "content": "changed", "confirm": True},
            authority="apply",
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(response["error"]["code"], "containment_refusal")
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside")

    def test_symlink_escape_is_refused_when_host_supports_symlinks(self) -> None:
        target = self.target()
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_text("outside-only-witness", encoding="utf-8")
        link = target / "link"
        try:
            os.symlink(outside, link, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"directory symlinks are unavailable: {exc}")
        try:
            self.attach(target)

            process, response = self.call(
                target,
                "write_file",
                {"path": "link/escaped.txt", "content": "no", "confirm": True},
                authority="apply",
            )
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual(response["error"]["code"], "containment_refusal")
            self.assertFalse((outside / "escaped.txt").exists())

            _, search = self.call(target, "search_text", {"query": "outside-only-witness"})
            self.assertEqual(search["result"]["matches"], [])
            self.assertTrue(
                any("symbolic links" in limitation for limitation in search["result"]["limitations"])
            )
        finally:
            link.unlink(missing_ok=True)

    def test_reentry_and_relocation_preserve_structural_identity(self) -> None:
        target = self.target("original")
        (target / "idea.txt").write_text("begin", encoding="utf-8")
        self.attach(target)
        _, first = self.sidecar(target, "status", cwd=self.root)
        _, second = self.sidecar(target, "status", cwd=target)
        self.assertEqual(first["instance_uuid"], second["instance_uuid"])

        moved = self.root / "renamed-and-moved"
        target.rename(moved)
        process, relocated = self.sidecar(moved, "status", cwd=REPOSITORY_ROOT)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(relocated["instance_uuid"], first["instance_uuid"])
        self.assertEqual(relocated["target_relation"], "..")
        self.assertEqual(Path(relocated["target_root"]), moved.resolve())

    def test_cli_calls_the_live_manifest_governed_control_plane(self) -> None:
        target = self.target()
        (target / "note.txt").write_text("hello", encoding="utf-8")
        self.attach(target)
        manifest_path = target / ".sidecar" / "tools" / "read_file" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["authority"] = "apply"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        process, denied = self.call(target, "read_file", {"path": "note.txt"})
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(denied["error"]["code"], "authority_denied")
        self.assertEqual(denied["required_authority"], "apply")

        process, allowed = self.call(
            target, "read_file", {"path": "note.txt"}, authority="apply"
        )
        self.assertEqual(process.returncode, 0)
        self.assertTrue(allowed["ok"])
        self.assertEqual(allowed["control_plane"]["version"], 1)
        self.assertEqual(allowed["result"]["content"], "hello")

        process, invalid = self.call(
            target, "read_file", {"path": "note.txt", "invented": True}, authority="apply"
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(invalid["error"]["code"], "input_contract")

    def test_observation_leaves_no_target_owned_footprint(self) -> None:
        target = self.target()
        (target / "source").mkdir()
        (target / "source" / "data.txt").write_text("stable evidence\n", encoding="utf-8")
        before = self.target_snapshot(target)

        self.attach(target)
        self.sidecar(target, "status")
        self.sidecar(target, "tools")
        self.call(target, "inventory", {})
        self.call(target, "read_file", {"path": "source/data.txt"})
        self.call(target, "search_text", {"query": "evidence"})
        self.call(target, "hash_file", {"path": "source/data.txt"})

        self.assertEqual(self.target_snapshot(target), before)
        self.assertEqual(set(path.name for path in target.iterdir()), {"source", ".sidecar"})
        self.assertFalse((target / ".gitignore").exists())

    def test_only_explicit_apply_and_confirmation_create_a_work_product(self) -> None:
        target = self.target()
        self.attach(target)
        arguments = {"path": "created.txt", "content": "intentional\n", "confirm": True}

        process, denied = self.call(target, "write_file", arguments)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(denied["error"]["code"], "authority_denied")
        self.assertFalse((target / "created.txt").exists())

        process, unconfirmed = self.call(
            target,
            "write_file",
            {"path": "created.txt", "content": "intentional\n", "confirm": False},
            authority="apply",
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(unconfirmed["error"]["code"], "input_contract")
        self.assertFalse((target / "created.txt").exists())

        process, applied = self.call(target, "write_file", arguments, authority="apply")
        self.assertEqual(process.returncode, 0)
        self.assertTrue(applied["ok"])
        self.assertEqual(applied["result"]["handle"], "path:created.txt")
        self.assertEqual((target / "created.txt").read_text(encoding="utf-8"), "intentional\n")

    def test_malformed_identity_fails_instead_of_guessing(self) -> None:
        target = self.target()
        self.attach(target)
        manifest = target / ".sidecar" / "instance.json"
        manifest.write_text("{broken", encoding="utf-8")

        process, response = self.sidecar(target, "status", cwd=target.parent)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(response["error"]["code"], "InstanceError")
        self.assertIn("invalid JSON", response["error"]["message"])

    def test_sqlite_identity_disagreement_refuses_reentry(self) -> None:
        target = self.target()
        self.attach(target)
        database = target / ".sidecar" / "state" / "workbench.sqlite3"
        connection = sqlite3.connect(database)
        try:
            connection.execute("UPDATE instances SET instance_uuid = ?", ("wrong",))
            connection.commit()
        finally:
            connection.close()

        process, response = self.sidecar(target, "status")
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(response["error"]["code"], "StorageError")
        self.assertIn("does not agree", response["error"]["message"])


if __name__ == "__main__":
    unittest.main()
