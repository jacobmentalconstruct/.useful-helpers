#!/usr/bin/env python3
"""
FILE:       _docs/parity/parity_check.py
ROLE:       The bounded parity verifier - six assertions, one per FAILING census row.
DOMAIN:     factory
DOES:       Drives the CURRENT governed runtime against a small fixture and asserts the
            six owed useful outcomes from PARITY_MATRIX.md. Prints one line per row.
DEPENDS ON: stdlib only. Calls the product through `src.app cli tool-call`.
NOTES:      DELIBERATELY NOT A GATE FRAMEWORK. `gates/run.py` already exists and is the
            right home for tranche outcomes; parity is a finite closure list of six rows
            that will be deleted from the "owed" column once green. Six assertions in one
            file is the proportionate instrument. If this grows a plugin system, it has
            become the thing the C1 anti-scope-creep rule forbids.

            EVERY ASSERTION GOES THROUGH THE SEAM, not through an import. A parity row is
            a claim about the PRODUCT, and importing the tool module would prove something
            about a function while the governed entrance stayed broken.

            Run:  python _docs/parity/parity_check.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ROWS: list[tuple[str, bool, str]] = []


def record(row: str, ok: bool, detail: str) -> None:
    ROWS.append((row, ok, detail))


def call(target: Path, tool: str, args: dict, timeout: int = 300) -> dict:
    """One governed call. Returns the FULL envelope; `ok` here is the seam's verdict."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("SUITE_HOME", "SUITE_PROJECT_ROOT", "SUITE_STATE_ROOT")}
    env["SUITE_PROJECT_ROOT"] = str(target)
    p = subprocess.run(
        [sys.executable, "-m", "src.app", "cli", "tool-call", "--tool", tool,
         "--args-json", json.dumps(args)],
        cwd=str(ROOT), capture_output=True, text=True, timeout=timeout, env=env)
    try:
        return json.loads(p.stdout)
    except ValueError:
        return {"ok": False, "error": (p.stderr or p.stdout)[-300:], "output": None}


def out(env: dict) -> dict:
    """The tool's own payload. `or {}` ONLY after checking - a null output is not an
    empty result, which is the lesson this census learned the hard way."""
    o = env.get("output")
    return o if isinstance(o, dict) else {}


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True)
    return (p.stdout or "") + (p.stderr or "")


# --------------------------------------------------------------------------- fixtures
def software_fixture() -> Path:
    t = Path(tempfile.mkdtemp(prefix="parity-")) / "proj"
    (t / "src").mkdir(parents=True)
    (t / "keep").mkdir()
    (t / "drop").mkdir()
    (t / "src" / "a.py").write_text("VALUE = 'a'\n", encoding="utf-8")
    (t / "src" / "b.py").write_text("VALUE = 'b'\n", encoding="utf-8")
    (t / "keep" / "kept.txt").write_text("kept\n", encoding="utf-8")
    (t / "drop" / "dropped.txt").write_text("dropped\n", encoding="utf-8")
    (t / "README.md").write_text("# parity fixture\n", encoding="utf-8")
    return t


def git_fixture() -> Path:
    t = Path(tempfile.mkdtemp(prefix="parity-git-")) / "repo"
    t.mkdir(parents=True)
    (t / ".gitignore").write_text("*.log\n", encoding="utf-8")
    git(t, "init", "-q")
    git(t, "config", "user.email", "parity@local")
    git(t, "config", "user.name", "parity")
    (t / "first.txt").write_text("one\n", encoding="utf-8")
    git(t, "add", ".")
    git(t, "commit", "-qm", "base")
    return t


# --------------------------------------------------------------------------- the six
def row_1_6(t: Path) -> None:
    """The artifact must record the selection that produced it."""
    env = call(t, "projectmapper",
               {"action": "compile", "root": ".", "name": "parity",
                "exclude_paths": ["drop"], "apply": True})
    o = out(env)
    outputs = o.get("outputs") or {}
    db = outputs.get("sqlite") or outputs.get("db") or outputs.get("snapshot")
    recorded = ""
    if db and Path(db).is_file():
        import sqlite3
        con = sqlite3.connect(db)
        try:
            rows = con.execute(
                "SELECT key, value FROM meta"
            ).fetchall() if _has_table(con, "meta") else []
            recorded = json.dumps(rows)
        finally:
            con.close()
    blob = recorded + json.dumps(o)
    record("1.6 capture selection is reproducible from the artifact",
           "exclude_paths" in blob and "drop" in blob,
           f"the snapshot must record the deselection that shaped it; ok={env.get('ok')} "
           f"outputs={list(outputs)} recorded_meta={recorded[:200]!r}")


def _has_table(con, name: str) -> bool:
    return bool(con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())


