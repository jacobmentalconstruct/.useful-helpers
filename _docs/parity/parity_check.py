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
    # An EXPLICIT `out` inside a dot-folder: the tool's source-integrity guard permits
    # co-locating output in the project only within a sidecar the scan skips, and knowing
    # where the artifact landed is the only way to read it back. `outputs.snapshot_db` is
    # a FILENAME, not a path - I guessed three other key names before reading the output,
    # which is the same reader-guessing this census keeps punishing.
    db = t / ".parity-out" / "snap.sqlite3"
    env = call(t, "projectmapper",
               {"action": "compile", "root": ".", "name": "parity",
                "exclude_paths": ["drop"], "out": str(db), "apply": True})

    recorded: dict[str, str] = {}
    if db.is_file():
        import sqlite3
        con = sqlite3.connect(db)
        try:
            if _has_table(con, "snapshot_metadata"):
                recorded = dict(con.execute(
                    "SELECT key, value FROM snapshot_metadata").fetchall())
        finally:
            con.close()
    manifest_file = db.parent / (db.stem + ".manifest.json")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8")) \
        if manifest_file.is_file() else {}
    generation = manifest.get("generation") or {}

    # BOTH HALVES MUST AGREE, and the regenerate command must actually carry the scope:
    # a snapshot that says "run this to reproduce me" while the command reproduces a WIDER
    # capture is worse than one that offers no command at all.
    regen = str(recorded.get("regenerate_command", ""))
    # REGENERATE FROM THE RECORDED COMMAND and compare the capture, rather than admiring
    # the metadata. A command that reproduces a DIFFERENT scope is the defect this row
    # exists for, and only running it can tell.
    first_checksum = recorded.get("content_checksum_sha256")
    first_files = recorded.get("text_file_count")
    regen_ok, regen_detail = False, "no regenerate_command recorded"
    if regen.startswith("python -m src.app"):
        import shlex
        argv = shlex.split(regen)[1:]
        rp = subprocess.run([sys.executable, *argv], cwd=str(ROOT), capture_output=True,
                            text=True, timeout=300, env={
                                **{k: v for k, v in os.environ.items()
                                   if k not in ("SUITE_HOME", "SUITE_PROJECT_ROOT",
                                                "SUITE_STATE_ROOT")},
                                "SUITE_PROJECT_ROOT": str(t)})
        again = {}
        if db.is_file():
            import sqlite3
            con = sqlite3.connect(db)
            try:
                if _has_table(con, "snapshot_metadata"):
                    again = dict(con.execute(
                        "SELECT key, value FROM snapshot_metadata").fetchall())
            finally:
                con.close()
        regen_ok = (again.get("content_checksum_sha256") == first_checksum
                    and again.get("text_file_count") == first_files
                    and again.get("exclude_paths") == recorded.get("exclude_paths"))
        regen_detail = (f"rc={rp.returncode} checksum {first_checksum!r} -> "
                        f"{again.get('content_checksum_sha256')!r}; files {first_files!r} "
                        f"-> {again.get('text_file_count')!r}; deselection "
                        f"{recorded.get('exclude_paths')!r} -> {again.get('exclude_paths')!r}")
    record("1.6b regenerating from the recorded command reproduces the SAME capture",
           regen_ok,
           "a snapshot that offers a command reproducing a different scope is worse than "
           f"one offering none; {regen_detail}")

    record("1.6 capture selection is reproducible from the artifact",
           "drop" in str(recorded.get("exclude_paths", ""))
           and "drop" in json.dumps(generation.get("exclude_paths"))
           and "drop" in regen,
           f"the snapshot must record the deselection that shaped it, in the database, in "
           f"the manifest, and in the command it offers; ok={env.get('ok')} "
           f"meta.exclude_paths={recorded.get('exclude_paths')!r} "
           f"manifest.exclude_paths={generation.get('exclude_paths')!r} "
           f"regenerate_command={regen[:160]!r}")


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
    # ALL OR NOTHING, kept as a standing assertion. A set that half-applies leaves the
    # target in a state nobody designed while reporting that it "partly worked".
    (t / "src" / "c.py").write_text("VALUE = 'c'\n", encoding="utf-8")
    bad = call(t, "patch", {"action": "apply", "apply": True, "patch": {"files": [
        {"path": "src/c.py",
         "hunks": [{"search_block": "VALUE = 'c'", "replace_block": "VALUE = 'C'"}]},
        {"path": "src/b.py",
         "hunks": [{"search_block": "NOT PRESENT", "replace_block": "X"}]}]}})
    record("2.5b a rejected file in the set leaves EVERY file untouched",
           bad.get("ok") is False
           and (t / "src" / "c.py").read_text(encoding="utf-8") == "VALUE = 'c'\n",
           f"partial application is worse than refusal; refused={bad.get('ok') is False} "
           f"c.py={(t / 'src' / 'c.py').read_text(encoding='utf-8').strip()!r} "
           f"problems={out(bad).get('problems')!r}")

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
    # THE INDEX ITSELF, not just the commit. `git status --porcelain` shows an unstaged
    # file as " M"/"??" and a staged one as "M "/"A " - so this proves the unapproved
    # change was never STAGED, which is the claim, rather than merely never committed.
    staged_now = git(repo, "diff", "--cached", "--name-only")
    record("4.2b the unapproved change was never staged in the index",
           "unapproved.txt" not in staged_now
           and any(ln.endswith("unapproved.txt") and not ln.startswith(("M ", "A "))
                   for ln in still_dirty.splitlines()),
           f"index after commit={staged_now.split()!r} porcelain={still_dirty.splitlines()!r}")
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
    # ADVANCE THE REMOTE behind our back, so a real pull has something to bring back.
    # Command text is not evidence; a commit that could only have arrived via fetch is.
    clone = repo.parent / "other"
    subprocess.run(["git", "clone", "-q", str(bare), str(clone)], check=False)
    git(clone, "config", "user.email", "other@local")
    git(clone, "config", "user.name", "other")
    (clone / "from_remote.txt").write_text("upstream\n", encoding="utf-8")
    git(clone, "add", ".")
    git(clone, "commit", "-qm", "upstream commit")
    git(clone, "push", "-q")

    (repo / "second.txt").write_text("two\n", encoding="utf-8")
    env = call(repo, "git", {"repo": str(repo), "action": "sync",
                             "message": "second change", "pull": True, "apply": True})
    record("4.6b the pull actually brought the remote commit down",
           (repo / "from_remote.txt").is_file(),
           "a file that exists only upstream must appear locally after sync(pull=true); "
           f"present={(repo / 'from_remote.txt').is_file()} "
           f"log={git(repo, 'log', '--oneline').splitlines()[:3]!r}")
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
    # REPEATED writes must not collide. A timestamp alone is not uniqueness: five writes
    # inside one second would all resolve to the same name, and "unique" would be a claim
    # rather than a property. This is the assertion the counter exists for.
    repeats = []
    for i in range(5):
        r = out(call(t, "write_file", {"path": "note.txt", "content": f"r{i}\n",
                                       "overwrite": False, "unique": True, "apply": True}))
        repeats.append(r.get("path"))
    record("6.4b repeated unique writes never resolve to the same path",
           len(set(repeats)) == 5 and all(repeats),
           f"a timestamp is not a uniqueness guarantee; paths="
           f"{[str(x).rsplit('/', 1)[-1] for x in repeats]}")

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
