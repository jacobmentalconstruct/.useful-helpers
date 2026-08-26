from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from tests.test_phase1 import InstalledFixture, REPOSITORY_ROOT


def _run_mechanical(tool_id: str, arguments: dict, context: dict) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPOSITORY_ROOT / "product")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(REPOSITORY_ROOT / "product" / "tools" / tool_id / "tool.py")],
        input=json.dumps({"args": arguments, "context": context}),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=context["target_root"],
        env=environment,
        check=False,
    )


def _document(process: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(process.stdout)


def _install_fixture_tool(target: Path, tool_id: str, manifest: dict, source: str) -> None:
    tool_root = target / ".sidecar" / "tools" / tool_id
    tool_root.mkdir()
    (tool_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (tool_root / "tool.py").write_text(source, encoding="utf-8")


class MechanicalLayerTests(InstalledFixture):
    def test_five_tools_run_with_product_neutral_context(self) -> None:
        target = self.target()
        hidden = target / ".host-private"
        hidden.mkdir()
        (hidden / "secret.txt").write_bytes(b"needle should stay hidden\n")
        visible = target / "visible.txt"
        visible.write_bytes(b"Alpha\nneedle here\n")
        context = {
            "target_root": str(target.resolve()),
            "excluded_roots": [str(hidden.resolve())],
        }

        inventory = _document(_run_mechanical("inventory", {}, context))
        self.assertTrue(inventory["ok"])
        self.assertIn("path:visible.txt", {item["handle"] for item in inventory["resources"]})
        self.assertFalse(any(item["path"].startswith(".host-private") for item in inventory["resources"]))

        read = _document(
            _run_mechanical("read_file", {"path": str(visible.resolve())}, context)
        )
        self.assertEqual(read["content"], "Alpha\nneedle here\n")

        search = _document(_run_mechanical("search_text", {"query": "needle"}, context))
        self.assertEqual([match["handle"] for match in search["matches"]], ["path:visible.txt#L2"])

        hashed = _document(
            _run_mechanical("hash_file", {"path": str(visible.resolve())}, context)
        )
        self.assertEqual(hashed["digest"], hashlib.sha256(visible.read_bytes()).hexdigest())

        created = target / "created.txt"
        written = _document(
            _run_mechanical(
                "write_file",
                {"path": str(created.resolve()), "content": "intentional\n", "confirm": True},
                context,
            )
        )
        self.assertTrue(written["ok"])
        self.assertEqual(written["handle"], "path:created.txt")
        self.assertEqual(created.read_text(encoding="utf-8"), "intentional\n")

    def test_inventory_reports_an_external_symlink_without_following_it(self) -> None:
        target = self.target()
        outside = self.root / "outside.txt"
        outside.write_text("external evidence", encoding="utf-8")
        link = target / "external-link.txt"
        try:
            os.symlink(outside, link)
        except OSError as exc:
            self.skipTest(f"file symlinks are unavailable: {exc}")
        context = {"target_root": str(target.resolve()), "excluded_roots": []}

        process = _run_mechanical("inventory", {}, context)
        result = _document(process)
        self.assertEqual(process.returncode, 0, result)
        resource = next(item for item in result["resources"] if item["path"] == "external-link.txt")
        self.assertEqual(resource["kind"], "symlink")
        self.assertEqual(resource["handle"], "path:external-link.txt")

    def test_mechanical_context_rejects_sidecar_identity_fields(self) -> None:
        target = self.target()
        source = target / "source.txt"
        source.write_text("known", encoding="utf-8")
        process = _run_mechanical(
            "hash_file",
            {"path": str(source.resolve())},
            {
                "target_root": str(target.resolve()),
                "excluded_roots": [],
                "instance_uuid": "identity-does-not-belong-here",
            },
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("unknown fields", _document(process)["error"])


class GovernedHostTests(InstalledFixture):
    def test_host_transports_only_mechanical_context(self) -> None:
        target = self.target()
        self.attach(target)
        manifest = {
            "contract_version": 1,
            "id": "context_probe",
            "description": "Report transported context keys for a host-boundary fixture.",
            "authority": "observe",
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
            "output_schema": {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "context_keys": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["ok", "context_keys"],
                "additionalProperties": False,
            },
            "reads": ["target"],
            "writes": [],
            "applicability": {"domains": ["test"]},
            "path_arguments": {},
            "invocation": {"kind": "python", "entry": "tools/context_probe/tool.py"},
        }
        source = (
            "import json, sys\n"
            "request = json.loads(sys.stdin.read())\n"
            "print(json.dumps({'ok': True, 'context_keys': sorted(request['context'])}))\n"
        )
        _install_fixture_tool(target, "context_probe", manifest, source)

        process, response = self.call(target, "context_probe", {})
        self.assertEqual(process.returncode, 0, response)
        self.assertEqual(response["result"]["context_keys"], ["excluded_roots", "target_root"])

    def test_refusals_happen_before_a_malicious_child_can_run(self) -> None:
        target = self.target()
        self.attach(target)
        witness = self.root / "child-launched.txt"
        manifest = {
            "contract_version": 1,
            "id": "witness",
            "description": "Leave a witness if governance launches this fixture.",
            "authority": "apply",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string", "minLength": 1}},
                "required": ["path"],
                "additionalProperties": False,
            },
            "output_schema": {
                "type": "object",
                "properties": {"ok": {"type": "boolean"}},
                "required": ["ok"],
            },
            "reads": ["target"],
            "writes": ["target"],
            "applicability": {"domains": ["test"]},
            "path_arguments": {"path": "target"},
            "invocation": {"kind": "python", "entry": "tools/witness/tool.py"},
        }
        source = (
            "import json\n"
            "from pathlib import Path\n"
            f"Path({str(witness)!r}).write_text('launched', encoding='utf-8')\n"
            "print(json.dumps({'ok': True}))\n"
        )
        _install_fixture_tool(target, "witness", manifest, source)

        cases = (
            ("authority", "observe", {"path": "safe.txt"}, "authority_denied"),
            ("input", "apply", {}, "input_contract"),
            ("containment", "apply", {"path": "../escape.txt"}, "containment_refusal"),
        )
        for name, authority, arguments, expected_code in cases:
            with self.subTest(case=name):
                process, response = self.call(target, "witness", arguments, authority=authority)
                self.assertNotEqual(process.returncode, 0)
                self.assertEqual(response["error"]["code"], expected_code)
                self.assertFalse(witness.exists(), f"child launched during {name} refusal")

        (target / ".sidecar" / "instance.json").write_text("{broken", encoding="utf-8")
        process, response = self.call(
            target, "witness", {"path": "safe.txt"}, authority="apply"
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(response["error"]["code"], "InstanceError")
        self.assertFalse(witness.exists(), "child launched despite invalid instance identity")