def row_2_5(t: Path) -> None:
    """One reviewed patch operation spanning more than one file."""
    env = call(t, "patch", {
        "action": "apply", "apply": True,
        "patch": {"files": [
            {"path": "src/a.py",
             "hunks": [{"search_block": "VALUE = 'a'", "replace_block": "VALUE = 'A'"}]},
            {"path": "src/b.py",
             "hunks": [{"search_block": "VALUE = 'b'", "replace_block": "VALUE = 'B'"}]},
        ]}})
    a = (t / "src" / "a.py").read_text(encoding="utf-8")
    b = (t / "src" / "b.py").read_text(encoding="utf-8")
    record("2.5 one governed patch set spans multiple files",
           "VALUE = 'A'" in a and "VALUE = 'B'" in b,
           f"both files must change in ONE governed call; a={a.strip()!r} b={b.strip()!r} "
           f"err={env.get('error')!r}")


def row_4_2(repo: Path) -> None:
    """Commit only what was approved. The other dirty file must stay uncommitted."""
    (repo / "approved.txt").write_text("yes\n", encoding="utf-8")
    (repo / "unapproved.txt").write_text("no\n", encoding="utf-8")
    env = call(repo, "git", {"repo": str(repo), "action": "commit",
                             "message": "only the approved set",
                             "paths": ["approved.txt"], "apply": True})
    committed = git(repo, "show", "--stat", "--name-only", "--format=", "HEAD")
    still_dirty = git(repo, "status", "--porcelain")
    record("4.2 commit stages ONLY the explicit approved working set",
           "approved.txt" in committed and "unapproved.txt" not in committed
           and "unapproved.txt" in still_dirty,
           f"staging the whole tree is not this product; committed={committed.split()!r} "
           f"dirty={still_dirty.split()!r} err={env.get('error')!r}")


def row_4_6(repo: Path) -> None:
    """Pull must happen BEFORE push, and be visible in the recorded steps."""
    bare = repo.parent / "remote.git"
    if not bare.exists():
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=False)
        git(repo, "remote", "add", "origin", str(bare))
        git(repo, "push", "-q", "-u", "origin", "HEAD")
    (repo / "second.txt").write_text("two\n", encoding="utf-8")
    env = call(repo, "git", {"repo": str(repo), "action": "sync",
                             "message": "second change", "pull": True, "apply": True})
    # THE SUBCOMMAND, NOT A SUBSTRING. This first read `"pull" in cmd`, and the fixture's
    # own commit message was "sync with pull first" - so the COMMIT step matched and the
    # assertion went green against a runtime with no pull at all. A false green caused
    # entirely by text I controlled, which is the same family as every other one this
    # project has caught: satisfied for a reason unrelated to the product. Renaming the
    # message would have hidden it; matching the verb is what fixes it.
    verbs = [(c.split() + ["", ""])[1] for c in
             (s.get("cmd", "") for s in (out(env).get("steps") or []))]
    pulled = "pull" in verbs
    pushed = "push" in verbs
    ordered = pulled and pushed and verbs.index("pull") < verbs.index("push")
    record("4.6 pull runs before push in one governed sync",
           pulled and pushed and ordered,
           f"a push that never pulled can clobber; git verbs={verbs!r} "
           f"err={env.get('error')!r}")


def row_4_7(repo: Path) -> None:
    """Minimum branch operations, with the dirty state visible."""
    (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    env = call(repo, "git", {"repo": str(repo), "action": "branch",
                             "branch": "parity-topic", "create": True, "apply": True})
    o = out(env)
    current = git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
    record("4.7 branch management reports dirty state",
           current == "parity-topic" and o.get("clean") is False,
           f"switching with uncommitted work must be visible; branch={current!r} "
           f"clean={o.get('clean')!r} err={env.get('error')!r}")


def row_6_4(t: Path) -> None:
    """A uniquely named file is CREATED, not refused."""
    (t / "note.txt").write_text("original\n", encoding="utf-8")
    env = call(t, "write_file", {"path": "note.txt", "content": "second\n",
                                 "overwrite": False, "unique": True, "apply": True})
    o = out(env)
    written = o.get("path") or ""
    others = sorted(p.name for p in t.glob("note*.txt"))
    record("6.4 a uniquely named file is created rather than refused",
           bool(written) and Path(str(written)).name != "note.txt" and len(others) >= 2
           and (t / "note.txt").read_text(encoding="utf-8") == "original\n",
           f"refusing is a different outcome from uniquifying; wrote={written!r} "
           f"files={others!r} err={env.get('error')!r}")


def main() -> int:
    soft = software_fixture()
    repo = git_fixture()
    try:
        row_1_6(soft)
        row_2_5(soft)
        row_4_2(repo)
        row_4_6(repo)
        row_4_7(repo)
        row_6_4(soft)
    finally:
        for d in (soft.parent, repo.parent):
            shutil.rmtree(d, ignore_errors=True)

    print("\nPARITY — the six owed rows\n" + "-" * 74)
    for name, ok, detail in ROWS:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            print(f"         {detail}")
    bad = [r for r in ROWS if not r[1]]
    print(f"\n{len(ROWS) - len(bad)}/{len(ROWS)} owed rows satisfied")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
