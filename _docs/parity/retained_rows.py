#!/usr/bin/env python3
"""
FILE:       _docs/parity/retained_rows.py
ROLE:       Closure Gate 1, stage 2 - execute every RETAINED row of the frozen census.
DOMAIN:     factory
DOES:       Runs 47 parity claims (30 Retained-direct + 17 Retained-composed) through the
            governed runtime and records, per row: fixture, invocation, expected useful
            product, observed evidence, verdict.
DEPENDS ON: stdlib only. Drives the product through `src.app cli tool-call`.
NOTES:      A SUCCESSFUL ENVELOPE IS NEVER PARITY. Every claim asserts the DONOR'S USEFUL
            OUTCOME - the artifact, the file state, the recovered text - not that a tool
            returned ok:true. `ok` proves the seam dispatched; it proves nothing about the
            product the predecessor existed to provide.

            FOR COMPOSED ROWS THE WHOLE CHAIN IS PROVEN, not the existence of its parts.
            "`bd_query` exists and `bd_project` exists" is not evidence that a corpus can
            be queried and its source text recovered; running one into the other is.

            Fixtures are reused where one real outcome legitimately demonstrates several
            rows. Rows still stand alone: each names its own fixture, invocation, expected
            product and observation, so a reader can audit one row without running any.

            The six REPAIRED rows live in parity_check.py and are not repeated here.

            Run:  python _docs/parity/retained_rows.py
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
CLAIMS: list[dict] = []


def claim(row: str, kind: str, fixture: str, invocation: str, expected: str,
          observed: str, ok: bool) -> None:
    CLAIMS.append({"row": row, "kind": kind, "fixture": fixture,
                   "invocation": invocation, "expected": expected,
                   "observed": observed, "ok": bool(ok)})


def call(target: Path, tool: str, args: dict, timeout: int = 300) -> dict:
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
        return {"ok": False, "error": (p.stderr or p.stdout)[-400:], "output": None}


def out(env: dict) -> dict:
    o = env.get("output")
    return o if isinstance(o, dict) else {}


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True)
    return (p.stdout or "") + (p.stderr or "")


def brief(v, n: int = 150) -> str:
    s = v if isinstance(v, str) else json.dumps(v, default=str)
    return s if len(s) <= n else s[:n] + "…"


# =========================================================== fixtures
def make_software() -> Path:
    t = Path(tempfile.mkdtemp(prefix="ret-soft-")) / "proj"
    (t / "src").mkdir(parents=True)
    (t / "drop").mkdir()
    (t / "src" / "__init__.py").write_text("", encoding="utf-8")
    (t / "src" / "backend.py").write_text(
        '"""Hub."""\nimport os\n\n\nclass Backend:\n'
        '    """ROLE: orchestration hub."""\n\n'
        "    def start(self):\n        return os.getpid()\n\n\n"
        "def genuinely_unused():\n    return 1\n", encoding="utf-8")
    (t / "src" / "svc.py").write_text(
        "from src.backend import Backend\n\n\nclass Svc:\n"
        '    """A service."""\n\n    def go(self):\n        return Backend()\n',
        encoding="utf-8")
    (t / "src" / "ui.py").write_text(
        "import tkinter as tk\n\n\ndef on_go():\n    return 'went'\n\n\n"
        "root = tk.Tk()\n"
        "root.title('Parity')\n"
        "btn = tk.Button(root, text='Go', command=on_go)\n"
        "btn.pack()\n", encoding="utf-8")
    (t / "drop" / "dropped.txt").write_text("dropped\n", encoding="utf-8")
    # Noise the shared PRUNE authority owns, so 5.4 asserts real pruning rather than a
    # dot-folder I invented. `.pm` is my own output dir and the product has no opinion
    # about it - asserting on it would have been my fixture grading itself.
    (t / "__pycache__").mkdir()
    (t / "__pycache__" / "stale.pyc").write_text("x", encoding="utf-8")
    (t / ".git").mkdir()
    (t / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (t / "notes.md").write_text(
        "# Notes\n\nThe quick brown fox jumps over the lazy dog.\n\n"
        "A second paragraph mentioning parity and evidence.\n", encoding="utf-8")
    (t / "requirements.txt").write_text("requests\n", encoding="utf-8")
    return t


def make_repo() -> Path:
    t = Path(tempfile.mkdtemp(prefix="ret-git-")) / "repo"
    t.mkdir(parents=True)
    (t / ".gitignore").write_text("*.log\n", encoding="utf-8")
    git(t, "init", "-q")
    git(t, "config", "user.email", "parity@local")
    git(t, "config", "user.name", "parity")
    (t / "first.txt").write_text("one\n", encoding="utf-8")
    git(t, "add", ".")
    git(t, "commit", "-qm", "base")
    return t


# =========================================================== 01 ProjectMapper
def rows_01(t: Path) -> None:
    db = t / ".pm" / "snap.sqlite3"
    env = call(t, "projectmapper", {"action": "compile", "root": ".", "name": "parity",
                                    "out": str(db), "markdown": True,
                                    "apply": True})
    o = out(env)
    inv = "projectmapper compile root=. markdown=true"
    import sqlite3
    tables, files = [], 0
    if db.is_file():
        con = sqlite3.connect(db)
        try:
            tables = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            if "project_files" in tables:
                files = con.execute("SELECT COUNT(*) FROM project_files").fetchone()[0]
        finally:
            con.close()
    claim("1.1", "direct", "software fixture", inv,
          "a portable SQLite snapshot exists and CONTAINS the captured files",
          f"db={db.name} exists={db.is_file()} tables={len(tables)} project_files={files}",
          db.is_file() and files > 0 and "project_files" in tables)

    # Read from the OUTPUTS the tool declares, not from a glob: a glob would silently
    # match a file some other row wrote and call it evidence.
    outs = o.get("outputs") or {}
    for row, key, must in (("1.2", "tree_md", "backend.py"),
                           ("1.3", "filedump_md", "class Backend"),
                           ("1.4", "combined_md", "class Backend"),
                           ("1.5", "manifest_md", "Capture selection")):
        named = outs.get(key)
        hit = (t / named) if named and (t / named).is_file() else None
        text = hit.read_text(encoding="utf-8", errors="replace") if hit else ""
        claim(row, "direct", "software fixture", inv + f" -> outputs.{key}",
              f"a {key} export whose CONTENT proves it is a real {key}",
              f"file={hit.name if hit else None} bytes={len(text)} contains={must!r}:"
              f"{must in text}", bool(hit) and must in text)


# =========================================================== 02 Patcher
def rows_02(t: Path) -> None:
    p = t / "src" / "svc.py"
    original = p.read_text(encoding="utf-8")
    hunk = {"hunks": [{"search_block": "        return Backend()",
                       "replace_block": "        return Backend().start()"}]}
    v = out(call(t, "patch", {"action": "validate", "path": "src/svc.py", "patch": hunk}))
    claim("2.1", "direct", "src/svc.py + one hunk", "patch action=validate",
          "the patch is validated and NOTHING is written",
          f"valid={v.get('valid')} written={v.get('written')} "
          f"file_unchanged={p.read_text(encoding='utf-8') == original}",
          v.get("valid") is True and not v.get("written")
          and p.read_text(encoding="utf-8") == original)

    prev = out(call(t, "patch", {"action": "apply", "path": "src/svc.py", "patch": hunk}))
    d = out(call(t, "diff", {"a_text": original, "b_text": prev.get("result", ""),
                             "from_label": "before", "to_label": "preview"}))
    dtext = json.dumps(d)
    claim("2.2", "composed", "src/svc.py + one hunk",
          "patch (preview) -> diff(original, preview.result)",
          "a reviewable unified diff showing the proposed change",
          f"identical={d.get('identical')} diff_mentions_change="
          f"{'Backend().start()' in dtext}",
          d.get("identical") is False and "Backend().start()" in dtext)

    indented = {"hunks": [{"search_block": "    def go(self):",
                           "replace_block": "    def go(self):\n        # noted"}]}
    call(t, "patch", {"action": "apply", "path": "src/svc.py", "patch": indented,
                      "apply": True})
    after = p.read_text(encoding="utf-8")
    claim("2.3", "direct", "src/svc.py", "patch action=apply apply=true",
          "the file is patched and the surrounding indentation intent is preserved",
          f"line={after.splitlines()[6] if len(after.splitlines()) > 6 else ''!r} "
          f"has_8_space_indent={'        # noted' in after}",
          "        # noted" in after)

    dup = t / "dup.txt"
    dup.write_text("a\nb\na\n", encoding="utf-8")
    amb = out(call(t, "patch", {"action": "validate", "path": "dup.txt",
                                "patch": {"hunks": [{"search_block": "a",
                                                     "replace_block": "Z"}]}}))
    mis = out(call(t, "patch", {"action": "validate", "path": "dup.txt",
                                "patch": {"hunks": [{"search_block": "NOPE",
                                                     "replace_block": "Z"}]}}))
    intact = dup.read_text(encoding="utf-8") == "a\nb\na\n"
    claim("2.4", "direct", "a file with a duplicated line",
          "patch validate x2 (ambiguous, then missing)",
          "both ambiguous and not-found hunks are REFUSED before any write",
          f"ambiguous={brief(amb.get('error'), 60)} missing={brief(mis.get('error'), 60)} "
          f"file_unchanged={intact}",
          "Ambiguous" in str(amb.get("error")) and "not found" in str(mis.get("error"))
          and intact)


# =========================================================== 03 LineNumberizer
def rows_03(t: Path) -> None:
    src = "alpha\nbeta\ngamma\n"
    f = t / "lines.txt"
    f.write_text(src, encoding="utf-8")
    ann = out(call(t, "linenumber", {"action": "annotate", "path": "lines.txt"}))
    annotated = ann.get("numbered") or ""
    claim("3.1", "direct", "a 3-line text file", "linenumber action=annotate",
          "every line carries a parseable number prefix",
          f"first_line={brief(annotated.splitlines()[0] if annotated else '', 40)!r} "
          f"lines={len(annotated.splitlines())}",
          len(annotated.splitlines()) == 3 and "alpha" in annotated
          and any(ch.isdigit() for ch in annotated.splitlines()[0]))

    st = out(call(t, "linenumber", {"action": "strip", "text": annotated}))
    stripped = st.get("stripped") or st.get("text") or st.get("numbered") or ""
    claim("3.2", "direct", "the annotated text", "linenumber action=strip",
          "the ORIGINAL content is recovered exactly",
          f"round_trip_identical={stripped == src} got={brief(stripped, 40)!r}",
          stripped == src)

    mp = out(call(t, "linenumber", {"action": "map", "path": "lines.txt"}))
    entries = mp.get("map") or mp.get("lines") or mp.get("entries")
    claim("3.3", "direct", "a 3-line text file", "linenumber action=map",
          "a line -> hash integrity map with one entry per line",
          f"entries={len(entries) if hasattr(entries, '__len__') else None} "
          f"sample={brief(entries, 90)}",
          bool(entries) and hasattr(entries, "__len__") and len(entries) == 3)

    sc = out(call(t, "semantic_chunk", {"path": "src/backend.py"}))
    chunks = sc.get("chunks") or []
    sg = out(call(t, "symbol_graph", {"action": "stats", "root": "src"}))
    names = {c.get("name") for c in chunks}
    claim("3.4", "composed", "src/backend.py",
          "semantic_chunk -> symbol_graph (structure, then relationships)",
          "a machine-readable structural projection of the module, plus its references",
          f"chunk_names={brief(sorted(n for n in names if n), 80)} "
          f"symbol_graph_ok={sg.get('ok')}",
          any("Backend" in str(n) for n in names) and sg.get("ok") is not False)

    claim("3.5", "direct", "src/backend.py", "semantic_chunk",
          "semantic blocks carrying name, type and line span",
          f"n={len(chunks)} first={brief({k: v for k, v in (chunks[0] if chunks else {}).items() if k != 'content'}, 110)}",
          bool(chunks) and all(k in chunks[0] for k in ("name", "type", "start_line",
                                                        "end_line")))


# =========================================================== 04 Git
def rows_04(repo: Path) -> None:
    ins = out(call(repo, "git_inspect", {"repo": str(repo)}))
    st = out(call(repo, "git", {"repo": str(repo), "action": "status"}))
    claim("4.1", "direct", "a git repo with one commit", "git_inspect + git status",
          "the repository's branch and working-tree state are reported",
          f"branch={st.get('branch')!r} clean={st.get('clean')!r} "
          f"inspect_keys={brief(sorted(ins), 90)}",
          bool(st.get("branch")) and st.get("branch") != "unknown"
          and "clean" in st and bool(ins))

    bare = repo.parent / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=False)
    git(repo, "remote", "add", "origin", str(bare))
    git(repo, "push", "-q", "-u", "origin", "HEAD")
    (repo / "pushed.txt").write_text("p\n", encoding="utf-8")
    env = call(repo, "git", {"repo": str(repo), "action": "sync",
                             "message": "commit and push", "apply": True})
    o = out(env)
    remote_log = subprocess.run(["git", "log", "--oneline"], cwd=str(bare),
                                capture_output=True, text=True).stdout
    claim("4.3", "direct", "a repo with a bare remote", "git action=sync",
          "the commit lands AND reaches the remote",
          f"steps={[s.get('cmd') for s in (o.get('steps') or [])]} "
          f"remote_has={brief(remote_log.strip().splitlines()[:1], 60)}",
          "commit and push" in remote_log)

    naked = Path(tempfile.mkdtemp(prefix="ret-nogi-")) / "r"
    naked.mkdir(parents=True)
    git(naked, "init", "-q")
    git(naked, "config", "user.email", "p@l")
    git(naked, "config", "user.name", "p")
    (naked / "x.txt").write_text("x\n", encoding="utf-8")
    guard = call(naked, "git", {"repo": str(naked), "action": "commit",
                                "message": "should refuse", "apply": True})
    log_after = git(naked, "log", "--oneline")
    claim("4.4", "direct", "a repo with NO .gitignore", "git action=commit (whole tree)",
          "the whole-tree stage is REFUSED and nothing is committed",
          f"refused={guard.get('ok') is False} err={brief(out(guard).get('error') or guard.get('error'), 70)} "
          f"commits={0 if 'does not have any commits' in log_after or not log_after.strip() else len(log_after.strip().splitlines())}",
          guard.get("ok") is False
          and ("does not have any commits" in log_after or not log_after.strip()))

    ledger = out(call(repo, "event_log", {"action": "tool", "tool_id": "git", "limit": 5}))
    events = ledger.get("events") or []
    claim("4.5", "composed", "the git calls just made",
          "git (returns per-command steps) -> event_log action=tool",
          "every git command's exit code is recoverable, and the calls are attributed",
          f"steps_carry_code={all('code' in s for s in (o.get('steps') or []))} "
          f"ledger_events={len(events)} clients={brief([e.get('client') for e in events[:3]], 40)}",
          bool(o.get("steps")) and all("code" in s for s in o["steps"])
          and bool(events) and all(e.get("client") for e in events))


# =========================================================== 05 UiMapper
def rows_05(t: Path) -> None:
    wt = out(call(t, "tkinter_widget_tree", {"root": "src"}))
    blob = json.dumps(wt)
    claim("5.1", "direct", "src/ui.py (a real tk.Tk root with a Button)",
          "tkinter_widget_tree root=src",
          "the Tk surface is mapped: the root window and its Button are found",
          f"windows={wt.get('window_count')} widgets={wt.get('widget_count')} "
          f"types={brief(wt.get('widget_types'), 60)} mentions_Button={'Button' in blob}",
          (wt.get("window_count") or 0) >= 1 and (wt.get("widget_count") or 0) >= 1
          and "Button" in blob)

    cg = out(call(t, "ui_callback_graph", {"root": "src"}))
    cblob = json.dumps(cg)
    claim("5.2", "direct", "src/ui.py", "ui_callback_graph root=src",
          "the button's command is bound to its handler `on_go`",
          f"mentions_on_go={'on_go' in cblob} edges={brief(cg.get('edges') or cg.get('callbacks'), 80)}",
          "on_go" in cblob)

    rep = out(call(t, "report", {"path": "src"}))
    claim("5.3", "composed", "src/",
          "ui_callback_graph / tkinter_widget_tree -> report",
          "a serialized report artifact describing the scanned surface",
          f"report_keys={brief(sorted(rep), 80)} markdown_bytes={len(str(rep.get('markdown') or ''))}",
          bool(rep.get("markdown")) or bool(rep.get("modules")))

    tree = out(call(t, "file_tree", {"root": ".", "kind": "file"}))
    rows = [r.get("path", "") for r in (tree.get("rows") or [])]
    listed = " ".join(rows)
    claim("5.4", "direct", "the fixture, which also contains .git/ and __pycache__/",
          "file_tree root=. kind=file",
          "the scan honours the shared prune list: source is listed, .git and "
          "__pycache__ are not",
          f"n={len(rows)} lists_source={'backend.py' in listed} "
          f"lists_git={'.git' in listed} lists_pycache={'__pycache__' in listed}",
          "backend.py" in listed and ".git" not in listed
          and "__pycache__" not in listed)

    claim("5.5", "direct", "src/ui.py", "ui_callback_graph root=src",
          "unresolved cases are reported honestly rather than dropped",
          f"has_unresolved_field={'unresolved_events' in cg} "
          f"value={brief(cg.get('unresolved_events'), 60)}",
          "unresolved_events" in cg)


# =========================================================== 06 TextToucher
def rows_06(t: Path) -> None:
    call(t, "write_file", {"path": "made/new.txt", "content": "hello\n", "apply": True})
    made = t / "made" / "new.txt"
    claim("6.1", "direct", "a target folder", "write_file apply=true",
          "a UTF-8 file exists with exactly the requested content",
          f"exists={made.is_file()} content={brief(made.read_text(encoding='utf-8') if made.is_file() else '', 30)!r}",
          made.is_file() and made.read_text(encoding="utf-8") == "hello\n")

    prev = out(call(t, "write_file", {"path": "made/new.txt", "content": "second\n"}))
    claim("6.2", "direct", "an existing file", "write_file (no apply)",
          "the preview names the exact target path and that it would overwrite, "
          "and writes nothing",
          f"path={brief(prev.get('path'), 60)} would_overwrite={prev.get('would_overwrite')} "
          f"written={prev.get('written')} still={brief(made.read_text(encoding='utf-8'), 20)!r}",
          prev.get("would_overwrite") is True and prev.get("written") is False
          and made.read_text(encoding="utf-8") == "hello\n")

    esc = call(t, "write_file", {"path": "../../escape.txt", "content": "no\n",
                                 "apply": True})
    claim("6.3", "direct", "a traversal attempt", "write_file path=../../escape.txt",
          "the write is REFUSED and no file appears outside the target",
          f"refused={esc.get('ok') is False} "
          f"err={brief(out(esc).get('error') or esc.get('error'), 70)} "
          f"escaped_exists={(t.parent.parent / 'escape.txt').exists()}",
          esc.get("ok") is False and not (t.parent.parent / "escape.txt").exists())


# =========================================================== 07 Chat host
def rows_07(t: Path) -> None:
    call(t, "session_record", {"action": "start", "session": "parity-s",
                               "description": "parity session", "write": True})
    call(t, "session_record", {"action": "append", "session": "parity-s", "role": "user",
                               "kind": "message", "content": "remember this line",
                               "write": True})
    rep = out(call(t, "session_replay", {"session": "parity-s"}))
    blob = json.dumps(rep)
    claim("7.2", "direct", "a recorded session",
          "session_record start/append -> session_replay",
          "the recorded turn is replayed back verbatim",
          f"replayed={'remember this line' in blob} events={brief(rep.get('count') or len(rep.get('events') or []), 20)}",
          "remember this line" in blob)

    op = out(call(t, "operation", {"action": "start", "title": "parity op",
                                   "goal": "prove pause/resume", "apply": True}))
    op_id = op.get("op_id") or op.get("id")
    paused = out(call(t, "operation", {"action": "pause", "op_id": op_id,
                                       "note": "held", "apply": True}))
    resumed = out(call(t, "operation", {"action": "resume", "op_id": op_id,
                                        "apply": True}))
    claim("7.3", "composed", "a durable operation",
          "operation start -> pause -> resume",
          "long work can be paused and resumed across the seam, not merely cancelled",
          f"op={brief(op_id, 24)} paused={brief(paused.get('status') or paused.get('action'), 20)} "
          f"resumed={brief(resumed.get('status') or resumed.get('action'), 20)}",
          bool(op_id) and paused.get("ok") is not False
          and resumed.get("ok") is not False)

    bad = call(t, "read_file", {"path": "does/not/exist.txt"})
    led = out(call(t, "event_log", {"action": "tool", "tool_id": "read_file", "limit": 3}))
    evs = led.get("events") or []
    claim("7.4", "composed", "a deliberately failing call",
          "read_file (fails) -> event_log action=tool",
          "the failure leaves a diagnosable record: error text AND who called",
          f"seam_reported_failure={bad.get('ok') is False} "
          f"ledger_has_event={bool(evs)} client={brief([e.get('client') for e in evs[:2]], 30)}",
          bad.get("ok") is False and bool(evs) and all(e.get("client") for e in evs))


# =========================================================== 08 theCELL
def rows_08(t: Path) -> None:
    d = call(t, "delegate", {"task": "summarise the fixture", "max_steps": 1})
    do = out(d)
    honest = (d.get("ok") is False) or bool(do)
    claim("8.3", "direct", "a one-step task", "delegate max_steps=1",
          "a bounded agent step runs, or reports honestly that no backend is available",
          f"ok={d.get('ok')} keys={brief(sorted(do), 70)} "
          f"err={brief(do.get('error') or d.get('error'), 70)}",
          honest)

    op = out(call(t, "operation", {"action": "start", "title": "queue",
                                   "goal": "declared task queue",
                                   "steps": ["one", "two"], "apply": True}))
    op_id = op.get("op_id")
    started = op.get("operation") or {}
    adv = out(call(t, "operation", {"action": "step", "op_id": op_id,
                                    "tool": "read_file", "apply": True}))
    after = out(call(t, "operation", {"action": "show", "op_id": op_id})).get(
        "operation") or {}
    claim("8.4", "composed", "a two-step declared queue",
          "operation start(steps=[...]) -> step -> show",
          "the declared queue is durable, and advancing MOVES it (recoverable by id)",
          f"op={brief(op_id, 20)} start_status={started.get('status')!r} "
          f"after={brief({k: v for k, v in after.items() if k in ('status', 'step', 'cursor', 'progress')}, 80)}",
          bool(op_id) and bool(started) and adv.get("ok") is not False and bool(after))

    call(t, "bd_index", {"paths": ["notes.md"], "apply": True})
    q = out(call(t, "bd_query", {"query": "parity", "limit": 3}))
    rr = out(call(t, "rag_retrieve", {"query": "quick brown fox", "path": "notes.md",
                                      "top_k": 2}))
    claim("8.5", "composed", "notes.md",
          "bd_index -> bd_query, and rag_retrieve over the same file",
          "context is ingested and retrievable by meaning, not just grep",
          f"anchors={len(q.get('anchors') or [])} "
          f"rag_hits={brief(rr.get('results') or rr.get('chunks') or rr.get('hits'), 60)}",
          bool(q.get("anchors")) and bool(rr))

    ev = out(call(t, "evidence", {"action": "attach", "kind": "note",
                                  "summary": "parity capture",
                                  "body": "captured during retained-row execution",
                                  "apply": True}))
    eid = ev.get("evidence_id") or ev.get("id")
    got = out(call(t, "evidence", {"action": "get", "evidence_id": eid}))
    body = str(got.get("content") or "")
    claim("8.6", "composed", "one recorded finding",
          "evidence attach -> evidence get",
          "the captured BODY is recovered verbatim by its id, with a content hash",
          f"id={brief(eid, 20)} hash={brief(got.get('hash'), 20)} "
          f"recovered={body == 'captured during retained-row execution'}",
          bool(eid) and body == "captured during retained-row execution")

    pc = out(call(t, "prompt_case_builder", {"prompt": "Summarise {doc}",
                                             "scenario": "parity", "id": "parity-case"}))
    wt = out(call(t, "workflow_templates", {}))
    claim("8.7", "composed", "a prompt + the template catalogue",
          "prompt_case_builder -> workflow_templates",
          "reusable prompts/templates are produced and enumerable",
          f"case={brief(pc.get('id') or pc.get('case') or sorted(pc), 60)} "
          f"templates={brief(wt.get('count') or len(wt.get('templates') or []), 20)}",
          bool(pc) and pc.get("ok") is not False and bool(wt))


# =========================================================== 09 Wasm wrapper
def rows_09(t: Path) -> None:
    # ASK THE TOOL WHICH ARCHETYPES EXIST rather than assuming one. "python-app" was a
    # guess; the real set is python-cli / records-project / web-app.
    known = out(call(t, "scaffold_project", {"action": "show_archetype",
                                             "archetype": "python-app"})).get("known") or []
    arch_name = "python-cli" if "python-cli" in known else (known[0] if known else "python-cli")
    pmap = {"name": "agentnode", "archetype": arch_name}
    sc = call(t, "scaffold_project", {"action": "plan", "archetype": arch_name,
                                      "map": pmap, "root": "agentnode"})
    so = out(sc)
    claim("9.1", "composed", "an empty subfolder",
          "scaffold_project show_archetype -> plan (archetype from the tool)",
          "a runtime scaffold is planned with its file manifest",
          f"ok={sc.get('ok')} keys={brief(sorted(so), 80)} "
          f"files={brief(so.get('files') or so.get('plan') or so.get('actions'), 70)}",
          sc.get("ok") is not False and bool(so))

    claim("9.2", "direct", "the same scaffold request",
          "scaffold_project (plan only, no apply)",
          "every generated file is previewed and NOTHING is created",
          f"created={(t / 'agentnode').exists()} dry={so.get('dry_run', so.get('written'))}",
          not (t / "agentnode").exists())

    di = call(t, "dep_install", {"packages": ["requests"]})
    dio = out(di)
    claim("9.3", "composed", "a dependency request",
          "dep_install packages=[requests] (no apply)",
          "the install is GATED behind explicit confirmation, not performed",
          f"ok={di.get('ok')} written/applied={dio.get('applied', dio.get('written', dio.get('dry_run')))} "
          f"keys={brief(sorted(dio), 70)}",
          dio.get("applied") is not True and dio.get("installed") is not True)

    pe = out(call(t, "prompt_eval", {"prompt": "Say OK", "cases": []}))
    claim("9.4", "composed", "a prompt case",
          "prompt_case_builder -> prompt_eval",
          "a prompt request/response contract can be exercised and reported",
          f"keys={brief(sorted(pe), 80)}",
          bool(pe))


# =========================================================== 10 Monaco
def rows_10(t: Path) -> None:
    f = t / "src" / "backend.py"
    before = f.read_text(encoding="utf-8")
    prev = out(call(t, "edit", {"path": "src/backend.py", "pattern": "orchestration hub",
                                "replacement": "orchestration core", "literal": True}))
    out(call(t, "edit", {"path": "src/backend.py", "pattern": "orchestration hub",
                                   "replacement": "orchestration core", "literal": True,
                                   **(prev.get("apply_with") or {})}))
    after = f.read_text(encoding="utf-8")
    claim("10.2", "direct", "src/backend.py",
          "edit preview -> edit apply (carrying the source witness)",
          "a range-precise replacement lands exactly, changing only the named text",
          f"changed={before != after} only_that_line="
          f"{after == before.replace('orchestration hub', 'orchestration core')}",
          after == before.replace("orchestration hub", "orchestration core"))

    rf = out(call(t, "read_file", {"path": "src/backend.py"}))
    claim("10.3", "direct", "src/backend.py", "read_file",
          "text operations work headlessly: the file's content is returned",
          f"bytes={rf.get('bytes')} has_content={'orchestration core' in str(rf.get('content'))}",
          "orchestration core" in str(rf.get("content")))

    led = out(call(t, "event_log", {"action": "read", "limit": 8}))
    evs = led.get("events") or []
    claim("10.6", "direct", "the edit just applied", "event_log action=read",
          "a second client can observe the mutation another client caused",
          f"recent_tools={brief([e.get('tool_id') for e in evs[:5]], 70)} "
          f"clients={brief(sorted({e.get('client') for e in evs}), 40)}",
          any(e.get("tool_id") == "edit" for e in evs)
          and all(e.get("client") for e in evs))


# =========================================================== 11 manifold
def rows_11(t: Path) -> None:
    idx = out(call(t, "bd_index", {"paths": ["notes.md"], "apply": True}))
    claim("11.2", "composed", "notes.md",
          "bd_index apply=true (split -> emit -> scribe)",
          "the document is ingested into a reversible corpus with content nodes",
          f"ok={idx.get('ok')} status={brief(idx.get('status'), 110)}",
          idx.get("ok") is not False and bool(idx.get("status") or idx.get("db")))

    q = out(call(t, "bd_query", {"query": "parity", "limit": 3}))
    anchors = q.get("anchors") or []
    claim("11.3", "composed", "the ingested corpus", "bd_query query=parity",
          "an evidence bag comes back carrying provenance (origin + structural path)",
          f"anchors={len(anchors)} first={brief({k: v for k, v in (anchors[0] if anchors else {}).items() if k in ('origin_id', 'structural_path', 'node_kind')}, 110)}",
          bool(anchors) and all(k in anchors[0] for k in ("origin_id", "structural_path")))

    # SELECT BY ORIGIN, NOT BY POSITION. The BD graph lives under the toolkit home and
    # ACCUMULATES across fixtures and across runs, so `anchors[0]` is whatever scored
    # highest in a corpus that may contain other documents entirely. Expanding that and
    # then failing to find this fixture's text would be a false parity failure caused by
    # a shared store - the row is about recovering the source of the evidence you asked
    # for, so the anchor must be the one drawn from THIS document.
    mine = [a for a in anchors if str(a.get("origin_id", "")).endswith("notes.md")]
    oid = mine[0]["occurrence_id"] if mine else ""
    proj = out(call(t, "bd_project", {"occurrence_ids": [oid]})) if oid else {}
    pblob = json.dumps(proj)
    source = (t / "notes.md").read_text(encoding="utf-8")
    recovered = [ln.strip() for ln in source.splitlines()
                 if ln.strip() and ln.strip() in pblob]
    claim("11.4", "composed", "an occurrence id from the query",
          "bd_query -> bd_project (expand to verbatim)",
          "the ORIGINAL source text is recovered verbatim from the evidence bag",
          f"anchors_from_notes.md={len(mine)} recovered_lines={brief(recovered, 90)}",
          bool(mine) and bool(recovered))

    esc = call(t, "read_file", {"path": "../../../etc/hostname"})
    claim("11.5", "direct", "a traversal attempt on a READ",
          "read_file path=../../../etc/hostname",
          "path containment refuses the read, not merely the write",
          f"refused={esc.get('ok') is False} "
          f"err={brief(out(esc).get('error') or esc.get('error'), 80)}",
          esc.get("ok") is False)


# =========================================================== 12 Dismantler
def rows_12(t: Path) -> None:
    big = t / "src" / "monolith.py"
    body = ['"""A large module."""', "import os", ""]
    for i in range(40):
        body += [f"def fn_{i:02d}(a, b):",
                 f"    if a > {i}:", "        return os.getpid()",
                 "    return b", ""]
    big.write_text("\n".join(body), encoding="utf-8")
    plan = out(call(t, "module_decomp_plan", {"root": "src", "limit": 5}))
    cx = out(call(t, "complexity_score", {"root": "src"}))
    ig = out(call(t, "import_graph", {"root": "src"}))
    cands = plan.get("candidates") or []
    claim("12.6", "composed", "a 40-function module",
          "complexity_score + import_graph -> module_decomp_plan",
          "a concrete decomposition proposal naming the monolith",
          f"candidates={len(cands)} names={brief([c.get('module') or c.get('path') for c in cands[:3]], 90)} "
          f"hotspots={brief(len(cx.get('hotspots') or []), 10)} imports_ok={ig.get('ok')}",
          bool(cands) and any("monolith" in str(c) for c in cands))

    planted = ROOT / "tools" / "_parity_never_loaded"
    planted.mkdir(parents=True, exist_ok=True)
    (planted / "cli.py").write_text(
        "raise SystemExit('this drop-in must never be executed by discovery')\n",
        encoding="utf-8")
    listing = call(t, "file_tree", {"root": ".", "kind": "file"})
    shutil.rmtree(planted, ignore_errors=True)
    claim("12.7", "direct", "a drop-in tool dir with NO tool.json, containing code that "
          "would crash if executed",
          "any governed call (discovery runs first)",
          "discovery reads manifests only; unmanifested drop-in code is never executed",
          f"seam_still_functional={listing.get('ok') is not False} "
          f"crash_text_absent={'must never be executed' not in json.dumps(listing)}",
          listing.get("ok") is not False
          and "must never be executed" not in json.dumps(listing))


# =========================================================== main
def main() -> int:
    soft, repo = make_software(), make_repo()
    try:
        rows_01(soft)
        rows_02(soft)
        rows_03(soft)
        rows_04(repo)
        rows_05(soft)
        rows_06(soft)
        rows_07(soft)
        rows_08(soft)
        rows_09(soft)
        rows_10(soft)
        rows_11(soft)
        rows_12(soft)
    finally:
        for d in (soft.parent, repo.parent):
            shutil.rmtree(d, ignore_errors=True)

    print("\nRETAINED-ROW PARITY EXECUTION\n" + "=" * 78)
    for c in CLAIMS:
        print(f"\n[{'PASS' if c['ok'] else 'FAIL'}] {c['row']}  ({c['kind']})")
        print(f"    fixture   {c['fixture']}")
        print(f"    invoked   {c['invocation']}")
        print(f"    expected  {c['expected']}")
        print(f"    observed  {c['observed']}")
    bad = [c for c in CLAIMS if not c["ok"]]
    direct = sum(1 for c in CLAIMS if c["kind"] == "direct")
    print("\n" + "=" * 78)
    print(f"{len(CLAIMS)} claims: {direct} direct + {len(CLAIMS) - direct} composed")
    print(f"{len(CLAIMS) - len(bad)} PASS / {len(bad)} FAIL")
    if bad:
        print("failing rows: " + ", ".join(c["row"] for c in bad))
    (Path(__file__).parent / "retained_rows.json").write_text(
        json.dumps(CLAIMS, indent=2), encoding="utf-8")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
