"""
FILE:       tools/git/cli.py
ROLE:       Git workflow tool  -  status, and the add -> commit -> push quick-push flow.
DOMAIN:     tool
DOES:       action=status: branch + porcelain status. action=commit: `add .` + commit.
            action=sync: commit then push. Validates the target is a repo; gates `add .`
            behind a .gitignore-present check (override with allow_no_gitignore).
DEPENDS ON: tools._toolkit, (stdlib) subprocess, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
NOTES:      Quick-push verbs only (init/status/commit/sync). Read-only inspection
            verbs live in tools/git_inspect.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from tools._toolkit import tool_main


def _git(repo: Path, args: list[str]) -> tuple[int, str, str]:
    try:
        r = subprocess.run(["git"] + args, cwd=str(repo), capture_output=True,
                           text=True, encoding="utf-8", timeout=60)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except FileNotFoundError:
        return 1, "", "git not found on PATH"
    except subprocess.TimeoutExpired:
        return 1, "", "git command timed out"


def _is_repo(repo: Path) -> bool:
    return (repo / ".git").is_dir()


def _branch(repo: Path) -> str:
    _, out, _ = _git(repo, ["branch", "--show-current"])
    return out or "unknown"


def _step(repo: Path, args: list[str]) -> dict:
    code, out, err = _git(repo, args)
    return {"cmd": "git " + " ".join(args), "code": code, "out": out, "err": err}


@tool_main
def run(args: dict) -> dict:
    repo = Path(args.get("repo") or ".").resolve()
    action = str(args.get("action", "status")).lower()

    if action == "init":
        # Initialize a repo (idempotent). Runs BEFORE the is-repo guard  -  it's the one action
        # whose whole point is a non-repo. Enables the guarded patch/apply/verify pipeline.
        if not repo.is_dir():
            return {"ok": False, "error": f"not a directory: {repo}"}
        if _is_repo(repo):
            return {"ok": True, "tool": "git", "action": "init", "already": True,
                    "repo": str(repo).replace("\\", "/"), "branch": _branch(repo)}
        code, out, err = _git(repo, ["init"])
        if code != 0:
            return {"ok": False, "error": f"git init failed: {err or out}"}
        return {"ok": True, "tool": "git", "action": "init", "already": False,
                "repo": str(repo).replace("\\", "/"), "branch": _branch(repo)}

    if not _is_repo(repo):
        return {"ok": False, "error": f"not a git repository: {repo}"}

    if action == "status":
        _, out, _ = _git(repo, ["status", "--porcelain"])
        return {
            "tool": "git", "action": "status",
            "repo": str(repo).replace("\\", "/"),
            "branch": _branch(repo),
            "clean": not out,
            "status": out.splitlines(),
        }

    if action in ("commit", "sync"):
        msg = str(args.get("message", "")).strip()
        if not msg:
            return {"ok": False, "error": "'message' is required for commit/sync"}
        if not (repo / ".gitignore").is_file() and not args.get("allow_no_gitignore"):
            return {"ok": False, "error": "no .gitignore present; refusing 'git add .' "
                                          "(set allow_no_gitignore:true to override)"}

        steps = [_step(repo, ["add", "."])]
        commit = _step(repo, ["commit", "-m", msg])
        steps.append(commit)
        committed = commit["code"] == 0 or "nothing to commit" in (commit["out"] + commit["err"]).lower()
        if not committed:
            return {"ok": False, "action": action, "branch": _branch(repo),
                    "steps": steps, "error": "commit failed"}

        if action == "sync":
            push = _step(repo, ["push"])
            steps.append(push)
            if push["code"] != 0:
                return {"ok": False, "action": action, "branch": _branch(repo),
                        "steps": steps, "error": "push failed"}

        return {
            "tool": "git", "action": action,
            "repo": str(repo).replace("\\", "/"),
            "branch": _branch(repo), "steps": steps,
        }

    return {"ok": False, "error": f"unknown action {action!r}; use init|status|commit|sync"}
