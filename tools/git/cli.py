"""
FILE:       tools/git/cli.py
ROLE:       Git workflow tool  -  status, and the add -> commit -> push quick-push flow.
DOMAIN:     tool
DOES:       action=status: branch + porcelain status. action=branch: list, or switch/create
            with the dirty state reported. action=commit: stage an EXPLICIT `paths` set (or
            `add .` when none is given) then commit. action=sync: commit, optional
            pull --rebase, then push. Gates the whole-tree `add .` behind a
            .gitignore-present check (override with allow_no_gitignore).
DEPENDS ON: tools._toolkit, (stdlib) subprocess, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
NOTES:      Quick-push verbs only (init/status/branch/commit/sync). Read-only inspection
            verbs live in tools/git_inspect. `paths` and `pull` close parity rows 4.2 and
            4.6; both are additive - omit them and behaviour is exactly what it was.
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

    if action == "branch":
        # PARITY ROW 4.7. The donor's product is branch management WITH THE DIRTY STATE
        # VISIBLE - switching away from uncommitted work silently is how it gets lost.
        # The state is REPORTED rather than used to refuse: git itself already refuses a
        # switch that would destroy work, and refusing the ones git permits would make
        # this tool less capable than the thing it wraps. Reporting is the donor's
        # requirement; forbidding is not.
        name = str(args.get("branch", "")).strip()
        _, porcelain, _ = _git(repo, ["status", "--porcelain"])
        state = {"tool": "git", "action": "branch", "repo": str(repo).replace("\\", "/"),
                 "clean": not porcelain, "dirty_paths": porcelain.splitlines()}
        if not name:
            _, listing, _ = _git(repo, ["branch", "--format=%(refname:short)"])
            return {**state, "branch": _branch(repo), "branches": listing.splitlines()}
        steps = []
        if args.get("create"):
            steps.append(_step(repo, ["checkout", "-b", name]))
        else:
            steps.append(_step(repo, ["checkout", name]))
        if steps[-1]["code"] != 0:
            return {**state, "ok": False, "branch": _branch(repo), "steps": steps,
                    "error": f"branch switch failed: {steps[-1]['err'] or steps[-1]['out']}"}
        return {**state, "branch": _branch(repo), "steps": steps}

    if action in ("commit", "sync"):
        msg = str(args.get("message", "")).strip()
        if not msg:
            return {"ok": False, "error": "'message' is required for commit/sync"}

        # PARITY ROW 4.2. An explicit approved working set is staged INSTEAD OF `add .`.
        # The donor contract is "stage and commit only an explicit user-approved working
        # set", and `add .` is the opposite product: it commits whatever happens to be in
        # the tree, including work the caller never looked at. The whole-tree path is
        # unchanged when no paths are given, so existing callers are unaffected.
        paths = args.get("paths")
        if paths:
            if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
                return {"ok": False, "error": "'paths' must be a list of strings"}
            missing = [p for p in paths if not (repo / p).exists()]
            if missing:
                # Staging a path that is not there would silently commit LESS than was
                # approved, which is the same class of defect as committing more.
                return {"ok": False, "error": f"approved paths do not exist: {missing}"}
            steps = [_step(repo, ["add", "--", *paths])]
        else:
            # `.gitignore` gates the WHOLE-TREE path only. An explicit set is already the
            # caller naming what they reviewed, so the guard that exists to stop `add .`
            # sweeping junk has nothing to protect against here.
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
            # PARITY ROW 4.6. Pull BEFORE push, so a push cannot clobber work that landed
            # upstream since the last fetch. Opt-in rather than default: a pull can produce
            # a merge or a conflict, and silently changing what `sync` does to every
            # existing caller would be a behaviour change smuggled in under a parity fix.
            # The ORDER is the product here - a pull after a push proves nothing.
            if args.get("pull"):
                # `--rebase`, NOT `--ff-only`. This shipped as --ff-only and was safe but
                # USELESS in the only flow that reaches it: sync commits first, so any
                # remote advance is a divergence, so the pull always refused and the push
                # never happened. "Pull before push" that can never integrate anything is
                # a ceremony, not a product - the donor's outcome is that the push
                # SUCCEEDS without clobbering upstream work.
                #
                # Rebase replays the local commits on top of the remote head: no merge
                # commit, and the commits being rewritten are by construction the ones
                # that have not been pushed yet.
                #
                # Found by a parity assertion that advanced the remote from a second clone
                # and demanded the upstream file appear locally. Reading the step list
                # would never have shown it: the verbs were add, commit, pull - and the
                # pull had refused.
                pull = _step(repo, ["pull", "--rebase"])
                steps.append(pull)
                if pull["code"] != 0:
                    # A failed rebase leaves the repo mid-rebase, which is a worse state
                    # than the one we started in. Put it back before reporting.
                    steps.append(_step(repo, ["rebase", "--abort"]))
                    return {"ok": False, "action": action, "branch": _branch(repo),
                            "steps": steps,
                            "error": "pull --rebase failed and was aborted; refusing to "
                                     "push over a remote we could not integrate: "
                                     + (pull["err"] or pull["out"])}
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

    return {"ok": False, "error": f"unknown action {action!r}; use "
            "init|status|branch|commit|sync"}
