"""
FILE:       tests/test_smoke.py
ROLE:       Spine smoke suite  -  the dogfooding check, made repeatable.
DOMAIN:     testing
DOES:       Drives the real surfaces without stdio: registry discovery, the invoke() seam
            (incl. the actual subprocess to a tool), and MCPHandler (initialize / tools.list /
            tools.call / error / notification). Fails if the control plane can't be used.
DEPENDS ON: src.core.{config,registry,invoke}, src.interfaces.mcp_server, (stdlib) unittest
WIRES TO:   run via `python -m unittest discover -s tests -t .` or `python smoke_test.py`
NOTES:      Uses the built-in `ping` proof tool as the fixture. invoke() really spawns a
            subprocess, so this validates the end-to-end loop, not just imports - the
            operator's dogfooding-is-done metric.
"""

from __future__ import annotations

import unittest
import uuid

from src.core import invoke as invoke_mod
from src.core import registry
from src.core.config import resolve_paths
from src.interfaces.mcp_server import MCPHandler


def _target_manifest(root: str, *, exclude: str) -> dict:
    """sha256 of every file under `root`, keyed by relative posix path, skipping the sidecar's
    own folder (`exclude`). The mechanical precept check: any delta here is a violation."""
    import hashlib
    import os
    from pathlib import Path

    out: dict[str, str] = {}
    base = Path(root)
    for cur, dirs, files in os.walk(root):
        if exclude in Path(cur).relative_to(base).parts:
            dirs[:] = []
            continue
        for name in files:
            p = Path(cur) / name
            rel = p.relative_to(base).as_posix()
            try:
                out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
            except OSError:
                out[rel] = "UNREADABLE"
    return out


class SpineSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # This is the toolkit's OWN self-test suite, so the work target is the toolkit itself  -
        # tools must exercise the toolkit's real files (src/core, smoke_test.py, requirements.txt).
        # In sidecar use the work target is the parent project instead (see
        # test_project_root_resolution). Scope SUITE_PROJECT_ROOT only around resolve_paths() so the
        # captured cls.paths.project_root is the toolkit home while ambient env stays clean for the
        # tests that assert on _resolve_project_root directly.
        import os
        import tempfile
        from pathlib import Path

        home = Path(__file__).resolve().parents[1]
        if os.environ.get("SUITE_TEST_TMP"):
            tmp_root = Path(os.environ["SUITE_TEST_TMP"])
        else:
            # INSIDE the sidecar, never beside it. This used to read `home.parent`,
            # which was correct only while the sidecar was nested one level down:
            # `home` was toolkit/, so the scratch landed at the repository root.
            # Now that the sidecar IS the root, `home.parent` would place scratch
            # in the operator's staging folder - outside the project entirely.
            #
            # Note this directory is on the project's own filesystem, and
            # `tempfile.tempdir` is redirected here for the whole suite. On a
            # network or FUSE-mounted checkout that makes every temp operation
            # slow enough to stall the run; set SUITE_TEST_TMP to a local path
            # (e.g. /tmp) to keep scratch on fast storage.
            tmp_root = home / ".useful-helpers-test-tmp"
        cls._suite_tmp_root = tmp_root
        cls._suite_tmp_owned = not bool(os.environ.get("SUITE_TEST_TMP"))
        cls._orig_tempdir = tempfile.tempdir
        cls._orig_mkdtemp = tempfile.mkdtemp
        tmp_root.mkdir(parents=True, exist_ok=True)
        tempfile.tempdir = str(tmp_root)

        def _suite_mkdtemp(suffix=None, prefix=None, dir=None):
            parent = Path(dir) if dir else tmp_root
            parent.mkdir(parents=True, exist_ok=True)
            name = f"{prefix or 'tmp'}{uuid.uuid4().hex}{suffix or ''}"
            path = parent / name
            path.mkdir()
            return str(path)

        tempfile.mkdtemp = _suite_mkdtemp
        prev = os.environ.get("SUITE_PROJECT_ROOT")
        os.environ["SUITE_PROJECT_ROOT"] = str(home)
        try:
            cls.paths = resolve_paths()
        finally:
            if prev is None:
                os.environ.pop("SUITE_PROJECT_ROOT", None)
            else:
                os.environ["SUITE_PROJECT_ROOT"] = prev

        # The derived registry is untracked, so a CLEAN CLONE does not have one.
        # These tests run in-process and never go through src/app.py, which is where
        # an entrance would generate it. Without this, two tests fail on a fresh
        # checkout while passing in any tree that had ever generated the file - the
        # exact blind spot that let a broken clean clone look green.
        registry.ensure_manifest(cls.paths)

    @classmethod
    def tearDownClass(cls) -> None:
        import shutil
        import tempfile

        tempfile.tempdir = getattr(cls, "_orig_tempdir", None)
        tempfile.mkdtemp = getattr(cls, "_orig_mkdtemp", tempfile.mkdtemp)
        tmp_root = getattr(cls, "_suite_tmp_root", None)
        if tmp_root is not None and getattr(cls, "_suite_tmp_owned", False):
            shutil.rmtree(tmp_root, ignore_errors=True)
        # Final sweep of _artifacts/test_tmp: per-test cleanup can miss a dir whose sqlite handle
        # was still held on Windows. By class teardown those are released, so nothing accumulates.
        shutil.rmtree(cls.paths.root / "_artifacts" / "test_tmp", ignore_errors=True)

    def _tmp_path(self, name: str) -> str:
        # Registered for cleanup: without this every run leaked a uuid dir under _artifacts
        # (822 of them / 20MB had accumulated)  -  the exact generated-residue rot this toolkit
        # exists to prevent, in its own tree. ignore_errors: Windows may still hold a sqlite handle.
        import shutil

        root = self.paths.root / "_artifacts" / "test_tmp" / uuid.uuid4().hex
        root.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        return str(root / name)

    def _install_product(self, target, mode: str = "install"):
        """Install through the STANDALONE SETUP APPLICATION - the product's entrance.

        Replaces four call sites that used `tools/sidecar_install`, a runtime tool
        retired in T6. A test claiming something about installation must exercise the
        implementation users actually get; every green install this project recorded
        before T6 came from a path that was not the product's, and that path produced
        an instance with no target.
        """
        import os
        import subprocess
        import sys
        import tempfile
        from pathlib import Path as _P

        from src.core import payload as _payload

        src_root = _P(self.paths.root)
        pay = _payload.materialise(src_root, _P(tempfile.mkdtemp(prefix="uh-pay-")) / "tk")
        env = {k: v for k, v in os.environ.items() if not k.startswith("SUITE_")}
        return subprocess.run(
            [sys.executable, str(src_root / "packaging" / "installer" / "install.py"),
             "--target", str(target), "--payload", str(pay), "--mode", mode],
            cwd=str(src_root), capture_output=True, text=True, timeout=900, env=env)

    def _foreign_target(self) -> str:
        """A directory GENUINELY OUTSIDE the toolkit tree, for install tests.

        setUpClass redirects `tempfile` into the sidecar's own home, which is right
        for ordinary scratch - the sidecar writing only inside itself is the precept.
        But `sidecar_install` refuses a target that overlaps its own source tree, and
        rightly so: vending a copy of yourself into yourself is nonsense. So the
        redirect made every install test's target illegal, and the three that install
        a sidecar failed on a DEFAULT run.

        Nobody saw it because every path used to verify this project - the operator's
        command, the harness, and both CI jobs - sets SUITE_TEST_TMP to somewhere
        outside the tree, which is exactly the condition that hides it.

        These tests need the real OS temp. Both halves of the redirect have to be
        undone for the call: the stashed pre-redirect `mkdtemp` still consults
        `tempfile.tempdir`, which is also patched, so restoring only one of them
        lands right back inside the tree.
        """
        import shutil
        import tempfile as _tf

        cls = type(self)
        mk = getattr(cls, "_orig_mkdtemp", _tf.mkdtemp)
        patched_dir = _tf.tempdir
        _tf.tempdir = getattr(cls, "_orig_tempdir", None)
        try:
            target = mk(prefix="uh-foreign-")
        finally:
            _tf.tempdir = patched_dir
        self.addCleanup(shutil.rmtree, target, ignore_errors=True)
        return target

    # ----- registry -----
    def test_registry_discovers_ping(self):
        ids = [t.id for t in registry.list_tools(self.paths)]
        self.assertIn("ping", ids)

    def test_registry_ping_record_shape(self):
        rec = registry.get(self.paths, "ping")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.authority, "Observe")
        self.assertIn("entry", rec.invocation)

    # ----- invoke() seam (real subprocess) -----
    def test_invoke_ping_ok(self):
        res = invoke_mod.invoke(self.paths, "ping", {"message": "smoke"})
        self.assertTrue(res.ok, res.error)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.output.get("echo"), "smoke")

    def test_invoke_unknown_tool_is_graceful(self):
        res = invoke_mod.invoke(self.paths, "does_not_exist", {})
        self.assertFalse(res.ok)
        self.assertIn("unknown tool", res.error)

    # ----- MCP agent entrance (no stdio) -----
    def test_mcp_initialize(self):
        resp = MCPHandler(self.paths).handle_message(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        )
        self.assertEqual(resp["result"]["serverInfo"]["name"], "usefulhelpers-suite")

    def test_mcp_tools_list_contains_ping(self):
        resp = MCPHandler(self.paths).handle_message(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        )
        names = [t["name"] for t in resp["result"]["tools"]]
        self.assertIn("ping", names)

    def test_mcp_tools_call_ping(self):
        resp = MCPHandler(self.paths).handle_message(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "ping", "arguments": {"message": "mcp-smoke"}},
            }
        )
        result = resp["result"]
        self.assertFalse(result["isError"])
        self.assertIn("mcp-smoke", result["content"][0]["text"])

    def test_mcp_tools_call_unknown_is_error(self):
        resp = MCPHandler(self.paths).handle_message(
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "ghost"}}
        )
        self.assertTrue(resp["result"]["isError"])

    def test_mcp_notification_returns_none(self):
        resp = MCPHandler(self.paths).handle_message(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}
        )
        self.assertIsNone(resp)

    # ----- T4 re-homed tools (dogfood coverage) -----
    def test_invoke_host_probe_ok(self):
        res = invoke_mod.invoke(self.paths, "host_probe", {})
        self.assertTrue(res.ok, res.error)
        self.assertIn("python", res.output)
        self.assertIn("tools_present", res.output)

    def test_invoke_file_tree_finds_self(self):
        res = invoke_mod.invoke(self.paths, "file_tree", {"ext": ".py", "kind": "file"})
        self.assertTrue(res.ok, res.error)
        found = [r["path"] for r in res.output["rows"]]
        self.assertIn("smoke_test.py", found)

    def test_stamp_registered_as_apply(self):
        rec = registry.get(self.paths, "stamp")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.authority, "Apply")

    def test_invoke_linenumber_roundtrip(self):
        orig = "alpha\n    beta\ngamma\n"
        a = invoke_mod.invoke(self.paths, "linenumber", {"action": "annotate", "text": orig})
        self.assertTrue(a.ok, a.error)
        s = invoke_mod.invoke(
            self.paths, "linenumber", {"action": "strip", "text": a.output["numbered"]}
        )
        self.assertEqual(s.output["stripped"], orig)

    def test_invoke_ollama_gov_tiers(self):
        res = invoke_mod.invoke(self.paths, "ollama_gov", {"action": "tiers"})
        self.assertTrue(res.ok, res.error)
        self.assertIn("VRAM Only (Fastest)", res.output["tiers"])

    def test_invoke_edit_preview(self):
        res = invoke_mod.invoke(
            self.paths, "edit", {"text": "foo bar foo", "pattern": "foo", "replacement": "X"}
        )
        self.assertTrue(res.ok, res.error)
        self.assertEqual(res.output["replacements"], 2)
        self.assertEqual(res.output["result"], "X bar X")
        self.assertFalse(res.output["written"])

    def test_invoke_report_dir(self):
        res = invoke_mod.invoke(self.paths, "report", {"path": "src/core"})
        self.assertTrue(res.ok, res.error)
        self.assertGreater(res.output["summary"]["files"], 0)
        self.assertIn("class", res.output["markdown"])

    def test_invoke_operational_audit_pack(self):
        search = invoke_mod.invoke(
            self.paths, "repo_search", {"query": "class SpineSmokeTest", "glob": "*.py", "limit": 5}
        )
        self.assertTrue(search.ok, search.error)
        self.assertGreaterEqual(search.output["count"], 1)

        audit = invoke_mod.invoke(self.paths, "workspace_audit", {})
        self.assertTrue(audit.ok, audit.error)
        self.assertTrue(audit.output["control_plane"]["registry"])

        profile = invoke_mod.invoke(self.paths, "command_profile", {})
        self.assertTrue(profile.ok, profile.error)
        self.assertTrue(any(c["id"] == "smoke" for c in profile.output["commands"]))

        deps = invoke_mod.invoke(self.paths, "dependency_check", {})
        self.assertTrue(deps.ok, deps.error)
        self.assertIn("requirements.txt", deps.output["declarations"]["python"])

        secrets = invoke_mod.invoke(self.paths, "secret_audit", {"root": "src", "limit": 5})
        self.assertTrue(secrets.ok, secrets.error)
        self.assertIn("finding_count", secrets.output)

    def test_invoke_journal_add_show_close(self):
        dbp = self._tmp_path("j.sqlite3")
        a = invoke_mod.invoke(
            self.paths,
            "journal",
            {
                "action": "add",
                "title": "smoke",
                "summary": "s",
                "files": ["a.py"],
                "decisions": ["d1"],
                "db": dbp,
            },
        )
        self.assertTrue(a.ok, a.error)
        uid = a.output["uid"]
        s = invoke_mod.invoke(self.paths, "journal", {"action": "show", "uid": uid, "db": dbp})
        self.assertEqual(s.output["entry"]["title"], "smoke")
        self.assertEqual(s.output["entry"]["files_changed"], ["a.py"])
        cl = invoke_mod.invoke(
            self.paths, "journal", {"action": "close", "uid": uid, "status": "parked", "db": dbp}
        )
        self.assertTrue(cl.ok, cl.error)
        self.assertEqual(cl.output["status"], "parked")

    def test_invoke_evidence_attach_verify(self):
        dbp = self._tmp_path("e.sqlite3")
        a = invoke_mod.invoke(
            self.paths,
            "evidence",
            {
                "action": "attach",
                "kind": "tool_output",
                "summary": "s",
                "body": "hello evidence",
                "db": dbp,
            },
        )
        self.assertTrue(a.ok, a.error)
        eid = a.output["evidence_id"]
        v = invoke_mod.invoke(
            self.paths, "evidence", {"action": "verify", "evidence_id": eid, "db": dbp}
        )
        self.assertTrue(v.output["verified"])
        self.assertEqual(v.output["status"], "verified")
        g = invoke_mod.invoke(
            self.paths, "evidence", {"action": "get", "evidence_id": eid, "db": dbp}
        )
        self.assertEqual(g.output["content"], "hello evidence")
        a2 = invoke_mod.invoke(
            self.paths, "evidence", {"action": "attach", "body": "hello evidence", "db": dbp}
        )
        self.assertEqual(a2.output["hash"], a.output["hash"])  # content-addressed
        self.assertTrue(a2.output["deduped"])

    def test_invoke_projectmapper_compile_deterministic(self):
        import os

        out1 = self._tmp_path("snap.sqlite3")
        r = invoke_mod.invoke(
            self.paths,
            "projectmapper",
            {"action": "compile", "root": "src/core", "name": "coretest", "out": out1},
        )
        self.assertTrue(r.ok, r.error)
        self.assertGreater(r.output["text_file_count"], 0)
        self.assertTrue(os.path.exists(out1))
        out2 = self._tmp_path("snap.sqlite3")
        r2 = invoke_mod.invoke(
            self.paths,
            "projectmapper",
            {"action": "compile", "root": "src/core", "name": "coretest", "out": out2},
        )
        self.assertEqual(r2.output["content_checksum"], r.output["content_checksum"])

    def test_invoke_packaging_core(self):
        from pathlib import Path

        root_a = Path(self._tmp_path("pkg-a")).parent
        root_b = Path(self._tmp_path("pkg-b")).parent
        (root_a / "a.txt").write_text("alpha\n", encoding="utf-8")
        (root_b / "a.txt").write_text("alpha changed\n", encoding="utf-8")
        (root_b / "b.txt").write_text("beta\n", encoding="utf-8")
        out_a = self._tmp_path("pkg_a.sqlite3")
        out_b = self._tmp_path("pkg_b.sqlite3")

        snap_a = invoke_mod.invoke(
            self.paths,
            "projectmapper",
            {"action": "compile", "root": str(root_a), "name": "pkg_a", "out": out_a},
        )
        self.assertTrue(snap_a.ok, snap_a.error)
        snap_b = invoke_mod.invoke(
            self.paths,
            "projectmapper",
            {"action": "compile", "root": str(root_b), "name": "pkg_b", "out": out_b},
        )
        self.assertTrue(snap_b.ok, snap_b.error)

        verify = invoke_mod.invoke(self.paths, "snapshot_verify", {"db": out_a})
        self.assertTrue(verify.ok, verify.error)
        self.assertEqual(verify.output["summary"]["failed"], 0)

        diff = invoke_mod.invoke(self.paths, "snapshot_diff", {"left": out_a, "right": out_b})
        self.assertTrue(diff.ok, diff.error)
        self.assertEqual(diff.output["summary"]["added"], 1)
        self.assertEqual(diff.output["summary"]["modified"], 1)

        catalog = invoke_mod.invoke(
            self.paths, "artifact_catalog", {"root": "_artifacts", "limit": 20}
        )
        self.assertTrue(catalog.ok, catalog.error)
        self.assertIn("summary", catalog.output)

        export = invoke_mod.invoke(
            self.paths, "vendor_export", {"root": str(root_b), "dry_run": True, "zip": False}
        )
        self.assertTrue(export.ok, export.error)
        self.assertFalse(export.output["summary"]["written"])
        self.assertGreaterEqual(export.output["summary"]["file_count"], 2)

    def test_c1_hands(self):
        # C1 (seam-completeness): read_file / write_file / glob work through the seam, and the
        # shared path resolver blocks escapes outside the roots.
        from src.core import invoke as invoke_mod

        rf = invoke_mod.invoke(self.paths, "read_file", {"path": "requirements.txt"})
        self.assertTrue(rf.ok, rf.error)
        self.assertGreater(rf.output["total_lines"], 0)

        # line range
        rng = invoke_mod.invoke(self.paths, "read_file",
                                {"path": "requirements.txt", "offset": 1, "limit": 1})
        self.assertEqual(rng.output["start_line"], 1)
        self.assertEqual(rng.output["end_line"], 1)

        # escape guard
        esc = invoke_mod.invoke(self.paths, "read_file", {"path": "../../../etc/passwd"})
        self.assertFalse(esc.ok)

        g = invoke_mod.invoke(self.paths, "glob", {"pattern": "tools/read_file/*.json"})
        self.assertTrue(g.ok, g.error)
        self.assertIn("tools/read_file/tool.json", g.output["matches"])
        # BOUNDARY REGRESSION: a pattern must not walk out of the root and expose outside paths.
        esc = invoke_mod.invoke(self.paths, "glob", {"pattern": "../*"})
        self.assertTrue(esc.ok, esc.error)
        self.assertEqual(esc.output["matches"], [])

        # write: preview then apply, into the toolkit's gitignored _artifacts, then clean up
        rel = "_artifacts/_c1_probe.txt"
        prev = invoke_mod.invoke(self.paths, "write_file", {"path": rel, "content": "probe"})
        self.assertTrue(prev.ok and prev.output["dry_run"] and not prev.output["written"])
        done = invoke_mod.invoke(self.paths, "write_file",
                                 {"path": rel, "content": "probe", "write": True})
        self.assertTrue(done.ok and done.output["written"], done.error)
        target_file = self.paths.root / rel
        try:
            self.assertEqual(target_file.read_text(encoding="utf-8"), "probe")
        finally:
            target_file.unlink(missing_ok=True)

    def test_c3_mutation(self):
        # C3: edit's expected_replacements safety belt refuses on a count mismatch, and fs_op runs
        # a batch (one plan, one apply)  -  both through the seam, into the gitignored _artifacts.
        from src.core import invoke as invoke_mod

        base = "_artifacts/_c3"
        # set up a file to edit via fs_op mkdir + write_file
        mk = invoke_mod.invoke(self.paths, "fs_op", {"op": "mkdir", "path": base, "apply": True})
        self.assertTrue(mk.ok, mk.error)
        wf = invoke_mod.invoke(self.paths, "write_file",
                               {"path": f"{base}/f.txt", "content": "foo foo foo", "write": True})
        self.assertTrue(wf.ok, wf.error)
        try:
            # count mismatch -> refuse, file unchanged
            bad = invoke_mod.invoke(self.paths, "edit",
                                    {"path": f"{base}/f.txt", "pattern": "foo", "replacement": "bar",
                                     "literal": True, "expected_replacements": 1, "write": True})
            self.assertFalse(bad.ok)
            self.assertEqual((self.paths.root / base / "f.txt").read_text(), "foo foo foo")
            # correct count -> apply
            ok = invoke_mod.invoke(self.paths, "edit",
                                   {"path": f"{base}/f.txt", "pattern": "foo", "replacement": "bar",
                                    "literal": True, "expected_replacements": 3, "apply": True})
            self.assertTrue(ok.ok and ok.output["written"], ok.error)
            self.assertEqual((self.paths.root / base / "f.txt").read_text(), "bar bar bar")
            # fs_op batch: copy + the escape guard
            batch = invoke_mod.invoke(self.paths, "fs_op", {"ops": [
                {"op": "copy", "path": f"{base}/f.txt", "dest": f"{base}/g.txt"},
                {"op": "touch", "path": f"{base}/h.txt"}], "apply": True})
            self.assertTrue(batch.ok and batch.output["applied"] == 2, batch.error)
            esc = invoke_mod.invoke(self.paths, "fs_op",
                                    {"op": "delete", "path": "../../../..", "apply": True})
            self.assertFalse(esc.ok)
            # SAFETY REGRESSION: deleting a root would rmtree the whole target. Never allowed.
            for root_path in (".", "", "sub/.."):
                r = invoke_mod.invoke(self.paths, "fs_op",
                                      {"op": "delete", "path": root_path or ".", "apply": True})
                self.assertFalse(r.ok, f"fs_op must refuse to delete a root ({root_path!r})")
            self.assertTrue((self.paths.root / "requirements.txt").is_file())  # target intact
        finally:
            invoke_mod.invoke(self.paths, "fs_op", {"op": "delete", "path": base, "apply": True})

    def test_c4_data(self):
        # C4: sqlite_exec (preview via rollback = accurate + non-destructive; apply commits;
        # SELECT refused) and diff (unified text diff)  -  through the seam.
        import sqlite3

        from src.core import invoke as invoke_mod

        db = self.paths.root / "_artifacts" / "_c4.sqlite3"
        db.parent.mkdir(parents=True, exist_ok=True)
        db.unlink(missing_ok=True)
        def _count_z():
            c = sqlite3.connect(db)
            try:
                return c.execute("SELECT COUNT(*) FROM t WHERE name='z'").fetchone()[0]
            finally:
                c.close()

        con = sqlite3.connect(db)
        con.execute("CREATE TABLE t (id INTEGER, name TEXT)")
        con.executemany("INSERT INTO t VALUES (?,?)", [(1, "a"), (2, "b")])
        con.commit()
        con.close()
        try:
            rel = "_artifacts/_c4.sqlite3"
            # preview: reports affected but does NOT persist
            prev = invoke_mod.invoke(self.paths, "sqlite_exec",
                                     {"db": rel, "sql": "UPDATE t SET name=? WHERE id>0", "params": ["z"]})
            self.assertTrue(prev.ok and prev.output["dry_run"] and prev.output["would_affect_rows"] == 2)
            self.assertEqual(_count_z(), 0)  # rollback: nothing persisted
            # apply commits
            ap = invoke_mod.invoke(self.paths, "sqlite_exec",
                                   {"db": rel, "sql": "UPDATE t SET name=? WHERE id>0",
                                    "params": ["z"], "apply": True})
            self.assertTrue(ap.ok and ap.output["affected_rows"] == 2)
            self.assertEqual(_count_z(), 2)
            # SELECT refused
            self.assertFalse(invoke_mod.invoke(self.paths, "sqlite_exec",
                                               {"db": rel, "sql": "SELECT 1"}).ok)
        finally:
            db.unlink(missing_ok=True)

        d = invoke_mod.invoke(self.paths, "diff",
                              {"a_text": "a\nb\nc\n", "b_text": "a\nX\nc\n"})
        self.assertTrue(d.ok)
        self.assertEqual((d.output["added"], d.output["removed"]), (1, 1))
        self.assertFalse(d.output["identical"])

    def test_c5_dep_install_batch(self):
        # C5: the HITL BATCH gate  -  one dry-run listing the COMPLETE dependency set (with
        # sources), never one prompt per dep; and the rail that refuses the system interpreter.
        # Preview only: no network, no install.
        import shutil

        from src.core import invoke as invoke_mod

        missing_venv = "_artifacts/_c5_venv"  # deliberately does not exist
        # rail: no venv and no create_venv -> refuse rather than touch the system interpreter
        r = invoke_mod.invoke(self.paths, "dep_install",
                              {"packages": ["click"], "venv": missing_venv})
        self.assertFalse(r.ok)
        self.assertIn("system interpreter", (r.error or "") + str(r.output))

        # batch preview: explicit + requirements.txt + pyproject, deduped, with provenance
        r = invoke_mod.invoke(self.paths, "dep_install",
                              {"packages": ["click"], "venv": missing_venv, "create_venv": True})
        self.assertTrue(r.ok, r.error)
        out = r.output
        self.assertTrue(out["dry_run"])
        self.assertFalse(out["installed"])
        self.assertTrue(out["would_create_venv"])
        specs = [p["package"] for p in out["packages"]]
        self.assertIn("click", specs)
        self.assertEqual(len(specs), len(set(specs)))          # deduped
        self.assertEqual(out["count"], len(specs))             # the ONE list to approve
        self.assertTrue(all(p.get("source") for p in out["packages"]))  # provenance on each

        # COMPLETENESS REGRESSION: the batch gate is only honest if `-r` includes are expanded;
        # silently dropping them would have the operator approve a list that isn't the truth.
        fx = self.paths.root / "_artifacts" / "_c5fx"
        fx.mkdir(parents=True, exist_ok=True)
        try:
            (fx / "base.txt").write_text("django>=4\npsycopg2\n", encoding="utf-8")
            (fx / "req.txt").write_text("-r base.txt\nrequests\n-e .\n", encoding="utf-8")
            n = invoke_mod.invoke(self.paths, "dep_install",
                                  {"requirements": "_artifacts/_c5fx/req.txt",
                                   "venv": missing_venv, "create_venv": True})
            self.assertTrue(n.ok, n.error)
            got = [p["package"] for p in n.output["packages"]]
            self.assertIn("django>=4", got)   # pulled through the nested -r
            self.assertIn("psycopg2", got)
            self.assertIn("requests", got)
            # and what could NOT be expanded is surfaced, never silently dropped
            self.assertTrue(any("-e" in u["directive"] for u in n.output.get("unresolved", [])))
        finally:
            shutil.rmtree(fx, ignore_errors=True)

    def test_c6_web_search(self):
        # C6: governed discovery. Unconfigured it refuses HONESTLY (never fabricates results);
        # configured, the preview shows what would be sent where without touching the network.
        import os

        from src.core import invoke as invoke_mod

        prev = {k: os.environ.get(k) for k in
                ("SUITE_SEARCH_PROVIDER", "SUITE_SEARCH_URL", "SUITE_SEARCH_API_KEY")}

        def _restore():
            for k, v in prev.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

        self.addCleanup(_restore)

        for k in prev:
            os.environ.pop(k, None)
        r = invoke_mod.invoke(self.paths, "web_search", {"query": "python packaging"})
        self.assertFalse(r.ok)
        self.assertIn("configure", r.output)          # tells you how to fix it
        self.assertNotIn("results", r.output)         # and never invents any

        os.environ["SUITE_SEARCH_PROVIDER"] = "searxng"
        os.environ["SUITE_SEARCH_URL"] = "http://localhost:8888"
        p = invoke_mod.invoke(self.paths, "web_search", {"query": "python packaging"})
        self.assertTrue(p.ok, p.error)
        self.assertTrue(p.output["dry_run"])
        self.assertFalse(p.output["searched"])        # preview makes no network call
        self.assertEqual(p.output["provider"], "searxng")
        self.assertIn("localhost:8888", p.output["endpoint"])

    def test_c7_delegate(self):
        # C7: the compute payoff. Preview is always checked (no model needed); the live loop runs
        # only when a local model is reachable. Asserts the loop is BOUNDED and that delegated
        # calls go through the governed seam  -  not that the model says any particular thing.
        from src.core import invoke as invoke_mod

        # preview: bounded, and `delegate` can never be in its own allowlist (no self-recursion)
        p = invoke_mod.invoke(self.paths, "delegate",
                              {"task": "anything", "allow": ["read_file", "delegate", "glob"]})
        self.assertTrue(p.ok, p.error)
        self.assertTrue(p.output["dry_run"])
        self.assertFalse(p.output["ran"])
        self.assertNotIn("delegate", p.output["allow"])
        self.assertLessEqual(p.output["max_steps"], 12)

        # SAFETY REGRESSION: a local model must not silently receive write/exec authority.
        el = invoke_mod.invoke(self.paths, "delegate",
                               {"task": "x", "allow": ["project_run", "write_file"]})
        self.assertFalse(el.ok)
        self.assertIn("project_run", el.output.get("elevated", []))
        unknown = invoke_mod.invoke(self.paths, "delegate",
                                    {"task": "x", "allow": ["no_such_tool"]})
        self.assertFalse(unknown.ok)          # unknown reads as elevated, never slips through
        opt_in = invoke_mod.invoke(self.paths, "delegate",
                                   {"task": "x", "allow": ["project_run"], "allow_apply": True})
        self.assertTrue(opt_in.ok)            # deliberate opt-in is honoured

        # PRECONDITION BY THE REAL PATH, not by proxy. Two earlier versions of this
        # guard were wrong in different ways, and each looked reasonable:
        #
        #   v1  guarded on summarize_shared.available() - the SUMMARIZER's default
        #       model (qwen2.5:3b) while delegate requests qwen2.5:7b
        #   v2  guarded on the right model, but still in the TEST's interpreter -
        #       and `delegate` runs under ${ROOT_VENV_PYTHON}, a different one. The
        #       test process could import `ollama`; the venv could not
        #
        # No in-process probe can establish what a tool running under another
        # interpreter will find. So the tool is asked, and its own documented
        # unavailability contract is what decides.
        from tools.delegate import cli as delegate_cli
        wanted = delegate_cli.DEFAULT_MODEL

        r = invoke_mod.invoke(self.paths, "delegate",
                              {"task": "How many files are in the tools directory? Use glob.",
                               "allow": ["glob"], "max_steps": 3, "apply": True})
        out = r.output or {}
        # DEGRADES HONESTLY, or it ran. Anything else is a defect.
        #
        # `configure` is delegate's documented "I cannot run, and here is what to do"
        # signal. Treating it as a skip keeps the environment out of the verdict;
        # asserting its SHAPE keeps the skip from becoming a place defects hide -
        # a delegate that always reported unavailable would still have to say so in
        # the documented form, and would still be visible as a skip rather than a pass.
        if not out.get("ran") and out.get("configure"):
            self.assertFalse(r.ok)
            self.assertTrue(out.get("error"), msg=f"unavailable without a reason: {out!r}")
            self.skipTest(f"delegate cannot run here: {out.get('error')}")

        self.assertTrue(out.get("ran"),
                        msg=f"model={wanted!r} ok={r.ok} error={r.error!r} output={out!r}")
        self.assertLessEqual(out.get("used_steps", 99), 3)      # budget honoured
        steps = out.get("steps") or []
        self.assertTrue(all(s.get("tool", "glob") in ("glob", None) for s in steps))  # allowlist held

    def test_d2_g6_symbol_graph(self):
        # D2/G6: the graph's whole claim is that an edge exists only when a reference actually
        # BINDS to its target. The fixture encodes the three lies the name-counting predecessor
        # told: a mutually-recursive dead pair read as alive, a name coincidence read as a
        # reference, and a relative import attributed to the wrong package.
        from pathlib import Path as _Path

        fx = _Path(self._tmp_path("g6-fixture"))
        (fx / "app" / "core").mkdir(parents=True)
        (fx / "app" / "web").mkdir()
        (fx / "app" / "__init__.py").write_text("", encoding="utf-8")
        (fx / "app" / "core" / "__init__.py").write_text("", encoding="utf-8")
        (fx / "app" / "web" / "__init__.py").write_text("", encoding="utf-8")
        (fx / "app" / "core" / "engine.py").write_text(
            "def start(): return helper()\n"
            "def helper(): return 1\n"
            "def dead_a(): return dead_b()\n"
            "def dead_b(): return dead_a()\n"
            "def orphan(): return 42\n", encoding="utf-8")
        (fx / "app" / "web" / "views.py").write_text(
            "from ..core.engine import start\n"
            "def handle():\n"
            "    orphan = object()\n"   # name coincidence, NOT engine.orphan
            "    print(orphan)\n"
            "    return start()\n"
            "def main(): return handle()\n", encoding="utf-8")

        rel = fx.relative_to(_Path.cwd()).as_posix() if fx.is_absolute() else str(fx)

        # 1. resolved refs: relative import anchored to the REAL package
        g = invoke_mod.invoke(self.paths, "symbol_graph", {"action": "refs", "symbol": "start",
                                                           "root": rel})
        self.assertTrue(g.ok, g.error)
        sym = g.output["symbols"][0]
        self.assertEqual(sym["inbound_count"], 1)
        self.assertIn("app.web.views::handle", [r["src"] for r in sym["inbound"]])
        self.assertIn("honesty", g.output)

        # 2. dead_code proves all three: the dead cluster, the orphan, and NOT the live chain
        d = invoke_mod.invoke(self.paths, "dead_code", {"root": rel})
        self.assertTrue(d.ok, d.error)
        self.assertTrue(d.output["resolved"])
        found = {c["qualname"]: c for c in d.output["candidates"]}
        self.assertIn("dead_a", found)      # mutually-recursive pair: invisible to name counting
        self.assertIn("dead_b", found)
        self.assertIn("orphan", found)      # name coincidence: previously read as a reference
        self.assertEqual(found["dead_a"]["confidence"], "high")
        self.assertIn("dead cluster", found["dead_a"]["reason"])
        self.assertEqual(found["orphan"]["confidence"], "high")
        self.assertNotIn("start", found)    # the live chain must never be a candidate
        self.assertNotIn("helper", found)
        self.assertIn("honesty", d.output)

        # 3. boundary audit: the ..core relative import is anchored to app.core (web -> core),
        #    not to a phantom top-level `core` - scoped to the package so domains split
        sub = fx / "app"
        sub_rel = sub.relative_to(_Path.cwd()).as_posix() if sub.is_absolute() else str(sub)
        b = invoke_mod.invoke(self.paths, "domain_boundary_audit", {"root": sub_rel})
        self.assertTrue(b.ok, b.error)
        edges = {(c["from_domain"], c["to_domain"]) for c in b.output["crossings"]}
        self.assertIn(("web", "core"), edges)

    def test_d2_g5_node_summaries_degrade_honestly(self):
        # D2/G5: with no model reachable, summarize must SAY which modules lack summaries -
        # never invent one, never fail opaquely. (The live path is proven manually + by the
        # CAS cache re-run; this guards the honesty contract that runs everywhere, incl. CI.)
        import os as _os
        from pathlib import Path as _Path

        fx = _Path(self._tmp_path("g5-fixture"))
        fx.mkdir(parents=True, exist_ok=True)
        (fx / "thing.py").write_text('"""A thing."""\ndef go(): return 1\n', encoding="utf-8")
        rel = fx.relative_to(_Path.cwd()).as_posix() if fx.is_absolute() else str(fx)

        env_backup = _os.environ.get("SUITE_LLM_DISABLE")
        _os.environ["SUITE_LLM_DISABLE"] = "1"
        try:
            r = invoke_mod.invoke(self.paths, "symbol_graph",
                                  {"action": "summarize", "root": rel})
            self.assertTrue(r.ok, r.error)
            self.assertTrue(r.output["degraded"])
            self.assertEqual(r.output["summarized"], 0)
            self.assertIn("thing.py", r.output["missing"])   # named, not hidden
            self.assertIn("note", r.output)
        finally:
            if env_backup is None:
                _os.environ.pop("SUITE_LLM_DISABLE", None)
            else:
                _os.environ["SUITE_LLM_DISABLE"] = env_backup

    def test_d1_p1_policy_overrides_survive_refresh(self):
        # D1/P1: refresh used to silently discard operator policy - it punished you for
        # customising. The whole claim of this feature is the word SURVIVE, so the test maps,
        # overrides, refreshes (a full re-detect), and demands the override still be in force.
        import json as _json
        import os as _os
        from pathlib import Path as _Path

        state = _Path(self._tmp_path("p1-overrides"))
        state.mkdir(parents=True, exist_ok=True)
        env_backup = _os.environ.get("SUITE_STATE_ROOT")
        _os.environ["SUITE_STATE_ROOT"] = str(state)
        try:
            first = invoke_mod.invoke(self.paths, "attach", {"refresh": True})
            self.assertTrue(first.ok, first.error)
            self.assertNotIn("policy_overrides", first.output["workbench"])  # none set yet

            (state / "policy_overrides.json").write_text(_json.dumps({
                "*": {"dead_code": {"confidence": "low", "note": "OPERATOR: suspect here",
                                    "tool_args": {"root": "src"}}}
            }), encoding="utf-8")

            # The load-bearing assertion: a FULL re-map must not lose the operator's decision.
            after = invoke_mod.invoke(self.paths, "attach", {"refresh": True})
            self.assertTrue(after.ok, after.error)
            wb = after.output["workbench"]
            self.assertIn("dead_code", wb["policy_overrides"]["tools"])
            entry = wb["policy"]["dead_code"]
            self.assertEqual(entry["confidence"], "low")
            self.assertTrue(entry["overridden"])   # visibly operator policy, not cartridge policy
            self.assertEqual(entry["tool_args"]["root"], "src")
            # key-wise tool_args merge: pinning one arg must not wipe the cartridge's others
            self.assertIn("entrypoint_decorators", entry["tool_args"])

            # It must reach `next`, not just the policy block - an override that is advertised
            # but not pre-bound into the suggested call would be a cosmetic lie.
            calls = [n["call"] for n in after.output["next"]
                     if n.get("call", {}).get("tool") == "dead_code"]
            if calls:
                self.assertEqual(calls[0]["args"].get("root"), "src")

            # Re-engage (no refresh) applies them too.
            re_eng = invoke_mod.invoke(self.paths, "attach", {})
            self.assertTrue(re_eng.ok, re_eng.error)
            self.assertEqual(re_eng.output["mode"], "reengaged")
            self.assertEqual(re_eng.output["workbench"]["policy"]["dead_code"]["confidence"], "low")

            # The PERSISTED profile stays a faithful record of what was DETECTED - overrides are
            # layered at read time, never written back, which is why refresh cannot clobber them.
            profile = _json.loads((state / "workbench" / "profile.json").read_text(encoding="utf-8"))
            self.assertNotIn("overridden", (profile.get("policy") or {}).get("dead_code", {}))

            # A malformed override file must degrade to "no overrides", never take the door down.
            (state / "policy_overrides.json").write_text("{ not json", encoding="utf-8")
            broken = invoke_mod.invoke(self.paths, "attach", {"refresh": True})
            self.assertTrue(broken.ok, "a bad override file must not break the front door")
            self.assertNotIn("policy_overrides", broken.output["workbench"])
        finally:
            if env_backup is None:
                _os.environ.pop("SUITE_STATE_ROOT", None)
            else:
                _os.environ["SUITE_STATE_ROOT"] = env_backup

    def test_d1_o1_single_inference_seam(self):
        # D1/O1: local inference is the one capability that burns real resources AND can silently
        # degrade, so it must pass through exactly one chokepoint. These assertions are the whole
        # point of the tranche: if a module opens its own client again, this test fails.
        import json as _json
        import os as _os
        import subprocess as _sp
        import sys as _sys
        from pathlib import Path as _Path

        from tools import llm_shared

        # 1. Exactly ONE `import ollama` in the shipped tree, and it lives in llm_shared.
        root = _Path(__file__).resolve().parents[1]
        offenders = []
        # Scan the SHIPPED PAYLOAD only. The assertion is about what the sidecar
        # ships, so reference material and development scaffolding are out of scope
        # by definition - and scanning them is not merely wasteful but ruinous:
        # `root` was toolkit/ before the sidecar was collapsed to the repository
        # root, so this walk went from ~136 files to 2,755, of which 95% are the
        # parts bin and harness targets. Every one is read in full. On a network or
        # FUSE-mounted checkout that stalls the suite outright.
        #
        # NOTE: this is the third place that describes what ships, after
        # _harness/_PAYLOAD_EXCLUDE and vendor_export's CLEAN_APP_STRIP. They must
        # converge on one manifest; tracked as a T1 item.
        # Derived from the ONE ship manifest. This was a literal set - one of five
        # copies of the same rule that drifted apart when the layout changed.
        from src.core import payload as _payload
        _NOT_PAYLOAD = set(_payload.PAYLOAD_EXCLUDE) | {"tests"}
        for py in root.rglob("*.py"):
            if any(part in _NOT_PAYLOAD for part in py.parts):
                continue
            for i, line in enumerate(py.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if line.strip() == "import ollama" and py.name != "llm_shared.py":
                    offenders.append(f"{py.relative_to(root)}:{i}")
        self.assertEqual(offenders, [], f"local inference must route through llm_shared: {offenders}")

        # 2. The global kill-switch actually kills, and says why rather than failing opaquely.
        env_backup = _os.environ.get("SUITE_LLM_DISABLE")
        try:
            _os.environ["SUITE_LLM_DISABLE"] = "1"
            llm_shared.reset_probe_cache()
            self.assertTrue(llm_shared.disabled())
            mod, err = llm_shared.client()
            self.assertIsNone(mod)
            self.assertIn("SUITE_LLM_DISABLE", err)
            self.assertFalse(llm_shared.probe("any-model")["available"])
            # a chat under the kill-switch degrades honestly - never raises, never pretends
            out = llm_shared.chat("any-model", "hi", purpose="test.killswitch")
            self.assertFalse(out["ok"])
            self.assertEqual(out["content"], "")
        finally:
            if env_backup is None:
                _os.environ.pop("SUITE_LLM_DISABLE", None)
            else:
                _os.environ["SUITE_LLM_DISABLE"] = env_backup
            llm_shared.reset_probe_cache()

        # 3. The governor can report usage, and every record is attributed to a purpose - an
        #    accounting entry that cannot say WHICH capability spent the tokens is not governance.
        rep = invoke_mod.invoke(self.paths, "ollama_gov", {"action": "usage"})
        self.assertTrue(rep.ok, rep.error)
        self.assertIn("by_purpose", rep.output)
        for row in rep.output.get("recent") or []:
            self.assertTrue(str(row.get("purpose") or "").strip(), f"unattributed usage: {row}")

        # 4. Embeds roll up instead of flooding: many calls, ONE log line. A governance log
        #    nobody can read is not worth writing.
        state = _Path(self._tmp_path("o1-usage"))
        state.mkdir(parents=True, exist_ok=True)
        code = ("import sys; sys.path.insert(0, r'%s')\n"
                "from tools import llm_shared\n"
                "[llm_shared.record_embeds('m', 1, 10) for _ in range(500)]\n" % str(root))
        env = dict(_os.environ, SUITE_STATE_ROOT=str(state))
        proc = _sp.run([_sys.executable, "-c", code], capture_output=True, text=True,
                       cwd=str(root), env=env, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        log = state / llm_shared.USAGE_FILENAME
        self.assertTrue(log.exists(), "embed rollup was never flushed at exit")
        lines = [ln for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1, f"500 embeds should roll up to 1 line, got {len(lines)}")
        rec = _json.loads(lines[0])
        self.assertEqual(rec["calls"], 500)
        self.assertEqual(rec["kind"], "embed")

    def test_semantic_retrieval(self):
        # Phase 6 Ga acceptance: with a real embedding backend, query() returns a PARAPHRASE match
        # that shares no lexical overlap with the source  -  the exact test the sha256 stub could
        # never pass. Skips cleanly when no Ollama is reachable, so CI without it stays green.
        import os
        import tempfile
        from pathlib import Path

        os.environ.pop("SUITE_EMBED_DISABLE", None)
        from tools import bd_graph_shared as bd
        from tools import embed_shared

        embed_shared._probe.update(available=None, backend=None, error=None)  # fresh probe
        if not embed_shared.probe()["available"]:
            self.skipTest(f"no embedding backend: {embed_shared.probe()['error']}")

        corpus = {
            "store.py": 'def build_store():\n    s = Store()\n    s["alpha"] = 1\n    return s',
            "auth.py": "def verify_password(user, secret):\n    return check(secret) == user.digest",
            "net.py": "def fetch_url(link):\n    return client.download(link).body",
        }
        nodes = []
        for name, text in corpus.items():
            for h in bd.split_text(text, name):
                nodes.append(bd.emit_node(h))
        db = Path(tempfile.mkdtemp()) / "sem.sqlite3"
        bd.ingest_nodes(db, nodes)

        # paraphrase of build_store with NO shared tokens (no build/store/Store/alpha/s)
        res = bd.query_db(db, "construct and return a key-value repository object", top_k=3)
        self.assertTrue(res["retrieval"]["semantic"], "expected a semantic backend")
        self.assertEqual(res["anchors"][0]["origin_id"], "store.py",
                         f"paraphrase should rank store.py first: {[a['origin_id'] for a in res['anchors']]}")

    def test_attach_synopsis(self):
        # Phase 6 Gf acceptance (the charter bar): attach() returns a model-written PURPOSE
        # grounded in the target's own signals, so a fresh agent can state what the target IS
        # without reading a file. Skips cleanly when no summary backend is reachable.
        import os
        import tempfile
        from pathlib import Path

        os.environ.pop("SUITE_SUMMARY_DISABLE", None)
        from tools import summarize_shared
        summarize_shared._probe.update(available=None, model=None, error=None)
        if not summarize_shared.available():
            self.skipTest(f"no summary backend: {summarize_shared.probe()['error']}")
        from tools.attach import cli as attach

        work = Path(tempfile.mkdtemp())
        (work / "README.md").write_text(
            "# LinkVault\n\nA command-line password manager that stores credentials encrypted "
            "with AES-256 in a local SQLite vault.\n", encoding="utf-8")
        (work / "app").mkdir()
        (work / "app" / "vault.py").write_text(
            '"""Encrypted credential store: AES-256 encryption of secrets at rest."""\n', encoding="utf-8")

        prev = {k: os.environ.get(k) for k in ("SUITE_STATE_ROOT", "SUITE_HOME", "SUITE_PROJECT_ROOT")}
        os.environ["SUITE_STATE_ROOT"] = tempfile.mkdtemp()
        os.environ["SUITE_HOME"] = str(self.paths.root)
        os.environ["SUITE_PROJECT_ROOT"] = str(work)
        try:
            res = attach.run({"target": str(work)})
        finally:
            for k, v in prev.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        syn = res["project_map"].get("synopsis")
        self.assertIsNotNone(syn, "attach produced no synopsis with a summary backend present")
        self.assertTrue(syn["purpose"].strip())
        self.assertTrue(any(kw in syn["purpose"].lower()
                            for kw in ("password", "vault", "credential", "encrypt", "secret")),
                        f"synopsis missed the target's purpose: {syn['purpose']}")

    def test_knowledge_why_layer(self):
        # Phase 6 Ge: journal/evidence ingested as knowledge nodes linked to code, so why(path)
        # traverses from code to the decisions/evidence behind it. Lexical backend for determinism.
        import os
        import tempfile
        from pathlib import Path

        os.environ["SUITE_EMBED_DISABLE"] = "1"
        self.addCleanup(os.environ.pop, "SUITE_EMBED_DISABLE", None)
        from tools import bd_graph_shared as bd

        work = Path(tempfile.mkdtemp())
        (work / "auth.py").write_text("def verify_password(u, s):\n    return check(s)\n", encoding="utf-8")
        gdb = work / "g.sqlite3"
        # index code (origin_ids relative to cwd)
        cwd = os.getcwd()
        os.chdir(work)
        try:
            bd.ingest_nodes(gdb, bd.emit_nodes(bd.split_path(work)))
        finally:
            os.chdir(cwd)
        journal = [{"uid": "j1", "entry_no": 1, "title": "Use bcrypt",
                    "summary": "Chose bcrypt for hashing.", "files_changed": ["auth.py"],
                    "decisions": ["bcrypt cost=12"], "status": "closed"}]
        evidence = [{"evidence_id": "e1", "kind": "citation", "summary": "OWASP says bcrypt",
                     "source_path": "auth.py", "attached_to": "j1"}]
        res = bd.ingest_knowledge(gdb, journal, evidence)
        self.assertEqual(res["knowledge_nodes"], 2)
        self.assertGreaterEqual(res["relations_added"], 2)

        why = bd.why_db(gdb, "auth.py")
        self.assertGreaterEqual(why["code_matches"], 1)
        kinds = {k["node_kind"] for k in why["knowledge"]}
        self.assertIn("journal_entry", kinds)
        self.assertIn("evidence_item", kinds)
        self.assertTrue(any("bcrypt" in k["summary"] for k in why["knowledge"]))

    def test_invoke_bd_graph_pack(self):
        import os
        from pathlib import Path

        # Force the lexical embedding backend so this test is fast and deterministic  -  the smoke
        # suite must never depend on a running Ollama. invoke() propagates os.environ to the tool
        # subprocesses, so this reaches bd_emit/bd_index. The real semantic path (Ga) is proven
        # separately by test_semantic_retrieval / the harness. Restored in tearDown-ish finally.
        _prev_embed = os.environ.get("SUITE_EMBED_DISABLE")
        os.environ["SUITE_EMBED_DISABLE"] = "1"
        self.addCleanup(lambda: os.environ.__setitem__("SUITE_EMBED_DISABLE", _prev_embed)
                        if _prev_embed is not None else os.environ.pop("SUITE_EMBED_DISABLE", None))

        root = Path(self._tmp_path("bd-root")).parent
        doc = root / "notes.md"
        doc.write_text(
            "# Activation\n\n"
            "Activation propagation links graph nodes through relation edges.\n\n"
            "# Storage\n\n"
            "The scribe writes content nodes and occurrence nodes to SQLite.\n",
            encoding="utf-8",
        )
        db = self._tmp_path("bd.sqlite3")

        split = invoke_mod.invoke(self.paths, "bd_split", {"path": str(doc), "max_size": 200})
        self.assertTrue(split.ok, split.error)
        self.assertGreaterEqual(split.output["summary"]["hunks"], 2)

        emit = invoke_mod.invoke(
            self.paths, "bd_emit", {"hunks": split.output["hunks"], "dimensions": 8}
        )
        self.assertTrue(emit.ok, emit.error)
        self.assertEqual(emit.output["summary"]["nodes"], split.output["summary"]["hunks"])

        guarded = invoke_mod.invoke(
            self.paths, "bd_scribe", {"db": db, "nodes": emit.output["nodes"], "dry_run": False}
        )
        self.assertFalse(guarded.ok)
        self.assertIn("confirm:true", guarded.error)

        dry = invoke_mod.invoke(
            self.paths, "bd_index", {"path": str(root), "db": db, "dry_run": True}
        )
        self.assertTrue(dry.ok, dry.error)
        self.assertFalse(dry.output["summary"]["written"])

        index = invoke_mod.invoke(
            self.paths,
            "bd_index",
            {"path": str(root), "db": db, "dry_run": False, "confirm": True, "dimensions": 8},
        )
        self.assertTrue(index.ok, index.error)
        self.assertTrue(index.output["summary"]["written"])
        self.assertGreaterEqual(index.output["status"]["occurrence_nodes"], 2)

        status = invoke_mod.invoke(self.paths, "bd_status", {"db": db})
        self.assertTrue(status.ok, status.error)
        self.assertEqual(status.output["status"]["missing_tables"], [])

        query = invoke_mod.invoke(
            self.paths, "bd_query", {"db": db, "query": "activation graph", "top_k": 2}
        )
        self.assertTrue(query.ok, query.error)
        self.assertGreaterEqual(query.output["summary"]["anchors"], 1)
        anchor = query.output["anchors"][0]
        occurrence_id = anchor["occurrence_id"]
        # Gb: every anchor carries a source citation `path:Lx-Ly` with a real line range.
        self.assertIn("citation", anchor)
        self.assertGreaterEqual(anchor["start_line"], 1)
        self.assertLessEqual(anchor["start_line"], anchor["end_line"])
        self.assertIn(":L", anchor["citation"])

        project = invoke_mod.invoke(
            self.paths, "bd_project", {"db": db, "occurrence_id": occurrence_id, "hops": 1}
        )
        self.assertTrue(project.ok, project.error)
        self.assertGreaterEqual(project.output["summary"]["nodes"], 1)

    def test_invoke_prompt_eval_pack(self):
        constraint_text = (
            "You must cite evidence.\n"
            "Never delete files without confirmation.\n"
            "Prefer structured tools over shell.\n"
        )
        build = invoke_mod.invoke(self.paths, "constraint_build", {"text": constraint_text})
        self.assertTrue(build.ok, build.error)
        self.assertGreaterEqual(build.output["summary"]["constraints"], 3)
        constraints = build.output["constraints"]

        query = invoke_mod.invoke(
            self.paths,
            "constraint_query",
            {"constraints": constraints, "query": "evidence", "tags": ["evidence"]},
        )
        self.assertTrue(query.ok, query.error)
        self.assertGreaterEqual(query.output["summary"]["matches"], 1)

        case = invoke_mod.invoke(
            self.paths,
            "prompt_case_builder",
            {
                "id": "tool-evidence",
                "label": "Tool Evidence",
                "prompt": "Explain how you inspect files safely.",
                "constraints": constraints,
            },
        )
        self.assertTrue(case.ok, case.error)
        self.assertFalse(case.output["written"])
        self.assertEqual(case.output["case"]["id"], "tool-evidence")

        response = "Use structured tools, cite evidence from file output, and require confirmation before deleting."
        judge = invoke_mod.invoke(
            self.paths, "prompt_rubric_judge", {"response": response, "case": case.output["case"]}
        )
        self.assertTrue(judge.ok, judge.error)
        self.assertGreaterEqual(judge.output["score"], 70)

        eval_run = invoke_mod.invoke(
            self.paths,
            "prompt_eval",
            {"cases": [case.output["case"]], "responses": {"tool-evidence": response}},
        )
        self.assertTrue(eval_run.ok, eval_run.error)
        self.assertEqual(eval_run.output["summary"]["cases"], 1)
        self.assertGreaterEqual(eval_run.output["summary"]["average_score"], 70)

        diff = invoke_mod.invoke(
            self.paths,
            "prompt_diff_report",
            {
                "baseline": "Use shell commands.",
                "candidate": "Use structured tools and cite evidence.",
                "required_terms": ["structured", "evidence"],
            },
        )
        self.assertTrue(diff.ok, diff.error)
        self.assertTrue(diff.output["changed"])
        self.assertIn("structured", diff.output["improvements"])

        interview = invoke_mod.invoke(
            self.paths,
            "agent_interview",
            {
                "goal": "evaluate safe file inspection",
                "limit": 4,
                "answers": {"intent": "Inspect files safely with evidence."},
            },
        )
        self.assertTrue(interview.ok, interview.error)
        self.assertEqual(interview.output["summary"]["questions"], 4)
        self.assertGreaterEqual(interview.output["summary"]["gaps"], 1)

        bench_plan = invoke_mod.invoke(self.paths, "model_benchmark", {"limit": 2})
        self.assertTrue(bench_plan.ok, bench_plan.error)
        self.assertEqual(bench_plan.output["mode"], "plan")
        self.assertEqual(bench_plan.output["summary"]["cases"], 2)
        first_case = bench_plan.output["run_plan"][0]["case_id"]
        bench_eval = invoke_mod.invoke(
            self.paths,
            "model_benchmark",
            {
                "limit": 1,
                "responses": {first_case: "Prefer structured tools because they produce evidence."},
            },
        )
        self.assertTrue(bench_eval.ok, bench_eval.error)
        self.assertEqual(bench_eval.output["mode"], "evaluate")
        self.assertEqual(bench_eval.output["summary"]["responses"], 1)

    def test_invoke_doc_pdf_pack(self):
        from pathlib import Path

        from pypdf import PdfWriter

        root = Path(self._tmp_path("pdf-root")).parent
        src = root / "sample.pdf"
        other = root / "other.pdf"
        writer = PdfWriter()
        for i in range(3):
            writer.add_blank_page(width=200 + i * 10, height=300 + i * 10)
        with src.open("wb") as fh:
            writer.write(fh)
        writer2 = PdfWriter()
        for _ in range(2):
            writer2.add_blank_page(width=180, height=280)
        with other.open("wb") as fh:
            writer2.write(fh)

        info = invoke_mod.invoke(self.paths, "pdf_info", {"path": str(src)})
        self.assertTrue(info.ok, info.error)
        self.assertEqual(info.output["page_count"], 3)

        extract_out = root / "extract.pdf"
        extract = invoke_mod.invoke(
            self.paths,
            "pdf_extract",
            {"path": str(src), "pages": "1-2", "write": True, "out": str(extract_out)},
        )
        self.assertTrue(extract.ok, extract.error)
        self.assertTrue(extract.output["written"])
        extracted_info = invoke_mod.invoke(self.paths, "pdf_info", {"path": str(extract_out)})
        self.assertEqual(extracted_info.output["page_count"], 2)

        split = invoke_mod.invoke(
            self.paths, "pdf_split", {"path": str(src), "max_pages": 2, "dry_run": True}
        )
        self.assertTrue(split.ok, split.error)
        self.assertEqual(split.output["summary"]["chunks"], 2)
        self.assertFalse(split.output["summary"]["written"])

        guarded_merge = invoke_mod.invoke(
            self.paths, "pdf_merge", {"files": [str(src), str(other)], "dry_run": False}
        )
        self.assertFalse(guarded_merge.ok)
        self.assertIn("confirm:true", guarded_merge.error)

        merged = root / "merged.pdf"
        merge = invoke_mod.invoke(
            self.paths,
            "pdf_merge",
            {
                "files": [str(src), str(other)],
                "out": str(merged),
                "dry_run": False,
                "confirm": True,
            },
        )
        self.assertTrue(merge.ok, merge.error)
        self.assertEqual(merge.output["summary"]["pages"], 5)

        interleave = invoke_mod.invoke(
            self.paths,
            "pdf_interleave",
            {"a": str(src), "b": str(other), "dry_run": True, "reverse_second": True},
        )
        self.assertTrue(interleave.ok, interleave.error)
        self.assertEqual(interleave.output["summary"]["pages"], 5)
        self.assertEqual(interleave.output["order"][1], {"source": "b", "page": 2})

        rotate = invoke_mod.invoke(
            self.paths,
            "pdf_rotate",
            {"path": str(src), "pages": "2", "degrees": 90, "dry_run": True},
        )
        self.assertTrue(rotate.ok, rotate.error)
        self.assertEqual(rotate.output["rotations"][0]["page"], 2)

        compress = invoke_mod.invoke(
            self.paths, "pdf_compress", {"path": str(src), "dry_run": True}
        )
        self.assertTrue(compress.ok, compress.error)
        self.assertEqual(compress.output["summary"]["pages"], 3)

        thumbs = invoke_mod.invoke(
            self.paths, "pdf_thumbnails", {"path": str(src), "pages": "1-2", "limit": 2}
        )
        self.assertTrue(thumbs.ok, thumbs.error)
        self.assertEqual(thumbs.output["summary"]["planned"], 2)
        self.assertFalse(thumbs.output["summary"]["written"])

    def test_invoke_sqlite_inspect_and_schema_diff(self):
        import sqlite3

        left = self._tmp_path("left.sqlite3")
        right = self._tmp_path("right.sqlite3")
        with sqlite3.connect(left) as c:
            c.execute("PRAGMA journal_mode=OFF")
            c.execute("CREATE TABLE item (id INTEGER PRIMARY KEY, name TEXT)")
            c.execute("INSERT INTO item (name) VALUES ('a')")
        with sqlite3.connect(right) as c:
            c.execute("PRAGMA journal_mode=OFF")
            c.execute("CREATE TABLE item (id INTEGER PRIMARY KEY, name TEXT, note TEXT)")
            c.execute("CREATE INDEX idx_item_name ON item(name)")
            c.execute("CREATE TABLE extra (id INTEGER PRIMARY KEY)")

        inspect = invoke_mod.invoke(
            self.paths, "sqlite_inspect", {"db": left, "include_samples": True}
        )
        self.assertTrue(inspect.ok, inspect.error)
        self.assertEqual(inspect.output["tables"][0]["name"], "item")
        self.assertEqual(inspect.output["tables"][0]["row_count"], 1)

        diff = invoke_mod.invoke(self.paths, "schema_diff", {"left": left, "right": right})
        self.assertTrue(diff.ok, diff.error)
        self.assertTrue(diff.output["changed"])
        self.assertIn("extra", diff.output["tables_added"])
        self.assertIn("note", diff.output["tables_changed"][0]["columns_added"])

    def test_invoke_process_port_inspector(self):
        res = invoke_mod.invoke(
            self.paths,
            "process_port_inspector",
            {
                "ports": [],
                "process_name_contains": ["python"],
                "max_processes": 10,
                "max_ports": 20,
                "timeout_seconds": 5,
            },
        )
        self.assertTrue(res.ok, res.error)
        self.assertIn("summary", res.output)
        self.assertIn("processes", res.output)
        self.assertIn("ports", res.output)

    def test_invoke_dev_server_manager_guards(self):
        status = invoke_mod.invoke(self.paths, "dev_server_manager", {"action": "status"})
        self.assertTrue(status.ok, status.error)
        self.assertIn("servers", status.output)
        self.assertIn("summary", status.output)

        guarded = invoke_mod.invoke(
            self.paths, "dev_server_manager", {"action": "start", "command_id": "run_bat"}
        )
        self.assertFalse(guarded.ok)
        self.assertIn("confirm:true", guarded.error)

        stop = invoke_mod.invoke(
            self.paths,
            "dev_server_manager",
            {"action": "stop", "command_id": "run_bat", "confirm": True},
        )
        self.assertFalse(stop.ok)
        self.assertIn("no registered server", stop.error)

    def test_invoke_smoke_runner_target(self):
        from pathlib import Path

        root = Path(self._tmp_path("mini_smoke.py")).parent
        target = root / "mini_smoke.py"
        target.write_text(
            "import unittest\n\n"
            "class MiniSmoke(unittest.TestCase):\n"
            "    def test_passes(self):\n"
            "        self.assertEqual(2 + 2, 4)\n\n"
            "if __name__ == '__main__':\n"
            "    unittest.main()\n",
            encoding="utf-8",
        )
        res = invoke_mod.invoke(
            self.paths,
            "smoke_runner",
            {"root": str(root), "targets": ["mini_smoke.py"], "timeout_seconds": 20},
        )
        self.assertTrue(res.ok, res.error)
        self.assertEqual(res.output["summary"]["failed"], 0)
        self.assertEqual(res.output["summary"]["passed"], 1)

    def test_invoke_artifact_cleaner_dry_run_and_confirm_guard(self):
        from pathlib import Path

        root = Path(self._tmp_path("clean-root")).parent
        junk = root / "junk.tmp"
        junk.write_text("temporary", encoding="utf-8")

        dry = invoke_mod.invoke(
            self.paths,
            "artifact_cleaner",
            {"root": str(root), "include_patterns": ["junk.tmp"], "dry_run": True},
        )
        self.assertTrue(dry.ok, dry.error)
        self.assertEqual(dry.output["summary"]["candidate_count"], 1)
        self.assertEqual(dry.output["summary"]["removed_count"], 0)
        self.assertTrue(junk.exists())

        guarded = invoke_mod.invoke(
            self.paths,
            "artifact_cleaner",
            {"root": str(root), "include_patterns": ["junk.tmp"], "dry_run": False},
        )
        self.assertFalse(guarded.ok)
        self.assertIn("confirm:true", guarded.error)
        self.assertTrue(junk.exists())

    def test_invoke_code_intel_pack(self):
        from pathlib import Path

        root = Path(self._tmp_path("code-intel-root")).parent
        pkg = root / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "b.py").write_text(
            "def used_helper():\n" "    return 2\n\n" "def unused_helper():\n" "    return 3\n",
            encoding="utf-8",
        )
        (pkg / "a.py").write_text(
            "import time\n"
            "from pkg.b import used_helper\n"
            "import tkinter as tk\n\n"
            "def busy(x):\n"
            "    if x:\n"
            "        for item in range(3):\n"
            "            if item:\n"
            "                time.sleep(0.01)\n"
            "    return used_helper()\n\n"
            "def build_ui():\n"
            "    root = tk.Tk()\n"
            "    btn = tk.Button(root, text='Go', command=busy)\n"
            "    btn.pack()\n"
            "    return root\n",
            encoding="utf-8",
        )

        graph = invoke_mod.invoke(self.paths, "import_graph", {"root": str(root), "cycle_limit": 5})
        self.assertTrue(graph.ok, graph.error)
        self.assertGreaterEqual(graph.output["summary"]["internal_edges"], 1)
        self.assertTrue(any(e["to_module"] == "pkg.b" for e in graph.output["internal_edges"]))

        complexity = invoke_mod.invoke(
            self.paths, "complexity_score", {"root": str(root), "limit": 5}
        )
        self.assertTrue(complexity.ok, complexity.error)
        self.assertTrue(any(h["name"] == "busy" for h in complexity.output["hotspots"]))

        dead = invoke_mod.invoke(self.paths, "dead_code", {"root": str(root), "limit": 20})
        self.assertTrue(dead.ok, dead.error)
        self.assertTrue(any(c["name"] == "unused_helper" for c in dead.output["candidates"]))

        blocking = invoke_mod.invoke(
            self.paths, "blocking_call_scan", {"root": str(root), "limit": 20}
        )
        self.assertTrue(blocking.ok, blocking.error)
        # busy() is a SYNC def, so its time.sleep is informational, not a finding (T-signal C3);
        # assert the scanner detects it in either bucket.
        self.assertTrue(
            any(
                f["call"] == "time.sleep"
                for f in blocking.output["findings"] + blocking.output["informational"]
            )
        )

        tkmap = invoke_mod.invoke(self.paths, "tkinter_widget_tree", {"root": str(root)})
        self.assertTrue(tkmap.ok, tkmap.error)
        self.assertEqual(tkmap.output["summary"]["windows"], 1)
        self.assertTrue(any(w["type"] == "Button" for w in tkmap.output["widgets"]))

    def test_invoke_code_intel_more_pack(self):
        from pathlib import Path

        root = Path(self._tmp_path("code-intel-more-root")).parent
        app = root / "app"
        infra = root / "infra"
        app.mkdir()
        infra.mkdir()
        (app / "__init__.py").write_text("", encoding="utf-8")
        (infra / "__init__.py").write_text("", encoding="utf-8")
        (infra / "store.py").write_text(
            "def save(value):\n" "    return value\n",
            encoding="utf-8",
        )
        sample = app / "main.py"
        sample.write_text(
            "import tkinter as tk\n"
            "from infra.store import save\n\n"
            "def helper(value):\n"
            "    if value:\n"
            "        return save(value)\n"
            "    return None\n\n"
            "def on_click():\n"
            "    return helper('x')\n\n"
            "def build():\n"
            "    root = tk.Tk()\n"
            "    btn = tk.Button(root, text='Go', command=on_click)\n"
            "    btn.bind('<Return>', on_click)\n"
            "    btn.pack()\n"
            "    return root\n",
            encoding="utf-8",
        )

        decomp = invoke_mod.invoke(
            self.paths, "module_decomp_plan", {"root": str(root), "limit": 10}
        )
        self.assertTrue(decomp.ok, decomp.error)
        self.assertIn("summary", decomp.output)

        boundary = invoke_mod.invoke(self.paths, "domain_boundary_audit", {"root": str(root)})
        self.assertTrue(boundary.ok, boundary.error)
        self.assertGreaterEqual(boundary.output["summary"]["crossings"], 1)
        self.assertTrue(any(c["to_domain"] == "infra" for c in boundary.output["crossings"]))

        callbacks = invoke_mod.invoke(self.paths, "ui_callback_graph", {"root": str(root)})
        self.assertTrue(callbacks.ok, callbacks.error)
        self.assertGreaterEqual(callbacks.output["summary"]["events"], 2)
        self.assertTrue(any(e["kind"] == "event_to_handler" for e in callbacks.output["edges"]))

        scaffold = invoke_mod.invoke(
            self.paths,
            "test_scaffold",
            {"path": str(sample), "module": "app.main", "framework": "unittest"},
        )
        self.assertTrue(scaffold.ok, scaffold.error)
        self.assertFalse(scaffold.output["written"])
        self.assertIn("class TestMain", scaffold.output["content"])
        self.assertIn("test_helper_placeholder", scaffold.output["content"])

    def test_invoke_patch_reindent_and_error(self):
        orig = "class C:\n    def m(self):\n        return 1\n"
        r = invoke_mod.invoke(
            self.paths,
            "patch",
            {
                "action": "apply",
                "text": orig,
                "patch": {
                    "hunks": [{"search_block": "        return 1", "replace_block": "return 2"}]
                },
            },
        )
        self.assertTrue(r.ok, r.error)
        self.assertTrue(r.output["changed"])
        self.assertIn(
            "        return 2\n", r.output["result"]
        )  # reflowed to file indent + trailing nl
        bad = invoke_mod.invoke(
            self.paths,
            "patch",
            {
                "action": "apply",
                "text": orig,
                "patch": {"hunks": [{"search_block": "nope", "replace_block": "x"}]},
            },
        )
        self.assertFalse(bad.ok)
        self.assertIn("not found", bad.output["error"])

    def test_invoke_memory_workflow_pack(self):
        from pathlib import Path

        root = Path(self._tmp_path("memory-root")).parent
        session_root = root / "sessions"
        sample = root / "sample.py"
        sample.write_text(
            "def alpha():\n"
            "    return 'workflow memory retrieval'\n\n"
            "class Beta:\n"
            "    def method(self):\n"
            "        return 'rules and session replay'\n",
            encoding="utf-8",
        )

        templates = invoke_mod.invoke(self.paths, "workflow_templates", {"action": "list"})
        self.assertTrue(templates.ok, templates.error)
        self.assertGreaterEqual(templates.output["summary"]["templates"], 3)

        decomp = invoke_mod.invoke(
            self.paths,
            "workflow_decompose",
            {
                "goal": "Inspect session memory then retrieve relevant context",
                "template": "code_review",
                "max_steps": 3,
            },
        )
        self.assertTrue(decomp.ok, decomp.error)
        self.assertEqual(decomp.output["summary"]["steps"], 3)

        chunks = invoke_mod.invoke(self.paths, "semantic_chunk", {"path": str(sample)})
        self.assertTrue(chunks.ok, chunks.error)
        self.assertGreaterEqual(chunks.output["summary"]["chunks"], 2)

        rag = invoke_mod.invoke(
            self.paths,
            "rag_retrieve",
            {"query": "workflow retrieval", "chunks": chunks.output["chunks"], "top_k": 2},
        )
        self.assertTrue(rag.ok, rag.error)
        self.assertGreaterEqual(rag.output["summary"]["matches"], 1)
        self.assertIn("RETRIEVED CONTEXT", rag.output["context"])

        blocked = invoke_mod.invoke(
            self.paths, "rules_eval", {"path": "requirements.txt", "content": "password = secret"}
        )
        self.assertTrue(blocked.ok, blocked.error)
        self.assertFalse(blocked.output["allowed"])
        self.assertGreaterEqual(blocked.output["summary"]["violations"], 2)

        created = invoke_mod.invoke(
            self.paths,
            "session_record",
            {
                "action": "create",
                "session": "smoke",
                "root": str(session_root),
                "description": "Smoke session",
                "write": True,
            },
        )
        self.assertTrue(created.ok, created.error)
        noted = invoke_mod.invoke(
            self.paths,
            "session_record",
            {
                "action": "append",
                "session": "smoke",
                "root": str(session_root),
                "role": "agent",
                "kind": "note",
                "content": "Captured workflow retrieval result.",
                "write": True,
            },
        )
        self.assertTrue(noted.ok, noted.error)
        replay = invoke_mod.invoke(
            self.paths, "session_replay", {"session": "smoke", "root": str(session_root)}
        )
        self.assertTrue(replay.ok, replay.error)
        self.assertIn("workflow retrieval", replay.output["transcript"])

        flush = invoke_mod.invoke(
            self.paths,
            "memory_flush",
            {"session": "smoke", "root": str(session_root), "write": True},
        )
        self.assertTrue(flush.ok, flush.error)
        self.assertTrue(flush.output["written"])
        self.assertIn("Session Flush", flush.output["markdown"])

    def test_invoke_packaging_more_pack(self):
        from pathlib import Path

        root = Path(self._tmp_path("packaging-root")).parent
        src = root / "src"
        src.mkdir()
        (src / "app.py").write_text(
            "def hello():\n" "    return 'bundle viewer factory'\n",
            encoding="utf-8",
        )
        (root / "README.md").write_text("# Demo\n\nBundle this project.\n", encoding="utf-8")

        bundle = invoke_mod.invoke(
            self.paths,
            "codebase_bundle",
            {
                "root": str(root),
                "formats": ["report", "jsonl", "ast"],
                "dry_run": True,
                "limit": 20,
            },
        )
        self.assertTrue(bundle.ok, bundle.error)
        self.assertEqual(bundle.output["summary"]["file_count"], 2)
        self.assertEqual(len(bundle.output["outputs"]), 3)

        viewer = invoke_mod.invoke(
            self.paths,
            "tempserver",
            {
                "root": str(root),
                "name": "smoke-viewer",
                "out_dir": str(root / "viewer"),
                "dry_run": False,
                "confirm": True,
            },
        )
        self.assertTrue(viewer.ok, viewer.error)
        self.assertTrue((root / "viewer" / "index.html").exists())
        self.assertIn("http://127.0.0.1", viewer.output["url"])

        templates = invoke_mod.invoke(self.paths, "app_factory", {"action": "list_templates"})
        self.assertTrue(templates.ok, templates.error)
        self.assertGreaterEqual(templates.output["summary"]["templates"], 2)

        dest = root / "stamped"
        plan = invoke_mod.invoke(
            self.paths,
            "app_factory",
            {
                "action": "plan",
                "template": "headless_cli",
                "name": "Smoke App",
                "destination": str(dest),
            },
        )
        self.assertTrue(plan.ok, plan.error)
        self.assertGreaterEqual(plan.output["summary"]["files"], 4)
        stamp = invoke_mod.invoke(
            self.paths,
            "app_factory",
            {
                "action": "stamp",
                "template": "headless_cli",
                "name": "Smoke App",
                "destination": str(dest),
                "dry_run": False,
                "confirm": True,
            },
        )
        self.assertTrue(stamp.ok, stamp.error)
        self.assertTrue((dest / "app.py").exists())
        self.assertTrue((dest / "app_manifest.json").exists())

    def test_playbook_chains_output(self):
        from src.core.playbook import run_playbook

        dbp = self._tmp_path("e.sqlite3")
        steps = [
            {"id": "r", "tool": "report", "args": {"path": "src/core"}},
            {
                "id": "g",
                "tool": "evidence",
                "args": {
                    "action": "attach",
                    "kind": "scan_summary",
                    "body": "@r.markdown",
                    "db": dbp,
                },
            },
            {
                "id": "v",
                "tool": "evidence",
                "args": {"action": "verify", "evidence_id": "@g.evidence_id", "db": dbp},
            },
        ]
        rep = run_playbook(self.paths, steps)
        self.assertTrue(rep["ok"], rep)
        self.assertEqual(rep["completed"], 3)
        self.assertTrue(
            rep["steps"][2]["output"]["verified"]
        )  # piped report body verified as evidence

    def test_playbook_ref_only_matches_bare_tokens(self):
        from src.core.playbook import _resolve_refs

        ctx = {"r": {"markdown": "X"}}
        self.assertEqual(_resolve_refs("@r.markdown", ctx), "X")  # ref resolves
        self.assertEqual(
            _resolve_refs("@id.path words here", ctx), "@id.path words here"
        )  # prose stays literal
        self.assertEqual(_resolve_refs("@@literal", ctx), "@literal")  # escape

    def test_playbook_stops_on_error(self):
        from src.core.playbook import run_playbook

        steps = [
            {"id": "a", "tool": "ping", "args": {"message": "hi"}},
            {"id": "b", "tool": "does_not_exist", "args": {}},
            {"id": "c", "tool": "ping", "args": {}},
        ]
        rep = run_playbook(self.paths, steps)
        self.assertFalse(rep["ok"])
        self.assertEqual(rep["failed_at"], "b")
        self.assertEqual(rep["completed"], 1)
        self.assertEqual(len(rep["steps"]), 2)  # stopped before 'c'

    def test_business_failure_preserves_structured_output(self):
        # git status on a missing repo is a handled ok:false  -  the structured
        # payload must survive on res.output, not be stringified into res.error.
        res = invoke_mod.invoke(
            self.paths, "git", {"action": "status", "repo": str(self.paths.root / "does_not_exist")}
        )
        self.assertFalse(res.ok)
        self.assertIsNotNone(res.output)
        self.assertFalse(res.output["ok"])
        self.assertIn("not a git repository", res.output["error"])

    def test_event_log_records_invocations(self):
        import os
        import tempfile

        dbp = os.path.join(tempfile.mkdtemp(), "ev.sqlite3")
        prev = os.environ.get("SUITE_EVENT_LOG_DB")
        os.environ["SUITE_EVENT_LOG_DB"] = dbp
        try:
            r = invoke_mod.invoke(self.paths, "ping", {"message": "evlog"})
            self.assertTrue(r.ok, r.error)
            # an unknown tool is still a recorded (failed) event
            invoke_mod.invoke(self.paths, "does_not_exist", {})
            q = invoke_mod.invoke(self.paths, "event_log", {"action": "recent", "limit": 20})
            self.assertTrue(q.ok, q.error)
            seen = [e["tool_id"] for e in q.output["events"]]
            self.assertIn("ping", seen)
            self.assertIn("does_not_exist", seen)
        finally:
            if prev is None:
                os.environ.pop("SUITE_EVENT_LOG_DB", None)
            else:
                os.environ["SUITE_EVENT_LOG_DB"] = prev

    def test_ui_probe_renders_and_invokes(self):
        # T6: the GUI entrance. Build the real window, drive one governed invoke() through
        # the view, tear down (no mainloop). Skip cleanly on Tk-less environments.
        try:
            import tkinter

            probe_root = tkinter.Tk()
            probe_root.destroy()
        except Exception as e:  # pragma: no cover - environment-dependent
            self.skipTest(f"tkinter unavailable: {e}")
        import os
        import tempfile

        prev = os.environ.get("SUITE_EVENT_LOG_DB")
        os.environ["SUITE_EVENT_LOG_DB"] = os.path.join(tempfile.mkdtemp(), "ev.sqlite3")
        try:
            from src.ui import app_ui

            rc = app_ui.run_probe(self.paths, tool_id="ping", args_json='{"message":"smoke-ui"}')
            self.assertEqual(rc, 0)
        finally:
            if prev is None:
                os.environ.pop("SUITE_EVENT_LOG_DB", None)
            else:
                os.environ["SUITE_EVENT_LOG_DB"] = prev

    def test_planner_probe_renders_and_proposes(self):
        # E7 cockpit: build the real planner window, drive one `plan propose` through the view via
        # the governed seam, tear down (no mainloop). LLM disabled -> deterministic archetype map.
        try:
            import tkinter

            probe_root = tkinter.Tk()
            probe_root.destroy()
        except Exception as e:  # pragma: no cover - environment-dependent
            self.skipTest(f"tkinter unavailable: {e}")
        import os
        import tempfile

        keep = {k: os.environ.get(k) for k in ("SUITE_EVENT_LOG_DB", "SUITE_LLM_DISABLE")}
        os.environ["SUITE_EVENT_LOG_DB"] = os.path.join(tempfile.mkdtemp(), "ev.sqlite3")
        os.environ["SUITE_LLM_DISABLE"] = "1"
        try:
            from src.ui import app_ui

            rc = app_ui.run_planner_probe(self.paths)
            self.assertEqual(rc, 0)
        finally:
            for k, v in keep.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_map_probe_renders_and_snapshots(self):
        # T6-ops: the Project Snapshot operator view. Build the real window, run one
        # projectmapper snapshot through the governed seam, tear down (no mainloop).
        try:
            import tkinter

            probe_root = tkinter.Tk()
            probe_root.destroy()
        except Exception as e:  # pragma: no cover - environment-dependent
            self.skipTest(f"tkinter unavailable: {e}")
        import os
        import tempfile

        prev = os.environ.get("SUITE_EVENT_LOG_DB")
        os.environ["SUITE_EVENT_LOG_DB"] = os.path.join(tempfile.mkdtemp(), "ev.sqlite3")
        save_to = tempfile.mkdtemp()
        try:
            from src.ui import app_ui

            rc = app_ui.run_mapper_probe(
                self.paths, root_dir="src/core", markdown=True, save_to=save_to
            )
            self.assertEqual(rc, 0)
            self.assertTrue(
                os.path.exists(os.path.join(save_to, "probe_snapshot_snapshot.sqlite3"))
            )
        finally:
            if prev is None:
                os.environ.pop("SUITE_EVENT_LOG_DB", None)
            else:
                os.environ["SUITE_EVENT_LOG_DB"] = prev

    def test_projectmapper_exclude_paths(self):
        # Tree-picker deselection at the engine level (no Tk): a deselected dir prunes its
        # subtree (is_selected=0, not captured); a deselected file drops content.
        import os
        import sqlite3
        import tempfile

        from src.core import invoke as invoke_mod

        proj = tempfile.mkdtemp()
        os.makedirs(os.path.join(proj, "src"))
        with open(os.path.join(proj, "src", "main.py"), "w") as h:
            h.write("code\n")
        with open(os.path.join(proj, "README.md"), "w") as h:
            h.write("readme\n")
        out = os.path.join(tempfile.mkdtemp(), "s.sqlite3")
        r = invoke_mod.invoke(
            self.paths,
            "projectmapper",
            {
                "action": "compile",
                "root": proj,
                "name": "s",
                "out": out,
                "exclude_paths": ["src", "README.md"],
            },
        )
        self.assertTrue(r.ok, msg=getattr(r, "error", None))
        self.assertEqual(r.output.get("text_file_count"), 0)
        self.assertEqual(r.output.get("deselected_count"), 1)  # README (src pruned, not counted)
        c = sqlite3.connect(out)
        try:
            sel = dict(
                (p, s) for p, s in c.execute("SELECT relative_path, is_selected FROM project_tree")
            )
            self.assertEqual(sel.get("src"), 0)
            self.assertEqual(sel.get("README.md"), 0)
            reasons = [
                row[0] for row in c.execute("SELECT skip_reason FROM snapshot_skipped_paths")
            ]
            self.assertIn("unchecked_by_user", reasons)
        finally:
            c.close()

    def test_mapper_tree_selection(self):
        # The GUI checkbox tree: build the window, scan a temp folder, untick one top node,
        # confirm the deselection is computed as an exclude path. Skip on Tk-less envs.
        try:
            import tkinter

            probe_root = tkinter.Tk()
            probe_root.destroy()
        except Exception as e:  # pragma: no cover - environment-dependent
            self.skipTest(f"tkinter unavailable: {e}")
        import os
        import tempfile

        proj = tempfile.mkdtemp()
        os.makedirs(os.path.join(proj, "keep"))
        os.makedirs(os.path.join(proj, "drop"))
        with open(os.path.join(proj, "keep", "a.txt"), "w") as h:
            h.write("a\n")
        from src.ui import app_ui

        root, view = app_ui._build_mapper_root(self.paths)
        try:
            view.source_var.set(proj)
            view._rescan()
            tops = [t for t in view.tree.get_children("") if t in view._state]
            self.assertTrue(tops, "tree did not populate")
            self.assertEqual(view._deselected_rel_paths(), [])  # model A: all selected
            drop = next(t for t in tops if t.endswith("/drop"))
            view._set_subtree(drop, "unchecked")
            self.assertEqual(view._deselected_rel_paths(), ["drop"])
        finally:
            root.destroy()

    def test_project_root_resolution(self):
        # The work target is resolved by EVIDENCE ONLY - four cases, no fallthrough.
        # This test previously asserted the older contract, in which a plain home was
        # its own project and a dot-prefixed folder NAME inferred a parent target.
        # Both are gone: a name is not evidence of installation, and that heuristic
        # made the sidecar's own repository bind to the operator's staging folder.
        import os
        import tempfile
        from pathlib import Path

        from src.core.config import NoTargetBound, _resolve_project_root

        # 1. not installed, no override -> NO TARGET. Callers must refuse, not guess.
        plain = Path(tempfile.mkdtemp()) / "proj"
        self.assertIsNone(_resolve_project_root(plain))

        # 2. a dot-prefixed NAME is not evidence of anything
        dotted = Path(tempfile.mkdtemp()) / ".useful-helpers"
        self.assertIsNone(_resolve_project_root(dotted))

        # 3. a canonical IDENTITY MANIFEST is evidence of an installed instance ->
        #    bind to the target it records. The `.suite_sidecar` marker was retired in
        #    T6: it was written only by development paths, never by the product
        #    installer, and a name or a bare marker is not an identity.
        from src.core import instance
        home = Path(tempfile.mkdtemp()) / "sidecar"
        home.mkdir()
        instance.create(home, home.parent)
        self.assertEqual(_resolve_project_root(home), home.parent.resolve())

        # 3b. a bare legacy marker is NOT evidence any more - absence of canonical
        #     identity means "not an installed instance", not "guess the parent".
        legacy = Path(tempfile.mkdtemp()) / "old"
        legacy.mkdir()
        (legacy / ".suite_sidecar").write_text("x", encoding="utf-8")
        self.assertIsNone(_resolve_project_root(legacy))

        # 3c. MALFORMED canonical identity fails LOUDLY. It must never degrade into
        #     "no target", which would read as merely uninstalled.
        broken = Path(tempfile.mkdtemp()) / "broken"
        broken.mkdir()
        instance.create(broken, broken.parent)
        (broken / instance.MANIFEST).write_text("{ not json", encoding="utf-8")
        with self.assertRaises(instance.InstanceError):
            _resolve_project_root(broken)

        # 4. an explicit valid override wins over everything
        override = tempfile.mkdtemp()
        prev = os.environ.get("SUITE_PROJECT_ROOT")
        os.environ["SUITE_PROJECT_ROOT"] = override
        try:
            self.assertEqual(_resolve_project_root(plain), Path(override).resolve())
            # 5. an explicit INVALID override is a hard error, never a silent fallback.
            #    This is the defect that made a typo indistinguishable from success.
            os.environ["SUITE_PROJECT_ROOT"] = str(Path(override) / "does-not-exist")
            with self.assertRaises(NoTargetBound):
                _resolve_project_root(home)
        finally:
            if prev is None:
                os.environ.pop("SUITE_PROJECT_ROOT", None)
            else:
                os.environ["SUITE_PROJECT_ROOT"] = prev

    def test_git_init(self):
        import os
        import tempfile

        from src.core import invoke as invoke_mod

        repo = tempfile.mkdtemp()
        r = invoke_mod.invoke(self.paths, "git", {"action": "init", "repo": repo})
        self.assertTrue(r.ok, msg=getattr(r, "error", None))
        self.assertTrue(os.path.isdir(os.path.join(repo, ".git")))
        # idempotent
        r2 = invoke_mod.invoke(self.paths, "git", {"action": "init", "repo": repo})
        self.assertTrue(r2.ok)
        self.assertTrue(r2.output.get("already"))

    def test_target_is_never_modified(self):
        # INVARIANT (charter sec 1): installing the sidecar writes EXACTLY ONE directory
        # (.useful-helpers/) into the target and touches nothing else. This test is named
        # after the invariant, not after current behavior  -  inverting it means deleting a
        # test whose name states the precept, which is the point. It replaces an earlier
        # assertion that the installer drops a host-root AGENTS.md pointer: that "feature"
        # was the load-bearing precept violation, green in the suite for exactly this reason.
        import os


        target = self._foreign_target()
        # A pre-existing host tree we will prove is left byte-for-byte untouched.
        with open(os.path.join(target, "README.md"), "w") as h:
            h.write("HOST OWNS THIS\n")
        os.makedirs(os.path.join(target, "src"))
        with open(os.path.join(target, "src", "app.py"), "w") as h:
            h.write("print('host')\n")
        before = _target_manifest(target, exclude=".useful-helpers")

        plan = self._install_product(target)
        self.assertEqual(plan.returncode, 0, msg=(plan.stderr or plan.stdout)[-300:])

        done = plan
        self.assertEqual(done.returncode, 0, msg=(done.stderr or done.stdout)[-300:])
        sidecar = os.path.join(target, ".useful-helpers")
        self.assertTrue(os.path.exists(os.path.join(sidecar, "run.bat")))
        self.assertTrue(os.path.exists(os.path.join(sidecar, "src", "app.py")))

        # THE INVARIANT: outside .useful-helpers/, the target is byte-for-byte unchanged.
        after = _target_manifest(target, exclude=".useful-helpers")
        self.assertEqual(before, after, "install modified the target outside its sidecar folder")
        # And specifically: no host-root breadcrumb of any kind.
        self.assertFalse(os.path.exists(os.path.join(target, "AGENTS.md")))
        self.assertFalse(os.path.exists(os.path.join(target, ".gitignore")))

        # refuses to install into itself (self-overlap guard)
        # RETIRED ASSERTION, not a fixed one. This used to check "refuses to install
        # into itself", a guard that existed because the RUNTIME installer vended from
        # its own running tree. The standalone setup application reads a materialised
        # payload, so there is no self to overlap - and any folder is a legitimate
        # target, including a source checkout.
        #
        # Asserting it anyway INSTALLED A REAL SIDECAR INTO THE SOURCE REPOSITORY.
        # The surviving invariant is the one the installer actually holds:
        bad = self._install_product(target, mode="install")
        self.assertNotEqual(bad.returncode, 0,
                            msg="a second plain install over an existing instance "
                                "must be refused; update or reinstall are the "
                                "explicit lifecycle choices")
        # update mode overlays code but preserves runtime memory (and refuses without a flag)
        mem = os.path.join(sidecar, "_state")
        os.makedirs(mem, exist_ok=True)
        with open(os.path.join(mem, "journal.sqlite3"), "w") as h:
            h.write("PRETEND-MEMORY")
        blocked = self._install_product(target)
        self.assertNotEqual(blocked.returncode, 0)   # exists, plain install -> refuse
        upd = self._install_product(target, mode="update")
        self.assertEqual(upd.returncode, 0, msg=(upd.stderr or upd.stdout)[-300:])
        with open(os.path.join(mem, "journal.sqlite3")) as h:
            self.assertEqual(h.read(), "PRETEND-MEMORY")  # memory survived the update
        self.assertTrue(os.path.exists(os.path.join(sidecar, "run.bat")))  # code still present

    def test_docs_have_no_dangling_links(self):
        # Phase 5 REGENERATE: no shipped doc may contain a MARKDOWN LINK to a file that does not
        # exist. A dozen docs once cited SOURCE_PROVENANCE.md / TARGET_STATE.md and nothing
        # noticed  -  this ends that class of rot. Only `[text](target)` links are checked;
        # inline-code mentions (`tool.json`) are generic prose, not navigable links.
        import re

        root = self.paths.root
        link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        # SHIPPED docs only, as the comment above says. Reference material is excluded
        # deliberately: the parts bin holds twelve predecessor applications whose READMEs
        # cite absolute paths on a machine that is not this one. Those links are broken,
        # they are not ours, and they will leave with the parts bin. Before the sidecar
        # was collapsed to the repository root they were outside this walk entirely.
        # Derived from the ONE ship manifest, same reason as above.
        from src.core import payload as _payload
        _NOT_SHIPPED = tuple(_payload.PAYLOAD_EXCLUDE)
        dangling = []
        for md in sorted(root.rglob("*.md")):
            if any(p in md.parts for p in _NOT_SHIPPED):
                continue
            text = md.read_text(encoding="utf-8", errors="ignore")
            for t in (m.group(1) for m in link_re.finditer(text)):
                t = t.split("#", 1)[0].strip()
                if not t or "://" in t or t.startswith("mailto:"):
                    continue
                if (md.parent / t).exists() or (root / t).exists():
                    continue
                dangling.append(f"{md.relative_to(root).as_posix()} -> {t}")
        self.assertEqual(dangling, [], f"dangling doc links: {dangling}")

    def test_tools_md_matches_registry(self):
        # TOOLS.md is DERIVED from the registry. If it drifts, that is a bug, not a doc edit:
        # regenerate it (python -m src.app cli docs-refresh) and commit. This asserts no drift.
        from src.core import docs as docs_mod

        def _strip(s):
            return "\n".join(ln for ln in s.splitlines() if not ln.startswith("_Generated "))

        on_disk = (self.paths.docs / "TOOLS.md").read_text(encoding="utf-8")
        fresh = docs_mod.render_tools_md(self.paths)
        self.assertEqual(_strip(on_disk), _strip(fresh),
                         "TOOLS.md is stale  -  run: python -m src.app cli docs-refresh")

    def test_e6_planner_engine(self):
        # E6: the planner ENGINE composes genesis+scaffold+provenance+journal into ONE resumable
        # build. Preview + propose-degrade are checked via invoke (fast); the full build cascade is
        # driven as a subprocess with a temp target+state (it orchestrates through the seam, so it
        # needs a real project root the way it is actually used).
        import json as _json
        import os as _os
        import subprocess as _sp
        import sys as _sys
        from pathlib import Path as _Path

        good_map = {"name": "acme", "plan": "sync widgets", "archetype": "python-cli",
                    "tree": [{"file": "src/sync.py", "role": "sync engine"}]}

        # preview writes nothing
        prev = invoke_mod.invoke(self.paths, "plan",
                                 {"action": "preview", "intent": "sync widgets", "name": "acme",
                                  "map": good_map})
        self.assertTrue(prev.ok, prev.error)
        self.assertTrue(prev.output["dry_run"])
        self.assertFalse(prev.output["created"])
        self.assertIn("src/sync.py", prev.output["planned_files"])

        # propose degrades honestly with no model
        _bak = _os.environ.get("SUITE_LLM_DISABLE")
        _os.environ["SUITE_LLM_DISABLE"] = "1"
        try:
            prop = invoke_mod.invoke(self.paths, "plan",
                                     {"action": "propose", "intent": "organize notes", "name": "n"})
            self.assertTrue(prop.ok, prop.error)
            self.assertTrue(prop.output["degraded"])
            self.assertTrue(prop.output["map"].get("archetype"))
        finally:
            if _bak is None:
                _os.environ.pop("SUITE_LLM_DISABLE", None)
            else:
                _os.environ["SUITE_LLM_DISABLE"] = _bak

        # full build cascade via subprocess (temp target + isolated state)
        state = _Path(self._tmp_path("e6-state"))
        target = _Path(self._tmp_path("e6-target"))
        state.mkdir(parents=True, exist_ok=True)
        target.mkdir(parents=True, exist_ok=True)
        env = dict(_os.environ, SUITE_STATE_ROOT=str(state), SUITE_PROJECT_ROOT=str(target),
                   SUITE_SUMMARY_DISABLE="1", SUITE_LLM_DISABLE="1")
        root = self.paths.root

        def _plan(args):
            p = _sp.run([_sys.executable, "-m", "src.app", "cli", "tool-call", "--tool", "plan",
                         "--args-json", _json.dumps(args)], cwd=str(root), capture_output=True,
                        text=True, env=env, timeout=300)
            return _json.loads(p.stdout).get("output", {})

        b = _plan({"action": "build", "apply": True, "intent": "sync widgets", "name": "acme",
                   "map": good_map, "root": "acme"})
        self.assertTrue(b.get("ok"), b.get("error"))
        self.assertTrue(b.get("created"))
        op_id = b.get("op_id")
        self.assertTrue(op_id)
        self.assertTrue((target / "acme" / "src" / "sync.py").is_file())
        self.assertTrue((state / "workspace.json").is_file())      # genesis ran
        self.assertTrue(all(t.get("ok") for t in b.get("trail", [])))

        # provenance chain: the project traces back to the intent
        pv = _sp.run([_sys.executable, "-m", "src.app", "cli", "tool-call", "--tool", "provenance",
                      "--args-json", _json.dumps({"action": "trace", "kind": "project", "ref": "acme"})],
                     cwd=str(root), capture_output=True, text=True, env=env, timeout=120)
        chain = _json.loads(pv.stdout).get("output", {}).get("chain", [])
        self.assertIn("intent", {x["subject"]["kind"] for x in chain})

        # resume is idempotent: every stage skipped, nothing re-run
        r = _plan({"action": "resume", "apply": True, "op_id": op_id, "map": good_map,
                   "intent": "sync widgets", "name": "acme", "root": "acme"})
        skipped = {t["step"] for t in r.get("trail", []) if t.get("skipped")}
        self.assertTrue({"genesis", "scaffold", "provenance", "journal"} <= skipped)

    def test_e5_formation_provenance(self):
        # E5: record WHY an artifact exists and TRACE it back. The core contract is that every
        # relation declares an enforced ORIGIN (discovered/operational/interpretive) and that a
        # multi-participant activity stays coherent, so "why does this exist" reaches the
        # originating intent AND shows its approvals/validations.
        from pathlib import Path as _Path

        from tools import provenance_shared as pv

        db = _Path(self._tmp_path("pv")) / "provenance.sqlite3"
        c = pv.open_db(db)
        try:
            # the review's example chain, all operationally-created
            chain = [
                ({"kind": "question", "ref": "viable?"}, "motivated", {"kind": "work_order", "ref": "wo1"}),
                ({"kind": "work_order", "ref": "wo1"}, "retrieved", {"kind": "source", "ref": "src1"}),
                ({"kind": "source", "ref": "src1"}, "supported", {"kind": "claim", "ref": "c7"}),
                ({"kind": "claim", "ref": "c7"}, "used_in", {"kind": "outline", "ref": "o1"}),
                ({"kind": "outline", "ref": "o1"}, "generated", {"kind": "draft", "ref": "draft.md"}),
            ]
            for subj, rel, obj in chain:
                r = pv.add_edge(c, subj, rel, obj, "operational", op_id="op1")
                self.assertTrue(r["ok"], r)

            # trace the draft back - it must reach the originating question
            t = pv.trace(c, "draft", "draft.md")
            self.assertTrue(t["ok"])
            kinds = {x["subject"]["kind"] for x in t["chain"]}
            self.assertIn("question", kinds)
            self.assertIn("source", kinds)
            self.assertEqual(t["origins"], ["operational"])

            # a multi-participant activity; trace must surface generated + used + approval + validation
            a = pv.add_activity(c, "generate draft", [
                {"role": "requested_by", "kind": "intent", "ref": "write it"},
                {"role": "used", "kind": "source", "ref": "src1"},
                {"role": "approved_by", "kind": "human", "ref": "jacob"},
                {"role": "validated_by", "kind": "check", "ref": "cite-audit"},
                {"role": "generated", "kind": "draft", "ref": "final.md"},
            ], origin="operational", op_id="op1")
            self.assertTrue(a["ok"])
            t2 = pv.trace(c, "draft", "final.md")
            roles = {x["relation"] for x in t2["chain"]}
            for expected in ("generated", "used", "approved_by", "validated_by"):
                self.assertIn(expected, roles)

            # ORIGIN is enforced (the whole point)
            bad = pv.add_edge(c, {"kind": "a", "ref": "1"}, "used", {"kind": "b", "ref": "2"}, "guessed")
            self.assertFalse(bad["ok"])

            # the three origins are distinguished in storage
            pv.add_edge(c, {"kind": "module", "ref": "a.py"}, "used", {"kind": "module", "ref": "b.py"}, "discovered")
            pv.add_edge(c, {"kind": "claim", "ref": "c7"}, "superseded_by", {"kind": "claim", "ref": "c9"}, "interpretive")
            self.assertTrue(len(pv.list_edges(c, origin="discovered")) >= 1)
            self.assertTrue(len(pv.list_edges(c, origin="interpretive")) >= 1)
            self.assertTrue(len(pv.list_edges(c, origin="operational")) >= 5)
        finally:
            c.close()

        # CLI wiring through the seam (isolated state root so it never touches the real _state)
        import os as _os
        sr = str(self._tmp_path("pv-cli"))
        _bak = _os.environ.get("SUITE_STATE_ROOT")
        _os.environ["SUITE_STATE_ROOT"] = sr
        try:
            note = invoke_mod.invoke(self.paths, "provenance",
                                     {"action": "note", "subject": {"kind": "intent", "ref": "seam-intent"},
                                      "relation": "generated", "object": {"kind": "artifact", "ref": "seam-art"},
                                      "origin": "operational"})
            self.assertTrue(note.ok, note.error)
            tr = invoke_mod.invoke(self.paths, "provenance",
                                   {"action": "trace", "kind": "artifact", "ref": "seam-art"})
            self.assertTrue(tr.ok, tr.error)
            self.assertGreaterEqual(tr.output["steps"], 1)
        finally:
            if _bak is None:
                _os.environ.pop("SUITE_STATE_ROOT", None)
            else:
                _os.environ["SUITE_STATE_ROOT"] = _bak

    def test_e4_recovery_lifecycle(self):
        # E4: recovery as normal operation. The whole point is that a multi-step effort survives
        # interruption at a specific, recoverable point - so this drives the full lifecycle at the
        # ledger level (durable across a simulated crash), plus the CLI wiring through the seam.
        from pathlib import Path as _Path

        from tools import operations_shared as ops

        db = _Path(self._tmp_path("op")) / "operations.sqlite3"
        target = _Path(self._tmp_path("op-target"))
        target.mkdir(parents=True, exist_ok=True)
        (target / "a.py").write_text("x = 1\n", encoding="utf-8")

        conn = ops.open_db(db)
        op = ops.start_op(conn, "Build widget", "a working widget",
                          steps=[{"tool": "scaffold_project"}, {"tool": "project_run"}])
        op_id = op["op_id"]
        self.assertEqual(op["status"], "open")
        self.assertEqual(len(op["steps"]), 2)

        # advance one step with an idempotency key
        r = ops.record_step(conn, op_id, tool="scaffold_project", status="done",
                            idempotency_key="scaffold:v1", result_ref="ev:1")
        self.assertTrue(r["ok"])
        self.assertFalse(r["idempotent_hit"])

        # a FAILED step must carry an explicit class - a generic failure is refused
        bad = ops.record_step(conn, op_id, tool="project_run", status="failed")
        self.assertFalse(bad["ok"])
        good = ops.record_step(conn, op_id, tool="project_run", status="failed",
                              failure_class="timeout")
        self.assertTrue(good["ok"])
        self.assertEqual(good["op_status"], "failed")
        ops.set_status(conn, op_id, "open")  # reopen to continue the lifecycle

        # PAUSE + simulate a crash by dropping the connection entirely
        ops.pause_op(conn, op_id, target, resume_hint="run the tests")
        conn.close()
        del conn

        # fresh connection (new process): the operation is durable and listed as paused, NOT lost
        conn2 = ops.open_db(db)
        paused = ops.list_ops(conn2, status="paused")
        self.assertEqual(len(paused), 1)
        self.assertEqual(paused[0]["op_id"], op_id)

        # resume with no drift: resumes and reports which idempotency keys already landed
        res = ops.resume_op(conn2, op_id, target)
        self.assertTrue(res["resumed"])
        self.assertFalse(res["drift"])
        self.assertIn("scaffold:v1", res["already_done_keys"])

        # re-recording a landed key does NOT re-run it
        again = ops.record_step(conn2, op_id, tool="scaffold_project", status="done",
                               idempotency_key="scaffold:v1")
        self.assertTrue(again["idempotent_hit"])

        # DRIFT: pause, edit the target externally, resume -> stale_witness, resumed=False
        ops.pause_op(conn2, op_id, target)
        (target / "b.py").write_text("y = 2\n", encoding="utf-8")
        drift = ops.resume_op(conn2, op_id, target)
        self.assertFalse(drift["resumed"])
        self.assertTrue(drift["drift"])
        self.assertEqual(drift["failure_class"], "stale_witness")
        conn2.close()

        # CLI wiring through the seam (isolated state root so it never touches the real _state)
        import os as _os
        sr = str(self._tmp_path("op-cli"))
        _bak = _os.environ.get("SUITE_STATE_ROOT")
        _os.environ["SUITE_STATE_ROOT"] = sr
        try:
            started = invoke_mod.invoke(self.paths, "operation",
                                        {"action": "start", "title": "seam probe"})
            self.assertTrue(started.ok, started.error)
            sid = started.output["op_id"]
            listed = invoke_mod.invoke(self.paths, "operation", {"action": "list", "status": "open"})
            self.assertTrue(any(o["op_id"] == sid for o in listed.output["operations"]))
            fin = invoke_mod.invoke(self.paths, "operation", {"action": "finish", "op_id": sid})
            self.assertEqual(fin.output["status"], "done")
        finally:
            if _bak is None:
                _os.environ.pop("SUITE_STATE_ROOT", None)
            else:
                _os.environ["SUITE_STATE_ROOT"] = _bak

    def test_e3_genesis_start_new(self):
        # E3: "Start New" first-class. An empty workspace + an intent must yield a coherent,
        # governed workspace with NO domain required, and attach must map it at its actual
        # evidence density (nascent -> domain is a SUGGESTION) rather than misclassifying it or
        # erroring on emptiness. Then it must CONVERGE: once artifacts exist, attach firms up.
        import os as _os
        from pathlib import Path as _Path

        state = _Path(self._tmp_path("e3-state"))
        target = _Path(self._tmp_path("e3-target"))
        state.mkdir(parents=True, exist_ok=True)
        target.mkdir(parents=True, exist_ok=True)  # deliberately EMPTY

        env_bak = {k: _os.environ.get(k) for k in ("SUITE_STATE_ROOT",)}
        _os.environ["SUITE_STATE_ROOT"] = str(state)
        try:
            # 1. genesis preview writes nothing
            prev = invoke_mod.invoke(self.paths, "genesis",
                                     {"intent": "Investigate an idea.", "name": "probe"})
            self.assertTrue(prev.ok, prev.error)
            self.assertTrue(prev.output["dry_run"])
            self.assertFalse(prev.output["created"])
            self.assertFalse((state / "workspace.json").exists())

            # 2. genesis for real: identity recorded, no domain required
            g = invoke_mod.invoke(self.paths, "genesis",
                                  {"intent": "Investigate an idea.", "name": "probe",
                                   "authority": "Sandbox", "apply": True})
            self.assertTrue(g.ok, g.error)
            self.assertTrue(g.output["created"])
            ws = g.output["workspace"]
            self.assertEqual(ws["intent"], "Investigate an idea.")
            self.assertEqual(ws["authority"], "Sandbox")
            self.assertTrue(ws["workspace_id"])
            self.assertTrue((state / "workspace.json").is_file())

            # 3. re-genesis without overwrite is refused (identity is not clobbered silently)
            again = invoke_mod.invoke(self.paths, "genesis",
                                      {"intent": "Something else.", "apply": True})
            self.assertFalse(again.ok)
            self.assertIn("already exists", again.output["error"])

            # 4. attach on the nascent workspace: density-aware, domain is a SUGGESTION, intent shown
            a = invoke_mod.invoke(self.paths, "attach", {"refresh": True, "target": str(target)})
            self.assertTrue(a.ok, a.error)
            pm = a.output["project_map"]
            self.assertEqual(pm["evidence_density"], "empty")
            self.assertTrue(pm["nascent"])
            self.assertEqual(pm["domain_status"], "suggested")
            self.assertEqual(pm.get("intent"), "Investigate an idea.")
            # next steps are growth-oriented, not code-analysis
            tools_next = [n["call"]["tool"] for n in a.output["next"]]
            self.assertIn("scaffold_project", tools_next)
            self.assertNotIn("dead_code", tools_next)

            # 5. CONVERGENCE: add real files, re-attach -> firms up from suggested to detected
            for i in range(12):
                (target / f"m_{i}.py").write_text("x = 1\n", encoding="utf-8")
            a2 = invoke_mod.invoke(self.paths, "attach", {"refresh": True, "target": str(target)})
            pm2 = a2.output["project_map"]
            self.assertFalse(pm2["nascent"])
            self.assertEqual(pm2["domain_status"], "detected")
            self.assertEqual(pm2.get("intent"), "Investigate an idea.")  # thread unbroken

            # 6. re-engage (no refresh) after growth stays INTERNALLY CONSISTENT: density and
            # domain_status are recomputed together, so nascent=False never coexists with a
            # "suggested" domain_status left over from the nascent map.
            re_eng = invoke_mod.invoke(self.paths, "attach", {"target": str(target)})
            self.assertTrue(re_eng.ok, re_eng.error)
            self.assertEqual(re_eng.output["mode"], "reengaged")
            pm3 = re_eng.output["project_map"]
            self.assertFalse(pm3["nascent"])
            self.assertEqual(pm3["domain_status"], "detected")
            self.assertEqual(pm3.get("intent"), "Investigate an idea.")
        finally:
            for k, v in env_bak.items():
                if v is None:
                    _os.environ.pop(k, None)
                else:
                    _os.environ[k] = v

    def test_installer_logic(self):
        # E2: the sidecar installer's LOGIC (the GUI is untestable headless, so it is split out).
        # Guards the promises: writes exactly one .useful-helpers/ dir and nothing else; refuses to
        # clobber an existing sidecar on a plain install; reinstall wipes; update KEEPS the
        # target's accumulated memory; and payload/target overlap is refused (the precept).
        import importlib.util
        from pathlib import Path as _Path

        mod_path = self.paths.root / "packaging" / "installer" / "install.py"
        self.assertTrue(mod_path.is_file(), "installer source missing")
        spec = importlib.util.spec_from_file_location("uh_install_probe", mod_path)
        inst = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(inst)

        # a minimal but valid payload (must have src/ to be a toolkit)
        payload = _Path(self._tmp_path("payload"))
        (payload / "src").mkdir(parents=True)
        (payload / "src" / "app.py").write_text("# entry\n", encoding="utf-8")
        # The installer loads the identity authority FROM THE PAYLOAD, so a payload
        # fixture must carry it - the format that governs an instance is the one that
        # shipped with it, not whatever version the installer happens to be.
        (payload / "src" / "core").mkdir(parents=True, exist_ok=True)
        (payload / "src" / "core" / "instance.py").write_text(
            (_Path(self.paths.root) / "src" / "core" / "instance.py").read_text(
                encoding="utf-8"), encoding="utf-8")
        (payload / "run.bat").write_text("@echo off\n", encoding="utf-8")

        target = _Path(self._tmp_path("target"))
        target.mkdir(parents=True, exist_ok=True)
        (target / "mine.py").write_text("print('user')\n", encoding="utf-8")
        sc = target / ".useful-helpers"

        # 1. new install: creates the one dir, leaves the user's file untouched
        r = inst.install(payload, target, "install")
        self.assertTrue(r["ok"], r.get("error"))
        self.assertTrue((sc / "run.bat").is_file())
        self.assertEqual((target / "mine.py").read_text(encoding="utf-8"), "print('user')\n")
        self.assertEqual([p.name for p in target.iterdir() if p.name != ".useful-helpers"],
                         ["mine.py"], "installer touched something outside the sidecar")

        # 2. plain install over an existing sidecar is refused (no silent clobber)
        r = inst.install(payload, target, "install")
        self.assertFalse(r["ok"])
        self.assertIn("already exists", r["error"])

        # 3. update KEEPS accumulated memory
        (sc / "_state").mkdir(parents=True, exist_ok=True)
        (sc / "_state" / "journal.json").write_text('{"real":true}', encoding="utf-8")
        r = inst.install(payload, target, "update")
        self.assertTrue(r["ok"], r.get("error"))
        self.assertTrue(r["memory_preserved"])
        self.assertEqual((sc / "_state" / "journal.json").read_text(encoding="utf-8"),
                         '{"real":true}', "update lost the target's memory")

        # 4. reinstall WIPES memory
        r = inst.install(payload, target, "reinstall")
        self.assertTrue(r["ok"], r.get("error"))
        self.assertFalse((sc / "_state" / "journal.json").exists())

        # 5. overlap refusal: installing INTO the payload itself is blocked (precept)
        self.assertTrue(inst.validate(payload, payload),
                        "installer must refuse when target overlaps the payload")

    def test_vendor_export_clean_app_doc_swap(self):
        # The clean_app profile promises to SWAP in product-focused README/ONBOARDING so a vended
        # copy never ships the build-time docs. That promise silently no-op'd once because the
        # override TEMPLATES did not exist (the copy loop skips a missing source). This guards the
        # invariant directly: every declared override must have a real, non-trivial source that is
        # ALSO stripped (so it is applied, never double-shipped verbatim). A full clean_app export
        # then proves the swap actually lands.
        from tools.vendor_export import cli as ve

        root = self.paths.root
        # The mapping moved to the ship-boundary authority in T6; vendor_export
        # consumes it rather than carrying a second copy.
        from src.core.payload import EXPORT_SUBSTITUTIONS
        for src_rel, dst_rel in EXPORT_SUBSTITUTIONS.items():
            src = root / src_rel
            self.assertTrue(src.is_file(), f"clean_app override template missing: {src_rel}")
            self.assertGreater(len(src.read_text(encoding="utf-8").strip()), 100,
                               f"override template is empty/trivial: {src_rel}")
            # its directory must be in the strip set so it is never shipped verbatim
            self.assertTrue(any(src_rel.startswith(s.rstrip("/") + "/") or src_rel.startswith(s)
                                for s in ve.CLEAN_APP_STRIP),
                            f"override source {src_rel} is not stripped; it would double-ship")

        # end-to-end: a clean_app export lands the templates at their destination names
        dest = str(self._tmp_path("clean_app"))
        r = invoke_mod.invoke(self.paths, "vendor_export",
                              {"root": ".", "name": "cleanapp_probe", "clean_app": True,
                               "zip": False, "out_root": dest, "apply": True, "overwrite": True})
        self.assertTrue(r.ok, r.error)
        from pathlib import Path as _Path
        export_dir = _Path(r.output["export_dir"])
        readme = (export_dir / "README.md").read_text(encoding="utf-8")
        self.assertIn("standalone copy", readme,
                      "clean_app README is not the swapped product template")
        # the template source dir must NOT have shipped verbatim
        self.assertFalse((export_dir / "tools" / "vendor_export" / "clean_app_docs").exists(),
                         "clean_app doc templates leaked into the export verbatim")

    def test_scaffold_project(self):
        # E1: the new-project materializer. It must (1) preview without writing, (2) enforce the
        # map contract by REFUSING malformed work orders with a named reason, (3) materialize a
        # real tree with stamped headers + PROJECT_PLAN.md on apply, and (4) never write outside
        # its confined base - the same escape-proofing every 'hand' shares.
        from pathlib import Path as _Path

        base = _Path(self._tmp_path("scaffold"))
        rel = base.relative_to(_Path.cwd()).as_posix() if base.is_absolute() else str(base)

        good_map = {"name": "demo", "plan": "A demo project.", "archetype": "python-cli",
                    "tree": [{"file": "src/extra.py", "role": "extra bit",
                              "does": "does an extra thing"}]}

        # (1) preview writes nothing
        prev = invoke_mod.invoke(self.paths, "scaffold_project",
                                 {"action": "plan", "map": good_map, "root": rel})
        self.assertTrue(prev.ok, prev.error)
        self.assertTrue(prev.output["dry_run"])
        self.assertFalse(prev.output["created"])
        self.assertIn("src/extra.py", [f["rel"] for f in prev.output["planned_files"]])
        self.assertIn("PROJECT_PLAN.md", [f["rel"] for f in prev.output["planned_files"]])
        self.assertFalse(any(base.rglob("*")), "preview must not write anything")

        # (2) contract enforcement: each malformed map refused with an error, never a guess
        bad = [
            {"tree": [{"dir": "x"}]},                                    # missing name
            {"name": "p", "tree": [{"file": "../evil.py"}]},            # path escape
            {"name": "p", "tree": [{"file": "/abs.py"}]},              # absolute
            {"name": "p", "tree": [{"file": "a", "content": "x", "template": "readme"}]},
            {"name": "p", "tree": [{"file": "a", "template": "nope"}]},  # unknown template
            {"name": "p", "archetype": "rails"},                        # unknown archetype
            {"name": "p", "tree": [{"dir": "s"}, {"file": "s"}]},       # dir/file conflict
        ]
        for m in bad:
            r = invoke_mod.invoke(self.paths, "scaffold_project",
                                  {"action": "plan", "map": m, "root": rel})
            self.assertFalse(r.ok, f"map should have been refused: {m}")
            self.assertTrue(r.output.get("error"), f"refusal must name a reason: {m}")

        # (3) materialize for real
        made = invoke_mod.invoke(self.paths, "scaffold_project",
                                 {"action": "create", "apply": True, "map": good_map, "root": rel})
        self.assertTrue(made.ok, made.error)
        self.assertTrue(made.output["created"])
        self.assertTrue((base / "src" / "extra.py").is_file())
        self.assertTrue((base / "PROJECT_PLAN.md").is_file())
        # header stamped from the map metadata
        stub = (base / "src" / "extra.py").read_text(encoding="utf-8")
        self.assertIn("ROLE:", stub)
        self.assertIn("extra bit", stub)
        self.assertIn("STATUS:", stub)
        # boilerplate placeholder filled with the project name, not left as a literal brace
        app = (base / "src" / "app.py").read_text(encoding="utf-8")
        self.assertIn("demo", app)
        self.assertNotIn("{name}", app)
        # PROJECT_PLAN.md captures the plan + a row per file
        plan_doc = (base / "PROJECT_PLAN.md").read_text(encoding="utf-8")
        self.assertIn("A demo project.", plan_doc)
        self.assertIn("src/extra.py", plan_doc)

        # (4) collision refusal without overwrite; success with it
        again = invoke_mod.invoke(self.paths, "scaffold_project",
                                  {"action": "create", "apply": True, "map": good_map, "root": rel})
        self.assertFalse(again.ok)
        self.assertIn("collision", (again.output.get("error") or "").lower())
        over = invoke_mod.invoke(self.paths, "scaffold_project",
                                 {"action": "create", "apply": True, "overwrite": True,
                                  "map": good_map, "root": rel})
        self.assertTrue(over.ok, over.error)

    def test_registry_json_matches_discovery(self):
        # config/registry.json is DERIVED state (a persisted snapshot of live manifest discovery).
        # Nothing else asserted it stayed fresh: test_tools_md_matches_registry checks TOOLS.md
        # against LIVE discovery, not against the on-disk registry, so a tool could be added and
        # the committed registry.json silently drift. (It did: `symbol_graph` was added and the
        # snapshot lagged at 89 while discovery found 90.) This closes that gap - the same
        # docs-as-code contract the TOOLS.md test enforces, applied to the registry itself.
        import json
        from dataclasses import asdict

        from src.core import registry as registry_mod

        on_disk = json.loads((self.paths.config / "registry.json").read_text(encoding="utf-8"))
        fresh_tools = [asdict(r) for r in registry_mod.discover(self.paths)]

        # internal consistency: the snapshot's own count must match its own list
        self.assertEqual(on_disk.get("count"), len(on_disk.get("tools", [])),
                         "registry.json count field disagrees with its own tools list")
        # freshness: the persisted tool records must match what discovery produces right now
        self.assertEqual(on_disk.get("tools"), fresh_tools,
                         "registry.json is stale  -  run: python -m src.app cli registry-refresh")

    def test_precept_guard_logic(self):
        # Phase 4 ENFORCE (unit): the seam's target-write guard fires for Observe tools under
        # real sidecar conditions and nowhere else. The end-to-end proof (a fixture tool actually
        # rejected) lives in the harness; this pins the decision + diff logic fast, in-suite.
        import os
        from dataclasses import replace
        from pathlib import Path

        from src.core import invoke as invoke_mod
        from src.core.config import resolve_paths

        # Sidecar conditions: target distinct from toolkit home.
        target = self._foreign_target()
        with open(os.path.join(target, "keep.txt"), "w") as h:
            h.write("host owns this\n")
        paths = replace(resolve_paths(), project_root=Path(target).resolve())

        class _T:
            def __init__(self, authority, writes="none"):
                self.authority, self.writes = authority, writes

        prev = os.environ.pop("SUITE_STRICT_OBSERVE", None)
        try:
            # Gated on Observe; Sandbox/Apply run project/deliberate writes and are not guarded.
            self.assertTrue(invoke_mod._guard_applies(paths, _T("Observe")))
            self.assertFalse(invoke_mod._guard_applies(paths, _T("Sandbox")))
            self.assertFalse(invoke_mod._guard_applies(paths, _T("Apply")))
            # `writes: target` is the sanctioned opt-out.
            self.assertFalse(invoke_mod._guard_applies(paths, _T("Observe", "target")))
            # Standalone (project_root == toolkit home): nothing to protect, guard off.
            self.assertFalse(invoke_mod._guard_applies(self.paths, _T("Observe")))
            # Kill-switch.
            os.environ["SUITE_STRICT_OBSERVE"] = "0"
            self.assertFalse(invoke_mod._guard_applies(paths, _T("Observe")))
        finally:
            os.environ.pop("SUITE_STRICT_OBSERVE", None)
            if prev is not None:
                os.environ["SUITE_STRICT_OBSERVE"] = prev

        # The diff catches an added file (the shape of a real violation).
        before, complete = invoke_mod._target_manifest(paths)
        self.assertTrue(complete)
        with open(os.path.join(target, "sneaky.txt"), "w") as h:
            h.write("i should not exist\n")
        after, _ = invoke_mod._target_manifest(paths)
        changed = invoke_mod._manifest_diff(before, after)
        self.assertTrue(any(c.endswith("sneaky.txt") for c in changed))

    def test_sidecar_conditions(self):
        # THE SIDECAR-CONDITIONS HARNESS (T-fold gate). Installs the toolkit into a scratch
        # host project, then drives tools through the INSTALLED sidecar's own seam and proves
        # the roots contract holds under true sidecar conditions: (1) project-awareness  -
        # scans see the host, never the toolkit's own home; (2) state stays in the sidecar;
        # (3) generated artifacts land under the sidecar, never the host. This is the net
        # that would have caught the 7 field failures our standalone suite missed.
        import json as _json
        import os
        import subprocess
        import sys


        host = self._foreign_target()
        os.makedirs(os.path.join(host, "src"))
        with open(os.path.join(host, "host_marker.txt"), "w") as h:
            h.write("HOST_ONLY_TOKEN_9Q\n")
        with open(os.path.join(host, "src", "host_mod.py"), "w") as h:
            h.write("def host_fn():\n    return 'HOST_ONLY_TOKEN_9Q'\n")

        done = self._install_product(host)
        self.assertEqual(done.returncode, 0, msg=(done.stderr or done.stdout)[-300:])
        sidecar = os.path.join(host, ".useful-helpers")

        def seam(tool, args):
            # Drive the INSTALLED sidecar's own governed seam, with a clean env so it
            # self-resolves its roots (no leakage from this test process).
            env = {
                k: v
                for k, v in os.environ.items()
                if k not in ("SUITE_HOME", "SUITE_PROJECT_ROOT", "SUITE_EVENT_LOG_DB", "PYTHONPATH")
            }
            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "src.app",
                    "cli",
                    "tool-call",
                    "--tool",
                    tool,
                    "--args-json",
                    _json.dumps(args),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=sidecar,
                env=env,
                timeout=180,
            )
            self.assertEqual(r.returncode, 0, msg=f"{tool}: {r.stderr[:400]}")
            return _json.loads(r.stdout).get("output", {})

        # (1a) file_tree with NO root: must scan the HOST, and never list the toolkit home.
        ft = seam("file_tree", {"limit": 200})
        rows = ft.get("rows", [])
        paths_seen = " ".join(str(r.get("path", "")) for r in rows)
        self.assertIn("host_marker.txt", paths_seen)
        self.assertNotIn(".useful-helpers", paths_seen)

        # (1b) repo_search: host-only token found; toolkit-only token invisible.
        hit = seam("repo_search", {"query": "HOST_ONLY_TOKEN_9Q"})
        self.assertGreaterEqual(int(hit.get("count", 0)), 1, msg=str(hit)[:300])
        miss = seam("repo_search", {"query": "SpineSmokeTest"})
        self.assertEqual(int(miss.get("count", -1)), 0, msg=str(miss)[:300])

        # (2) journal writes into the SIDECAR's store, never the host's tree.
        seam("journal", {"action": "add", "title": "harness", "summary": "sidecar-conditions"})
        self.assertTrue(
            os.path.exists(
                os.path.join(sidecar, "_state", "journal.sqlite3")
            )
        )
        self.assertFalse(os.path.exists(os.path.join(host, "_docs")))

        # (3) artifact-producing tool defaults its OUTPUT under the sidecar, not the host.
        pm = seam("projectmapper", {"action": "compile", "root": ".", "name": "harness"})
        self.assertTrue(pm.get("ok", True), msg=str(pm)[:300])
        self.assertTrue(
            os.path.exists(
                os.path.join(sidecar, "_artifacts", "projectmapper", "harness_snapshot.sqlite3")
            )
        )
        self.assertFalse(os.path.exists(os.path.join(host, "_artifacts")))

    def test_roots_contract_declared(self):
        # T-roots gate: every manifest declares a valid operates_on; the registry surfaces it;
        # the shared contract API exists (no tool re-derives roots ad hoc).
        import json as _json
        import os

        from src.core import registry
        from tools._toolkit import (
            MissingRuntimeContext,
            instance_root,
            output_root,
            project_root,
            suite_home,
        )

        checked = 0
        for base in (self.paths.tools, self.paths.apps):
            for m in sorted(base.glob("*/tool.json")):
                if m.parent.name.startswith("_"):
                    continue
                data = _json.loads(m.read_text(encoding="utf-8"))
                self.assertIn(
                    data.get("operates_on"),
                    ("project", "toolkit"),
                    msg=f"manifest missing/invalid operates_on: {m.parent.name}",
                )
                checked += 1
        self.assertGreaterEqual(checked, 73)
        recs = registry.list_tools(self.paths)
        self.assertTrue(all(r.operates_on in ("project", "toolkit") for r in recs))
        # The roots contract is TRANSPORTED, not inferred. `toolkit_home_names()` is
        # gone: it returned a NAME set seeded with a hardcoded ".useful-helpers", which
        # missed a renamed instance and pruned unrelated target folders sharing the name.
        # Transport supplied EXPLICITLY. Tools no longer infer their roots, so a
        # test exercising the contract must play the seam's part rather than rely on
        # a fallback that deliberately no longer exists.
        os.environ.setdefault("SUITE_HOME", str(self.paths.root))
        os.environ.setdefault("SUITE_PROJECT_ROOT", str(self.paths.project_root
                                                        or self.paths.root))
        self.assertEqual(output_root(), suite_home() / "_artifacts")
        self.assertEqual(instance_root(), suite_home())
        self.assertTrue(callable(project_root))

        # And the other half: WITHOUT transported context a tool child must FAIL rather
        # than rediscover the project from cwd. Removing eight guesses is only half the
        # repair if a ninth quietly reappears inside the adapter.
        saved = {k: os.environ.pop(k) for k in ("SUITE_HOME", "SUITE_PROJECT_ROOT")
                 if k in os.environ}
        try:
            with self.assertRaises(MissingRuntimeContext):
                project_root()
            with self.assertRaises(MissingRuntimeContext):
                instance_root()
        finally:
            os.environ.update(saved)

    def test_path_scrubber(self):
        # T-roots gate: a failing call whose error echoes an absolute path is stored SCRUBBED
        # in the event log, and suite.log never carries the raw path (central scrubber, A5).
        import os
        import sqlite3
        import tempfile

        from src.core import invoke as invoke_mod
        from src.lib import logging_setup

        logging_setup.configure(
            self.paths.logs,
            scrub_roots=(
                (str(self.paths.project_root), "<project>"),
                (str(self.paths.root), "<toolkit>"),
            ),
        )
        prev = os.environ.get("SUITE_EVENT_LOG_DB")
        db = os.path.join(tempfile.mkdtemp(), "ev.sqlite3")
        os.environ["SUITE_EVENT_LOG_DB"] = db
        try:
            bad = str(self.paths.project_root / "no_such_dir_scrub_probe")
            r = invoke_mod.invoke(self.paths, "file_tree", {"root": bad})
            self.assertFalse(r.ok)
            self.assertIn("no_such_dir_scrub_probe", str(r.error))  # error does echo the path
            row = (
                sqlite3.connect(db)
                .execute("SELECT error FROM events ORDER BY event_id DESC LIMIT 1")
                .fetchone()
            )
            self.assertIsNotNone(row[0])
            self.assertIn("<project>", row[0])
            self.assertNotIn(str(self.paths.project_root), row[0])
            log_file = self.paths.logs / "suite.log"
            if log_file.exists():  # handler filter scrubbed the logged warning too
                tail = log_file.read_text(encoding="utf-8", errors="ignore")[-4000:]
                self.assertNotIn(bad, tail)
        finally:
            if prev is None:
                os.environ.pop("SUITE_EVENT_LOG_DB", None)
            else:
                os.environ["SUITE_EVENT_LOG_DB"] = prev

    def test_seam_args_file_and_stdin(self):
        # T-seam gate (F0): --args-file <path> and --args-file - (stdin) both deliver hostile
        # JSON (nested objects, quotes, Windows backslash paths) intact  -  no shell escaping.
        import json as _json
        import os
        import subprocess
        import sys
        import tempfile
        from pathlib import Path as _P

        # This subprocess runs the seam from the sidecar's own source tree, which is not
        # a vended install and therefore has NO work target - every call would correctly
        # refuse. The test is about --args-file plumbing, not target binding, so bind one
        # explicitly.
        env = dict(os.environ, PYTHONIOENCODING="utf-8",
                   SUITE_PROJECT_ROOT=str(self.paths.root))
        nasty = {"message": 'nested "quotes" and C:\\win\\style\\path', "arr": [1, {"k": True}]}
        f = _P(tempfile.mkdtemp()) / "args.json"
        f.write_text(_json.dumps(nasty), encoding="utf-8")
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.app",
                "cli",
                "tool-call",
                "--tool",
                "ping",
                "--args-file",
                str(f),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=120,
        )
        d = _json.loads(r.stdout)
        self.assertTrue(d["ok"])
        self.assertIn("C:\\win\\style\\path", d["output"]["echo"])
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.app",
                "cli",
                "tool-call",
                "--tool",
                "ping",
                "--args-file",
                "-",
            ],
            input=_json.dumps({"message": "via stdin"}),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=120,
        )
        self.assertTrue(_json.loads(r.stdout)["ok"])
        # mutually exclusive with --args-json
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.app",
                "cli",
                "tool-call",
                "--tool",
                "ping",
                "--args-json",
                "{}",
                "--args-file",
                str(f),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=120,
        )
        self.assertFalse(_json.loads(r.stdout)["ok"])

    def test_seam_universal_apply(self):
        # T-seam gate (F1): apply:true executes every gated Apply tool; each legacy flag still
        # works; previews and refusals state the exact flag via apply_with.

        from src.core import invoke as invoke_mod

        # edit confines its path to the roots (C3), so probe lives in the gitignored _artifacts.
        probe = self.paths.root / "_artifacts" / "_apply_probe.txt"
        probe.parent.mkdir(parents=True, exist_ok=True)
        probe.write_text("hello world\n", encoding="utf-8")
        self.addCleanup(lambda: probe.unlink(missing_ok=True))
        # write-gated tool, universal flag
        r = invoke_mod.invoke(
            self.paths,
            "edit",
            {"path": str(probe), "pattern": "world", "replacement": "APPLIED", "apply": True},
        )
        self.assertTrue(r.ok, msg=getattr(r, "error", None))
        self.assertTrue(r.output.get("written"))
        self.assertIn("APPLIED", probe.read_text(encoding="utf-8"))
        # legacy flag untouched
        r = invoke_mod.invoke(
            self.paths,
            "edit",
            {"path": str(probe), "pattern": "APPLIED", "replacement": "LEGACY", "write": True},
        )
        self.assertTrue(r.output.get("written"))
        # preview (no flag) carries the hint
        r = invoke_mod.invoke(
            self.paths, "edit", {"path": str(probe), "pattern": "LEGACY", "replacement": "x"}
        )
        self.assertFalse(r.output.get("written"))
        self.assertEqual(r.output.get("apply_with"), {"apply": True})
        # dry-run/confirm tool: preview hint + refusal hint
        # A dry-run/confirm tool - previously `sidecar_install`, retired in T6. The
        # INTENT here is the universal Apply seam (preview hint, refusal hint,
        # apply:true executes), not installation, so any gated Apply tool serves.
        #
        # SCOPED TO A DIRECTORY THIS TEST OWNS. The first substitution called
        # `artifact_cleaner` with no root, which pointed a destructive cleanup at the
        # LIVE REPOSITORY and ran it with apply:true. It happened to delete nothing.
        # A test that proves a seam must not also be an unscoped Apply against the
        # tree it is running in.
        from pathlib import Path as _CleanPath
        cleanable = _CleanPath(self._tmp_path("cleanable"))
        cleanable.mkdir(parents=True, exist_ok=True)
        (cleanable / "junk.log").write_text("disposable\n", encoding="utf-8")
        clean_args = {"root": str(cleanable), "include_patterns": ["*.log"]}
        r = invoke_mod.invoke(self.paths, "artifact_cleaner", dict(clean_args))
        self.assertTrue(r.output.get("dry_run"))
        self.assertEqual(r.output.get("apply_with"), {"apply": True})
        r = invoke_mod.invoke(self.paths, "vendor_export", {"dry_run": False})
        self.assertFalse(r.ok)
        self.assertEqual(r.output.get("apply_with"), {"apply": True})
        # apply:true on a dry_run/confirm tool executes for real
        r = invoke_mod.invoke(self.paths, "artifact_cleaner",
                              dict(clean_args, apply=True))
        self.assertTrue(r.ok, msg=f"{r.error!r} {r.output!r}"[:400])
        self.assertFalse(r.output.get("dry_run"))
        self.assertFalse((cleanable / "junk.log").exists(),
                         "apply:true must actually execute, not merely report")

    def test_project_run(self):
        # T-operate gate (B1) + C2: dry-run plan, real execution with captured output + failure
        # classification, cwd confined to the roots, profile resolution  -  all through the seam.
        from src.core import invoke as invoke_mod

        cmd = "python -c \"print('PR_SMOKE_OK')\""
        r = invoke_mod.invoke(self.paths, "project_run", {"command": cmd})
        self.assertTrue(r.ok, msg=getattr(r, "error", None))
        self.assertTrue(r.output.get("dry_run"))
        self.assertEqual(r.output.get("would_run"), cmd)
        # apply, cwd within the roots (default project root)
        r = invoke_mod.invoke(self.paths, "project_run", {"command": cmd, "apply": True})
        self.assertTrue(r.ok, msg=getattr(r, "error", None))
        self.assertEqual(r.output.get("exit_code"), 0)
        self.assertEqual(r.output.get("classification"), "ok")
        self.assertIn("PR_SMOKE_OK", r.output.get("stdout_tail", ""))
        # C2 governance: a cwd outside the roots is refused
        esc = invoke_mod.invoke(self.paths, "project_run",
                                {"command": "echo hi", "apply": True, "cwd": "../../../.."})
        self.assertFalse(esc.ok)
        r = invoke_mod.invoke(self.paths, "project_run", {"profile": "smoke"})
        self.assertTrue(r.ok, msg=getattr(r, "error", None))
        self.assertIn("smoke_test.py", r.output.get("would_run", ""))

    def test_git_inspect(self):
        # T-operate gate (B4): read-only inspection verbs against this repo.
        from src.core import invoke as invoke_mod

        r = invoke_mod.invoke(self.paths, "git_inspect", {"action": "log", "n": 2})
        self.assertTrue(r.ok, msg=getattr(r, "error", None))
        self.assertGreaterEqual(len(r.output.get("entries", [])), 1)
        r = invoke_mod.invoke(
            self.paths,
            "git_inspect",
            {"action": "check-ignore", "paths": ["logs/x.log", "README.md"]},
        )
        self.assertTrue(r.output["ignored"]["logs/x.log"])
        self.assertFalse(r.output["ignored"]["README.md"])
        r = invoke_mod.invoke(
            self.paths,
            "git_inspect",
            {"action": "grep", "pattern": "instance_root", "path": "tools/_toolkit.py"},
        )
        self.assertGreaterEqual(int(r.output.get("count", 0)), 1)

    def test_http_probe_and_fetch(self):
        # T-operate gate (B2/B5): probe + gated fetch against a throwaway local server  -
        # no external network. Remote hosts refused without allow_remote.
        import hashlib
        import http.server
        import pathlib
        import socketserver
        import tempfile
        import threading

        from src.core import invoke as invoke_mod

        sdir = pathlib.Path(tempfile.mkdtemp())
        payload = b"SMOKE_LOCAL_ASSET " * 32
        (sdir / "asset.txt").write_bytes(payload)

        class H(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **kw):
                super().__init__(*a, directory=str(sdir), **kw)

            def log_message(self, *a):  # keep test output clean
                pass

        srv = socketserver.TCPServer(("127.0.0.1", 0), H)
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            r = invoke_mod.invoke(
                self.paths, "http_probe", {"url": f"http://127.0.0.1:{port}/asset.txt"}
            )
            self.assertTrue(r.ok, msg=getattr(r, "error", None))
            self.assertEqual(r.output.get("status"), 200)
            self.assertIn("SMOKE_LOCAL_ASSET", r.output.get("body_snippet", ""))
            r = invoke_mod.invoke(self.paths, "http_probe", {"url": "http://example.com/"})
            self.assertFalse(r.ok)  # non-local refused without allow_remote
            dest = str(sdir / "fetched.txt")
            r = invoke_mod.invoke(
                self.paths, "fetch", {"url": f"http://127.0.0.1:{port}/asset.txt", "dest": dest}
            )
            self.assertTrue(r.output.get("dry_run"))
            self.assertEqual(r.output.get("apply_with"), {"apply": True})
            r = invoke_mod.invoke(
                self.paths,
                "fetch",
                {"url": f"http://127.0.0.1:{port}/asset.txt", "dest": dest, "apply": True},
            )
            self.assertTrue(r.ok, msg=getattr(r, "error", None))
            self.assertEqual(r.output.get("sha256"), hashlib.sha256(payload).hexdigest())
            self.assertEqual(pathlib.Path(dest).read_bytes(), payload)
        finally:
            srv.shutdown()

    def test_signal_analyzers(self):
        # T-signal gate: against tests/fixtures/signal_proj, the opinionated analyzers signal
        # correctly instead of flagging valid architecture (field report C1/C2/C3).
        from src.core import invoke as invoke_mod

        root = "tests/fixtures/signal_proj"

        # dead_code (G6): a real dead fn is high; framework entrypoints and __all__ exports are
        # ROOTS now - the graph can PROVE they are live, so they are not candidates at all
        # (pre-G6 they appeared as low-confidence noise because the tool could not tell).
        r = invoke_mod.invoke(self.paths, "dead_code", {"root": root})
        self.assertTrue(r.ok, msg=getattr(r, "error", None))
        conf = {c["name"]: c["confidence"] for c in r.output["candidates"]}
        self.assertEqual(conf.get("genuinely_dead"), "high")
        self.assertNotIn("PublicThing", conf)   # __all__ export -> root, live
        self.assertNotIn("plan_list", conf)     # @app.command -> root, live
        self.assertNotIn("read_items", conf)    # @router.get -> root, live
        skipped = r.output["skipped"]
        self.assertGreaterEqual(skipped.get("framework_decorator", 0), 2)
        self.assertGreaterEqual(skipped.get("exported", 0), 1)

        # blocking_call_scan: only the async-context call is a finding.
        r = invoke_mod.invoke(self.paths, "blocking_call_scan", {"root": root})
        finding_calls = {(f["call"], f["context"]) for f in r.output["findings"]}
        info_calls = {(f["call"], f["context"]) for f in r.output["informational"]}
        self.assertIn(("time.sleep", "read_items"), finding_calls)
        self.assertNotIn(("subprocess.run", "sync_handler"), finding_calls)
        self.assertIn(("subprocess.run", "sync_handler"), info_calls)

        # domain_boundary_audit: no verdict without a policy; exact violation with one.
        r = invoke_mod.invoke(self.paths, "domain_boundary_audit", {"root": root})
        self.assertEqual(r.output["verdict"], "none (no policy supplied)")
        self.assertIsNone(r.output["violation_count"])
        self.assertFalse(any(c["allowed"] is False for c in r.output["crossings"]))
        r = invoke_mod.invoke(
            self.paths,
            "domain_boundary_audit",
            {
                "root": root,
                "policy": {"allowed_edges": ["cli->services", "web->services", "services->domain"]},
            },
        )
        self.assertEqual(r.output["verdict"], "policy applied")
        viols = {(v["from_domain"], v["to_domain"]) for v in r.output["violations"]}
        self.assertEqual(viols, {("domain", "services")})

    def test_domain_boundary_policy_profiles(self):
        import json

        profile_name = f"smoke-{uuid.uuid4().hex}"
        profile_dir = self.paths.root / "config" / "domain-boundary"
        profile_path = profile_dir / f"{profile_name}.json"
        profile_dir.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(
            json.dumps(
                {
                    "name": "Smoke layered architecture",
                    "layers": {
                        "cli": "adapter",
                        "web": "adapter",
                        "services": "application",
                        "domain": "domain",
                    },
                    "allowed_edges": [
                        "adapter->application",
                        "application->domain",
                    ],
                }
            ),
            encoding="utf-8",
        )
        try:
            result = invoke_mod.invoke(
                self.paths,
                "domain_boundary_audit",
                {
                    "root": "tests/fixtures/signal_proj",
                    "policy_profile": profile_name,
                },
            )
        finally:
            profile_path.unlink(missing_ok=True)

        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.output["policy_source"], f"profile:{profile_name}")
        self.assertEqual(result.output["policy_name"], "Smoke layered architecture")
        self.assertEqual(result.output["policy_status"], "fail")
        self.assertEqual(result.output["unmapped_domains"], [])
        self.assertIn(profile_name, result.output["available_policy_profiles"])
        self.assertEqual(result.output["violation_count"], 1)
        violation = result.output["violations"][0]
        self.assertEqual(
            (
                violation["from_domain"],
                violation["to_domain"],
                violation["from_layer"],
                violation["to_layer"],
            ),
            ("domain", "services", "domain", "application"),
        )

        escaped = invoke_mod.invoke(
            self.paths,
            "domain_boundary_audit",
            {
                "root": "tests/fixtures/signal_proj",
                "policy_profile": "../outside",
            },
        )
        self.assertFalse(escaped.ok)
        self.assertIn("policy_profile", escaped.error)

        malformed = invoke_mod.invoke(
            self.paths,
            "domain_boundary_audit",
            {
                "root": "tests/fixtures/signal_proj",
                "policy": {"layers": [], "allowed_edges": ["adapter-domain"]},
            },
        )
        self.assertFalse(malformed.ok)
        self.assertIn("policy.layers", malformed.error)

    def test_self_lint_clean(self):
        # T-seal gate (C5): the toolkit lints itself to zero under the committed ruff.toml.
        # Skips where ruff is not installed (it is a dev-time tool, not a runtime dep).
        import shutil
        import subprocess
        import sys

        if shutil.which("ruff") is None:
            try:
                import ruff  # noqa: F401
            except Exception:
                self.skipTest("ruff not installed")
        r = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            cwd=str(self.paths.root),
            capture_output=True,
            text=True,
            # Windows pipes default to cp1252, which raises UnicodeDecodeError on ruff's
            # output and destroys the failure message - the assertion below then reports
            # "1 != 0" with nothing to act on.
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        self.assertEqual(r.returncode, 0, msg=(r.stdout or r.stderr)[-1500:])

    def test_event_log_rollup(self):
        import os
        import tempfile

        dbp = os.path.join(tempfile.mkdtemp(), "ev.sqlite3")
        prev = os.environ.get("SUITE_EVENT_LOG_DB")
        os.environ["SUITE_EVENT_LOG_DB"] = dbp
        try:
            invoke_mod.invoke(self.paths, "ping", {"message": "x"})
            invoke_mod.invoke(
                self.paths, "journal", {"action": "list"}, allow="Observe"
            )  # a denial
            r = invoke_mod.invoke(self.paths, "event_log", {"action": "rollup"})
            self.assertTrue(r.ok, r.error)
            self.assertGreaterEqual(r.output["total"], 2)
            self.assertGreaterEqual(r.output["denials"], 1)
            self.assertIn("Governance rollup", r.output["markdown"])
        finally:
            if prev is None:
                os.environ.pop("SUITE_EVENT_LOG_DB", None)
            else:
                os.environ["SUITE_EVENT_LOG_DB"] = prev

    def test_authority_enforcement(self):
        import os
        import tempfile

        prev_auth = os.environ.get("SUITE_MAX_AUTHORITY")
        prev_db = os.environ.get("SUITE_EVENT_LOG_DB")
        os.environ["SUITE_EVENT_LOG_DB"] = os.path.join(tempfile.mkdtemp(), "ev.sqlite3")
        try:
            # per-call allow tightens: an Apply tool is denied when caller allows only Observe
            d = invoke_mod.invoke(self.paths, "journal", {"action": "list"}, allow="Observe")
            self.assertFalse(d.ok)
            self.assertIn("authority denied", d.error)
            # an Observe tool passes under the same clamp
            o = invoke_mod.invoke(self.paths, "ping", {"message": "x"}, allow="Observe")
            self.assertTrue(o.ok, o.error)
            # env ceiling also enforces
            os.environ["SUITE_MAX_AUTHORITY"] = "Observe"
            self.assertFalse(invoke_mod.invoke(self.paths, "journal", {"action": "list"}).ok)
            # default (config Apply, no clamp) allows Apply
            os.environ.pop("SUITE_MAX_AUTHORITY", None)
            self.assertTrue(invoke_mod.invoke(self.paths, "journal", {"action": "list"}).ok)
        finally:
            for k, v in (("SUITE_MAX_AUTHORITY", prev_auth), ("SUITE_EVENT_LOG_DB", prev_db)):
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_broken_governance_config_degrades_audibly(self):
        """A governance ceiling that cannot be read must SAY SO and must WITHHOLD Apply.

        The defect this pins: `_config_ceiling` caught `Exception` and returned None, and
        an unrecognised value fell through the same way - so an operator who clamped a
        sensitive target to `Observe` and mistyped the file got the MOST PERMISSIVE
        ceiling with no indication whatever. Two distinct silent paths, one outcome:
        a governance control that is not in force and looks exactly like one that is.

        AUDIBILITY WAS FIXED FIRST AND THE POSTURE DELIBERATELY LEFT ALONE, because
        changing a security posture is the operator's decision and not a review's. T8
        made that decision: a bench that can rewrite arbitrary target files must not read
        an unreadable mutation control as permission to mutate. This test now pins the
        new posture, and the cases that were ALREADY correct are unchanged.

        Cases 3, 4 and 5 are the load-bearing half. Without them the degradation could be
        implemented as "always clamp, always warn", which would satisfy 1 and 2 while
        meaning nothing at all: absent, unspecified and valid must all stay permissive
        and silent, because none of them is a broken control.
        """
        import json
        import logging
        import tempfile
        from dataclasses import replace
        from pathlib import Path

        from src.core import policy

        root = Path(tempfile.mkdtemp(prefix="gov-"))
        (root / "config").mkdir(parents=True)
        cfg = root / "config" / "governance.json"
        paths = replace(self.paths, root=root)

        def ceiling_and_logs(text):
            cfg.write_text(text, encoding="utf-8")
            with self.assertLogs("suite.core.policy", level=logging.WARNING) as cm:
                got = policy.effective_ceiling(paths)
            return got, "\n".join(cm.output)

        # 1. malformed JSON -> DEGRADED, and it warns
        got, logs = ceiling_and_logs('{ "max_authority": "Observe"')
        self.assertEqual(got, policy.DEGRADED_CEILING)
        self.assertIn("DEGRADING", logs)
        self.assertEqual(policy.decide(paths, "Apply")[0], False)
        self.assertEqual(policy.decide(paths, "Observe")[0], True)

        # 2. a value outside AUTHORITIES (lowercase typo) -> DEGRADED, and it warns
        got, logs = ceiling_and_logs('{"max_authority": "observe"}')
        self.assertEqual(got, policy.DEGRADED_CEILING)
        self.assertIn("not one of", logs)
        self.assertEqual(policy.decide(paths, "Apply")[0], False)

        # 2b. THE DEGRADATION IS NOT THE PERMISSIVE DEFAULT. Asserting only
        #     `== DEGRADED_CEILING` would still pass if someone set DEGRADED_CEILING back
        #     to "Apply", which is the exact regression this whole change exists to
        #     prevent. Naming the relationship pins it independently of either constant.
        self.assertNotEqual(policy.DEGRADED_CEILING, policy.DEFAULT_CEILING)
        self.assertEqual(policy.DEGRADED_CEILING, "Observe")

        # 3. a VALID clamp is silent AND enforced. Without this the warning could be
        #    made unconditional, which would pass 1 and 2 while meaning nothing.
        cfg.write_text('{"max_authority": "Observe"}', encoding="utf-8")
        with self.assertNoLogs("suite.core.policy", level=logging.WARNING):
            self.assertEqual(policy.effective_ceiling(paths), "Observe")
        self.assertEqual(policy.decide(paths, "Apply"), (False, "Observe"))

        # 4. no config at all is not a degradation, and must stay silent.
        #    A SEPARATE ROOT, deliberately, rather than deleting the one above: the
        #    development mount denies unlink, so `cfg.unlink()` failed here for a reason
        #    with nothing to do with governance - the exact class of assertion this
        #    project keeps finding. A test must not need a capability it is not testing.
        bare = Path(tempfile.mkdtemp(prefix="gov-bare-"))
        with self.assertNoLogs("suite.core.policy", level=logging.WARNING):
            self.assertEqual(policy.effective_ceiling(replace(self.paths, root=bare)),
                             policy.DEFAULT_CEILING)

        # 5. a config that simply declares no ceiling is also not a degradation
        cfg.write_text(json.dumps({"note": "no ceiling here"}), encoding="utf-8")
        with self.assertNoLogs("suite.core.policy", level=logging.WARNING):
            self.assertEqual(policy.effective_ceiling(paths), policy.DEFAULT_CEILING)


    def test_canonical_observation_selects_rather_than_denylists(self):
        """Evidence identity is built by SELECTION; runtime metadata never enters it.

        A HELPER-LEVEL test on purpose. The black-box gate cannot reach this: none of the
        three current contributors emits a timestamp, so removing the exclusion entirely
        left the gate green (verified by mutation). The invariant is real even where the
        current fixtures cannot exercise it, so it is pinned at the level where it lives.

        The defect this replaces was a VOLATILE_KEYS denylist stripping key NAMES -
        `path`, `created`, `db`, `root` - recursively from arbitrary tool output. Two
        failures in one:

          it DISCARDED REAL EVIDENCE. `path` is which file a finding is about; `created`
          is a record's own date. A finding moving from a.txt to b.txt produced the SAME
          fingerprint, so awareness reported "nothing changed" about a target that had.

          it was a DENYLIST, wrong in only one direction: every future contributor field
          participates until someone remembers to exclude it.

        A key name cannot tell you whether a value is noise. Selection can.
        """
        from tools.awareness_shared import canonical_observation, fingerprint

        noisy = {
            "summary": {"files": 3, "classes": 1, "functions": 9},
            # runtime metadata: must NOT reach the canonical observation
            "generated_at": "2026-08-16T12:00:00Z", "duration_ms": 412,
            "root": "/tmp/build-a/proj", "evidence_id": "ev-1",
            # THE DISCRIMINATOR. Bulky, unlisted, and not part of the semantic
            # projection. A denylist keeps it (nobody named it); selection drops it
            # (nobody reached for it). Without a field of this shape the fixture cannot
            # tell the two implementations apart - verified by mutation: an earlier
            # version of this test contained only fields both approaches agreed on, and
            # a restored denylist passed it.
            "markdown": "# Report\n" + ("verbose rendering\n" * 40),
        }
        noisy["modules"] = [
            {"file": "src/backend.py", "purpose": "",
             "classes": [{"name": "Backend", "doc": "ROLE: Orchestration Hub."}]},
        ]
        c1 = canonical_observation("report", noisy)
        self.assertEqual(c1["summary"], {"files": 3, "classes": 1, "functions": 9})
        # The purpose comes from the CLASS, not the empty module docstring - measured on
        # `_theCELL`, where every useful line lived on a class and `src/backend.py` had
        # no module docstring at all.
        self.assertEqual(c1["purposes"], {"src/backend.py": "ROLE: Orchestration Hub."})
        for volatile in ("generated_at", "duration_ms", "root", "evidence_id"):
            self.assertNotIn(volatile, c1)
        self.assertNotIn("markdown", c1)

        # And the other half: a field named like "volatile" that IS the evidence must
        # survive, because selection reaches for it. `sqlite_inspect`'s table names are
        # the observation; a denylist carrying "tables" or "path" would erase them.
        tables = canonical_observation(
            "sqlite_inspect", {"tables": [{"name": "records"}, {"name": "audit"}],
                               "db": "/tmp/x/app.sqlite3", "duration_ms": 9})
        self.assertEqual(tables, {"tables": ["audit", "records"]})

        # Same findings observed later, elsewhere, taking longer -> identical identity.
        c2 = canonical_observation("report", {
            **noisy, "generated_at": "2026-09-01T04:00:00Z", "duration_ms": 3,
            "root": "/elsewhere/entirely/proj", "evidence_id": "ev-999"})
        self.assertEqual(c1, c2)
        obs = [{"tool": "report", "canonical": c1, "ok": True}]
        self.assertEqual(fingerprint("", obs),
                         fingerprint("", [{"tool": "report", "canonical": c2, "ok": True}]))

        # And the half a denylist got backwards: a REAL change must still register.
        changed = canonical_observation("report", {**noisy, "summary": {"files": 4}})
        self.assertNotEqual(c1, changed)
        self.assertNotEqual(
            fingerprint("", obs),
            fingerprint("", [{"tool": "report", "canonical": changed, "ok": True}]))

        # Scope participates, but only relatively - an absolute path would make a
        # relocated target look different (gates/t07 asserts the same thing end to end).
        self.assertNotEqual(fingerprint("", obs), fingerprint("src", obs))


    def test_awareness_persistence_failure_does_not_break_orientation(self):
        """Awareness is an ENRICHMENT on orientation. It must not take the front door down.

        `build()` persists, and `_persist` mkdir'd and wrote with nothing catching it -
        so an unwritable state root (read-only mount, full disk, a file sitting where the
        directory belongs) raised straight out of `attach.run()`. The user loses their
        PROJECT_MAP, workbench and next steps because a *derived* record could not be
        saved.

        The seam already holds this line for the same reason: `_announce` wraps presence
        in try/except because "visibility is an enrichment; it must never break a
        dispatch". Same rule, one layer up.

        The envelope must still come back - awareness that was COMPOSED is real
        knowledge even if it could not be stored - and it must SAY it was not persisted,
        because a caller that re-engages later will not find it.
        """
        import os
        import tempfile
        from pathlib import Path

        from tools import awareness_shared

        state = Path(tempfile.mkdtemp(prefix="aw-state-"))
        # A file where the directory has to go: mkdir cannot succeed, and no amount of
        # permission juggling is needed to reproduce it on any platform.
        (state / awareness_shared.AWARENESS_DIR).write_text("not a directory\n",
                                                           encoding="utf-8")
        # `awareness_shared` is a TOOL-side module: it consumes TRANSPORTED roots and
        # refuses to infer them (MissingRuntimeContext). Supply the whole context, not
        # just the one under test - a test that omits it fails for a reason unrelated to
        # what it is asserting.
        target = Path(tempfile.mkdtemp(prefix="aw-target-"))
        keys = ("SUITE_STATE_ROOT", "SUITE_PROJECT_ROOT", "SUITE_HOME")
        prev = {k: os.environ.get(k) for k in keys}
        os.environ.update(SUITE_STATE_ROOT=str(state), SUITE_PROJECT_ROOT=str(target),
                          SUITE_HOME=str(self.paths.root))
        try:
            env = awareness_shared.build({"domain": "generic"}, {"file_count": 0}, False)
        finally:
            for k, v in prev.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

        self.assertTrue(env, "composing awareness must survive a persistence failure")
        self.assertTrue(env.get("revision"), "the revision is still validly derived")
        self.assertFalse(env.get("persisted", True),
                         "an unpersisted envelope must say so")
        self.assertTrue(
            any("persist" in str(x).lower() or "stored" in str(x).lower()
                for x in (env.get("limitations") or [])),
            f"limitations must name the failure; got {env.get('limitations')}")


if __name__ == "__main__":
    unittest.main()
