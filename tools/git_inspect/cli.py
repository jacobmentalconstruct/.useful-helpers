"""
FILE:       tools/git_inspect/cli.py
ROLE:       Read-only git inspection  -  the verbs an agent needs to REASON about a repo/commit.
DOMAIN:     tool
DOES:       action = status (porcelain) | branches | log (capped) | ls-files | diff
            (name-status or unified, path-scoped) | grep | check-ignore (paths). Never
            mutates. Separate from the Apply-authority `git` tool so an Observe ceiling
            still permits inspection.
DEPENDS ON: tools._toolkit, (stdlib) subprocess, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Observe authority)
            grep/check-ignore/log/diff through the governed seam, not around it)
NOTES:      Roots contract: repo defaults to the WORK TARGET (cwd  -  the seam runs us there).
            All output is size/count-capped so results stay seam-friendly.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from tools._toolkit import tool_main

_CAP_LINES = 500
_CAP_CHARS = 60_000


def _git(repo: Path, argv: list) -> tuple:
    try:
        r = subprocess.run(["git"] + argv, cwd=str(repo), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except FileNotFoundError:
        return 1, "", "git not found on PATH"
    except subprocess.TimeoutExpired:
        return 1, "", "git command timed out"


def _lines(out: str) -> dict:
    lines = out.splitlines()
    return {"lines": lines[:_CAP_LINES], "count": len(lines),
            "truncated": len(lines) > _CAP_LINES}


@tool_main
def run(args: dict) -> dict:
    repo = Path(str(args.get("repo") or ".")).resolve()
    action = str(args.get("action", "status")).lower()
    code, inside, err = _git(repo, ["rev-parse", "--is-inside-work-tree"])
    if code != 0 or inside.strip().lower() != "true":
        return {"ok": False, "error": f"not a git repository: {repo}"}
    base = {"tool": "git_inspect", "action": action, "repo": repo.as_posix()}

    if action == "status":
        code, out, err = _git(repo, ["status", "--porcelain"])
        b_code, branch, _ = _git(repo, ["branch", "--show-current"])
        return {**base, "branch": branch or "unknown", "clean": not out, **_lines(out)}

    if action == "branches":
        code, out, err = _git(repo, ["branch", "-a", "--no-color"])
        return {**base, **_lines(out)} if code == 0 else {"ok": False, "error": err or out}

    if action == "log":
        n = min(int(args.get("n", 20)), 200)
        fmt = "%h|%an|%ad|%s"
        argv = ["log", f"-{n}", f"--pretty=format:{fmt}", "--date=short"]
        if args.get("path"):
            argv += ["--", str(args["path"])]
        code, out, err = _git(repo, argv)
        if code != 0:
            return {"ok": False, "error": err or out}
        entries = [dict(zip(("hash", "author", "date", "subject"), ln.split("|", 3)))
                   for ln in out.splitlines() if ln]
        return {**base, "count": len(entries), "entries": entries}

    if action == "ls-files":
        argv = ["ls-files"]
        if args.get("path"):
            argv += ["--", str(args["path"])]
        code, out, err = _git(repo, argv)
        return {**base, **_lines(out)} if code == 0 else {"ok": False, "error": err or out}

    if action == "diff":
        argv = ["diff", "--no-color"]
        if args.get("cached"):
            argv.append("--cached")
        argv.append("--stat" if str(args.get("format", "stat")) == "stat" else "-U3")
        if args.get("ref"):
            argv.insert(1, str(args["ref"]))
        if args.get("path"):
            argv += ["--", str(args["path"])]
        code, out, err = _git(repo, argv)
        if code != 0:
            return {"ok": False, "error": err or out}
        return {**base, "diff": out[:_CAP_CHARS], "truncated": len(out) > _CAP_CHARS}

    if action == "grep":
        pattern = str(args.get("pattern") or "").strip()
        if not pattern:
            return {"ok": False, "error": "grep needs 'pattern'"}
        argv = ["grep", "-n", "--no-color", "-e", pattern]
        if args.get("cached"):
            argv.insert(1, "--cached")
        if args.get("path"):
            argv += ["--", str(args["path"])]
        code, out, err = _git(repo, argv)
        if code > 1:  # 1 = no matches (fine); >1 = real error
            return {"ok": False, "error": err or out}
        return {**base, "pattern": pattern, **_lines(out)}

    if action == "check-ignore":
        paths = args.get("paths") or ([args["path"]] if args.get("path") else [])
        if not paths:
            return {"ok": False, "error": "check-ignore needs 'paths' (list) or 'path'"}
        results = {}
        for p in [str(x) for x in paths][:200]:
            code, out, _ = _git(repo, ["check-ignore", "-q", "--", p])
            results[p] = (code == 0)  # True = ignored
        return {**base, "ignored": results}

    return {"ok": False, "error": f"unknown action {action!r}; use "
            "status|branches|log|ls-files|diff|grep|check-ignore"}
