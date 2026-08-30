from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests.test_phase1 import InstalledFixture


class McpSession:
    def __init__(self, front_door: Path, cwd: Path) -> None:
        self.process = subprocess.Popen(
            [sys.executable, str(front_door), "mcp"],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

    def request(self, method: str, params: dict | None = None, request_id: int = 1) -> dict:
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        self.process.stdin.write(
            json.dumps(
                {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}},
                separators=(",", ":"),
            )
            + "\n"
        )
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            stderr = self.process.stderr.read() if self.process.stderr else ""
            raise AssertionError(f"MCP server produced no response; stderr={stderr!r}")
        return json.loads(line)

    def notification(self, method: str, params: dict | None = None) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(
            json.dumps(
                {"jsonrpc": "2.0", "method": method, "params": params or {}},
                separators=(",", ":"),
            )
            + "\n"
        )
        self.process.stdin.flush()

    def raw(self, payload: str) -> dict:
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        self.process.stdin.write(payload + "\n")
        self.process.stdin.flush()
        return json.loads(self.process.stdout.readline())

    def close(self) -> None:
        try:
            self.request("shutdown", request_id=999)
        finally:
            try:
                assert self.process.stdin is not None
                self.process.stdin.close()
            except OSError:
                pass
            self.process.wait(timeout=5)


