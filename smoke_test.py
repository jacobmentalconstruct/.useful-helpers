"""
FILE:       smoke_test.py
ROLE:       `run smoke` - verify THIS installation, or run the factory suite in the factory.
DOMAIN:     testing
DOES:       In an installed instance: six bounded assertions about the instance itself -
            identity, registry, manifest truth, the seam, the seam's refusal, awareness.
            In the source checkout: discovers and runs tests/ exactly as before.
DEPENDS ON: (stdlib) unittest, subprocess, json, sys, pathlib
WIRES TO:   run.sh smoke | run.bat smoke; CI runs it from the checkout.
NOTES:      IT USED TO RUN THE FACTORY'S SUITE WHEREVER IT LANDED, and `run smoke` is
            documented as "verify this installation". Those are different suites. The
            toolkit's own tests bind their work target to the instance's target - which in
            sidecar use is the USER'S project - and then assert this repository's layout
            against it: `src/core` is a directory, `requirements.txt` is a file, the root
            is a git repository, `tests/fixtures/signal_proj` exists. On a records folder
            that is 23 failures and 3 errors, every one of them describing the customer's
            directory rather than the product. There was no subset worth keeping: 245
            assertions across its 89 methods reach through the work target.

            So `tests/` no longer ships (see `payload.NEVER_SHIP`), and the installed
            command answers the question it was always advertised to answer. In the
            factory there IS no instance, the work target is the toolkit itself, and the
            full suite is exactly right - so that path is untouched, including in CI.

            Bounded on purpose. Six checks that can each be wrong in one way, run through
            the same documented CLI a user has, with no fixtures and no scratch state. An
            installation self-check that needs a rig is not one.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

HOME = Path(__file__).resolve().parent
INSTALLED = (HOME / "instance.json").is_file()


def cli(*args: str, timeout: int = 300) -> "tuple[int, dict]":
    """One call through the documented CLI, the way a user makes it. Returns (rc, envelope)."""
    p = subprocess.run([sys.executable, "-m", "src.app", "cli", *args],
                       cwd=str(HOME), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    try:
        return p.returncode, json.loads(p.stdout)
    except ValueError:
        return p.returncode, {"ok": False, "error": ((p.stderr or p.stdout) or "")[-300:]}


class InstallationSelfCheck(unittest.TestCase):
    """What must be true of THIS instance for it to be usable at all."""

    def test_1_identity_resolves_and_names_this_folder(self):
        ident = json.loads((HOME / "instance.json").read_text(encoding="utf-8"))
        self.assertTrue(ident.get("uuid"), "instance.json carries no uuid")
        target = Path(ident.get("target") or "")
        self.assertTrue(target.is_dir(), f"the bound target is not a directory: {target}")
        self.assertEqual(HOME.parent.resolve(), target.resolve(),
                         "the instance is not bound to the folder it lives in")

    def test_2_the_registry_loads_and_is_not_empty(self):
        rc, env = cli("tool-list")
        self.assertEqual(0, rc, f"tool-list exited {rc}: {env.get('error')}")
        tools = (env.get("output") or env).get("tools") or []
        self.assertTrue(tools, "the registry names no tools")

    def test_3_every_tool_the_registry_names_has_its_entry(self):
        # The one assertion here that catches a SUBTRACTIVE packaging error. A registry
        # promising 94 tools while the payload carries 90 is a product that fails on the
        # fourth thing a user reaches for, and nothing else in this file would notice.
        rc, env = cli("tool-list")
        self.assertEqual(0, rc, "tool-list did not answer")
        missing = []
        for t in (env.get("output") or env).get("tools") or []:
            entry = ((t.get("invocation") or {}).get("entry") or "")
            if entry and not (HOME / entry).is_file():
                missing.append(f"{t.get('id')} -> {entry}")
        self.assertEqual([], missing, f"registered tools with no entry file: {missing[:6]}")

    def test_4_the_seam_answers(self):
        rc, env = cli("tool-call", "--tool", "ping", "--args-json", "{}")
        self.assertEqual(0, rc, f"ping exited {rc}")
        self.assertTrue(env.get("ok"), f"ping was not ok: {env.get('error')}")

    def test_5_the_seam_refuses_what_it_does_not_have(self):
        # A seam that has only ever been seen to say yes has not been shown to say no,
        # and every check above reads success from an exit code. `run.bat` returned 0 for
        # eight modes unconditionally; this is the assertion that catches that class from
        # inside the product rather than from a release gate.
        rc, env = cli("tool-call", "--tool", "__no_such_tool__", "--args-json", "{}")
        self.assertNotEqual(0, rc, "an unknown tool was not refused with a non-zero exit")
        self.assertFalse(env.get("ok"), "an unknown tool reported ok")

    def test_6_awareness_maps_this_target(self):
        rc, env = cli("tool-call", "--tool", "attach", "--args-json", "{}")
        self.assertEqual(0, rc, f"attach exited {rc}")
        out = env.get("output") or {}
        self.assertTrue(out.get("ok"), f"attach was not ok: {env.get('error')}")
        self.assertTrue(out.get("project_map"), "attach returned no project map")


def run() -> int:
    if INSTALLED:
        suite = unittest.TestLoader().loadTestsFromTestCase(InstallationSelfCheck)
    else:
        # The factory. No instance exists, the work target is the toolkit itself, and the
        # full suite is the right thing to run - which is what CI does.
        suite = unittest.TestLoader().discover("tests", top_level_dir=".")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run())