class T6McpEntranceTests(InstalledFixture):
    def open_mcp(self, target: Path) -> McpSession:
        return McpSession(target / ".sidecar" / "bin" / "sidecar.py", self.root)

    def test_mcp_initializes_and_projects_live_manifest_catalog(self) -> None:
        target = self.target()
        (target / "note.txt").write_text("hello\n", encoding="utf-8")
        self.attach(target)
        manifest_path = target / ".sidecar" / "tools" / "read_file" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["description"] = "UNIQUE T6 LIVE MANIFEST DESCRIPTION"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        session = self.open_mcp(target)
        try:
            initialized = session.request("initialize", {"clientInfo": {"name": "fixture"}}, 1)
            self.assertEqual(initialized["result"]["protocolVersion"], "2024-11-05")
            listed = session.request("tools/list", request_id=2)
        finally:
            session.close()

        tools = {tool["name"]: tool for tool in listed["result"]["tools"]}
        self.assertIn("tool.read_file", tools)
        self.assertEqual(tools["tool.read_file"]["description"], manifest["description"])
        self.assertTrue(tools["tool.write_file"]["inputSchema"]["additionalProperties"] is False)
        self.assertNotIn("_authority", tools["tool.write_file"]["inputSchema"]["properties"])
        self.assertNotIn("authority", tools["tool.write_file"]["inputSchema"]["properties"])
        self.assertIn("sidecar.status", tools)
        self.assertIn("receipts.list", tools)
        self.assertIn("journal.read", tools)
        self.assertIn("substrate.status", tools)
        self.assertIn("awareness.current", tools)
        self.assertIn("mutation.status", tools)

    def test_mcp_tool_call_routes_through_control_plane_and_same_receipts(self) -> None:
        target = self.target()
        (target / "note.txt").write_bytes(b"mcp-visible\n")
        self.attach(target)

        session = self.open_mcp(target)
        try:
            response = session.request(
                "tools/call",
                {"name": "tool.read_file", "arguments": {"path": "note.txt"}},
                3,
            )
            mcp_receipts = session.request(
                "tools/call",
                {"name": "receipts.list", "arguments": {"limit": 5}},
                4,
            )
        finally:
            session.close()

        structured = response["result"]["structuredContent"]
        self.assertTrue(structured["ok"], structured)
        self.assertEqual(structured["client"], "mcp")
        self.assertEqual(structured["result"]["content"], "mcp-visible\n")
        self.assertTrue(structured["receipt_id"].startswith("operation:"))
        self.assertTrue(structured["artifact_id"].startswith("artifact:"))

        _, cli_receipts = self.sidecar(target, "receipts", "list", "--limit", "5")
        cli_ids = {receipt["receipt_id"] for receipt in cli_receipts["receipts"]}
        self.assertIn(structured["receipt_id"], cli_ids)
        self.assertIn(structured["receipt_id"], {r["receipt_id"] for r in mcp_receipts["result"]["structuredContent"]["receipts"]})

    def test_mcp_apply_authority_uses_call_envelope_and_records_receipt(self) -> None:
        target = self.target()
        self.attach(target)

        session = self.open_mcp(target)
        try:
            refused = session.request(
                "tools/call",
                {
                    "name": "tool.write_file",
                    "arguments": {"path": "created.txt", "content": "no\n", "confirm": True},
                },
                31,
            )
            refused_structured = refused["result"]["structuredContent"]
            self.assertFalse(refused_structured["ok"])
            self.assertEqual(refused_structured["error"]["code"], "authority_denied")
            self.assertFalse((target / "created.txt").exists())
            applied = session.request(
                "tools/call",
                {
                    "name": "tool.write_file",
                    "arguments": {"path": "created.txt", "content": "yes\n", "confirm": True},
                    "authority": "apply",
                },
                32,
            )
        finally:
            session.close()

        applied_structured = applied["result"]["structuredContent"]
        self.assertTrue(applied_structured["ok"], applied_structured)
        self.assertEqual(applied_structured["client"], "mcp")
        self.assertEqual(applied_structured["authority"], "apply")
        self.assertEqual(applied_structured["result"]["handle"], "path:created.txt")
        self.assertEqual((target / "created.txt").read_text(encoding="utf-8"), "yes\n")

        _, receipt = self.sidecar(target, "receipts", "read", applied_structured["receipt_id"])
        self.assertEqual(receipt["receipt"]["client"], "mcp")
        self.assertEqual(receipt["receipt"]["authority"], "apply")
        self.assertEqual(receipt["receipt"]["status"], "success")
        self.assertEqual(receipt["receipt"]["tool_id"], "write_file")
        self.assertEqual(receipt["receipt"]["artifact_id"], applied_structured["artifact_id"])

    def test_mcp_reads_existing_world_through_owner_surfaces(self) -> None:
        target = self.target()
        (target / "doc.txt").write_text("alpha\n", encoding="utf-8")
        self.attach(target)
        self.sidecar(target, "journal", "add", "--title", "Decision", "--body", "Keep alpha.")
        self.sidecar(target, "substrate", "refresh")
        _, awareness = self.sidecar(target, "awareness", "refresh")

        session = self.open_mcp(target)
        try:
            journal = session.request(
                "tools/call",
                {"name": "journal.list", "arguments": {"limit": 5}},
                5,
            )
            substrate_status = session.request(
                "tools/call",
                {"name": "substrate.status", "arguments": {}},
                6,
            )
            awareness_current = session.request(
                "tools/call",
                {"name": "awareness.current", "arguments": {}},
                7,
            )
            mutation_status = session.request(
                "tools/call",
                {"name": "mutation.status", "arguments": {}},
                8,
            )
        finally:
            session.close()

        self.assertEqual(journal["result"]["structuredContent"]["entries"][0]["title"], "Decision")
        self.assertEqual(substrate_status["result"]["structuredContent"]["counts"]["resources"], 1)
        self.assertEqual(
            awareness_current["result"]["structuredContent"]["revision"]["awareness_id"],
            awareness["revision"]["awareness_id"],
        )
        self.assertEqual(
            mutation_status["result"]["structuredContent"]["counts"]["mutation_records"],
            0,
        )

    def test_cli_survives_when_mcp_adapter_is_removed(self) -> None:
        target = self.target()
        (target / "note.txt").write_bytes(b"still here\n")
        self.attach(target)
        mcp_source = target / ".sidecar" / "core" / "mcp.py"
        if mcp_source.exists():
            mcp_source.unlink()

        process, status = self.sidecar(target, "status")
        self.assertEqual(process.returncode, 0, status)
        self.assertTrue(status["ok"])
        process, read = self.call(target, "read_file", {"path": "note.txt"})
        self.assertEqual(process.returncode, 0, read)
        self.assertEqual(read["result"]["content"], "still here\n")
        process, receipts = self.sidecar(target, "receipts", "list")
        self.assertEqual(process.returncode, 0, receipts)
        self.assertTrue(receipts["ok"])
        process, unavailable = self.sidecar(target, "mcp")
        self.assertEqual(process.returncode, 1, unavailable)
        self.assertEqual(unavailable["error"]["code"], "mcp_unavailable")

    def test_mcp_malformed_and_unknown_requests_fail_truthfully(self) -> None:
        target = self.target()
        self.attach(target)
        session = self.open_mcp(target)
        try:
            malformed = session.raw("{not json")
            unknown = session.request("unknown/method", request_id=10)
        finally:
            session.close()

        self.assertEqual(malformed["error"]["code"], -32700)
        self.assertIn("parse", malformed["error"]["message"].lower())
        self.assertEqual(unknown["id"], 10)
        self.assertEqual(unknown["error"]["code"], -32601)

    def test_mcp_initialization_notification_is_silent_and_allows_listing(self) -> None:
        target = self.target()
        self.attach(target)
        session = self.open_mcp(target)
        try:
            initialized = session.request("initialize", request_id=21)
            session.notification("notifications/initialized")
            listed = session.request("tools/list", request_id=22)
        finally:
            session.close()

        self.assertEqual(initialized["id"], 21)
        self.assertEqual(listed["id"], 22)
        self.assertIn("tools", listed["result"])

    def test_no_mcp_state_or_automatic_memory_is_created_by_listing(self) -> None:
        target = self.target()
        self.attach(target)
        session = self.open_mcp(target)
        try:
            session.request("initialize", request_id=11)
            session.request("tools/list", request_id=12)
        finally:
            session.close()

        _, journal = self.sidecar(target, "journal", "list")
        _, substrate = self.sidecar(target, "substrate", "status")
        _, mutation_status = self.sidecar(target, "mutation", "status")
        self.assertEqual(journal["entries"], [])
        self.assertEqual(substrate["counts"]["resources"], 0)
        self.assertEqual(mutation_status["counts"]["mutation_records"], 0)
        self.assertFalse((target / ".sidecar" / "state" / "mcp.sqlite3").exists())


if __name__ == "__main__":
    unittest.main()
