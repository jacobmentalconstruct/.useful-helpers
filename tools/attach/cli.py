"""
FILE:       tools/attach/cli.py
ROLE:       THE front door  -  one verb that re-engages an already-mapped target or maps a new one.
DOMAIN:     tool
DOES:       Resolves the target (default: the work target). If a workbench profile + map already
            exist, RE-ENGAGES: loads them, re-probes a cheap signature to report staleness, and
            hands back the orientation. Otherwise MAPS: probes the target, scores it against every
            cartridge in config/cartridges/, mounts the winner's tools, writes the profile + map,
            and hands back the same orientation. Either way the caller gets one PROJECT_MAP and an
            ordered `next` workflow. Pure Observe on the target; writes only into the toolkit's state root.
DEPENDS ON: tools._toolkit, (stdlib) json, os, time, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json; reads
            config/cartridges/*.json; writes <state_root>/workbench/{profile,map}.json
STATUS:     SKELETON
NOTES:      Structural only  -  it maps SHAPE, not MEANING. It runs no model and builds no
            embeddings, so `map.limits` states plainly what it does not know rather than
            implying otherwise. See _design/CHARTER.md sec 3 (Layer 4) and sec 4.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from tools import awareness_shared, summarize_shared
from tools._toolkit import instance_uuid, is_instance_path, output_root, project_root, state_root, suite_home, tool_main

PRUNE = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build", ".idea", ".vscode",
    "_artifacts", "_exports", "site-packages", ".tox", ".next", "target",
}
MAX_FILES = 20000
MARKER_DEPTH = 2          # how deep a marker file still counts (monorepos nest theirs)
MARKER_NESTED_FACTOR = 0.5  # a marker below the root is suggestive, not decisive
SHARE_SCALE = 10.0        # extension share (0..1) -> comparable magnitude to marker weights
MIN_CONFIDENT_SCORE = 1.0   # below this, admit we do not know and fall back to `generic`
MIN_SUBSYSTEM_FILES = 5     # below this, a subsystem is too small to classify honestly


def _workbench() -> Path:
    """The workbench is durable memory, not exhaust: it is what makes RE-ENGAGE possible
    across sessions. It belongs in the state root, and an update must preserve it."""
    return state_root() / "workbench"


def _self_paths() -> set[Path]:
    """Everything the INSTRUMENT itself writes.

    A sidecar normally sits inside the target, so `toolkit_home_names()` prunes it by name on
    the way past. That prune cannot fire when the target IS the toolkit home (self-attach, or
    standalone use)  -  we start inside it rather than descending into it. Without this, `attach`
    counts the map it just wrote as part of the target and reports the target stale the instant
    it finishes mapping it: the instrument observing its own exhaust.

    The governance event log is the sharp edge: EVERY governed call writes it, so without
    excluding it a self-attached target is stale one millisecond after being mapped, forever.

    This used to enumerate six hardcoded locations because the toolkit had no declared state
    root. It now asks the roots contract instead: state, output, logs, and the derived registry.
    A new store added under state_root() is excluded automatically  -  the list cannot rot.
    """
    home = suite_home()
    return {
        state_root(),
        output_root(),
        home / "logs",
        home / "_exports",
        home / "config" / "registry.json",
    }


def _cartridges(home: Path) -> list[dict]:
    out = []
    for p in sorted((home / "config" / "cartridges").glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            raise ValueError(f"unreadable cartridge {p.name}: {exc}") from exc
    if not out:
        raise ValueError("no cartridges found in config/cartridges/")
    return out


def _probe(target: Path) -> dict:
    """Walk the target once. Returns the raw facts every later step reads.

    Never counts the instrument's own output (see _self_paths), so the map stays a description
    of the target rather than of the toolkit sitting on it.
    """
    skip = set(PRUNE)
    mine = _self_paths()
    ext_counts: dict[str, int] = {}
    top_dirs: dict[str, int] = {}
    root_files: set[str] = set()
    shallow: dict[str, int] = {}  # filename -> shallowest depth seen (0 = target root)
    rel_paths: list[str] = []
    # Per-subsystem tallies. A target is often not one thing: a monorepo's sub-apps each want
    # their own workbench. Collected on the same single walk  -  subsystems are scored with the
    # exact machinery as the whole, just over a narrower slice.
    sub_ext: dict[str, dict[str, int]] = {}
    sub_shallow: dict[str, dict[str, int]] = {}
    sub_files: dict[str, int] = {}
    n_files = n_dirs = 0
    newest = 0.0
    truncated = False

    for current, dir_names, file_names in os.walk(target):
        here = Path(current)
        # `not d.startswith(".git")` used to sit here. It was written for `.git` - which
        # PRUNE already contains, so it added nothing there - and it silently swallowed
        # `.github`, `.gitlab` and every other sibling sharing the prefix. CI
        # configuration is exactly what a map of a target should see, and it made
        # workflow files invisible to `command_profile` too. Removed, not narrowed: the
        # named PRUNE set is the one authority on what is skipped, and a prefix test
        # beside it is a second, weaker rule that nobody declared. Journal 0032.
        dir_names[:] = sorted(
            d for d in dir_names
            if d not in skip and (here / d) not in mine
               and not is_instance_path(here / d)
        )
        rel_dir = here.relative_to(target)
        bucket = rel_dir.parts[0] if rel_dir.parts else ""
        n_dirs += len(dir_names)

        for name in file_names:
            if n_files >= MAX_FILES:
                truncated = True
                break
            if (here / name) in mine:
                continue
            n_files += 1
            ext = Path(name).suffix.lower()
            if ext:
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
            depth = len(rel_dir.parts)
            if bucket:
                top_dirs[bucket] = top_dirs.get(bucket, 0) + 1
                sub_files[bucket] = sub_files.get(bucket, 0) + 1
                if ext:
                    se = sub_ext.setdefault(bucket, {})
                    se[ext] = se.get(ext, 0) + 1
                # Depth is measured from the SUBSYSTEM's own root, so `_app/requirements.txt`
                # is a depth-0 marker for `_app` (full weight) while remaining depth-1  -
                # merely suggestive  -  for the target as a whole.
                sub_depth = depth - 1
                ss = sub_shallow.setdefault(bucket, {})
                if sub_depth <= MARKER_DEPTH and (name not in ss or sub_depth < ss[name]):
                    ss[name] = sub_depth
            else:
                root_files.add(name)
            if depth <= MARKER_DEPTH and (name not in shallow or depth < shallow[name]):
                shallow[name] = depth
            rel = (rel_dir / name).as_posix()
            if len(rel_paths) < MAX_FILES:
                rel_paths.append(rel)
            try:
                mt = (here / name).stat().st_mtime
                newest = max(newest, mt)
            except OSError:
                pass
        if truncated:
            break

    return {
        "file_count": n_files,
        "dir_count": n_dirs,
        "newest_mtime": round(newest, 3),
        "truncated": truncated,
        "ext_counts": ext_counts,
        "top_dirs": top_dirs,
        "root_files": root_files,
        "shallow_files": shallow,
        "rel_paths": rel_paths,
        "sub_ext": sub_ext,
        "sub_shallow": sub_shallow,
        "sub_files": sub_files,
    }


def _sub_probe(probe: dict, bucket: str) -> dict:
    """A probe-shaped view of ONE top-level subsystem, from the walk's per-dir tallies."""
    return {
        "file_count": probe["sub_files"].get(bucket, 0),
        "ext_counts": probe["sub_ext"].get(bucket, {}),
        "shallow_files": probe["sub_shallow"].get(bucket, {}),
    }


def _slice_probe(probe: dict, member: str) -> dict:
    """A probe-shaped view of an ARBITRARY subsystem path (e.g. `packages/web`), reconstructed
    from rel_paths so declared workspace members  -  which need not be top-level dirs  -  classify
    with the same machinery as everything else. Marker depth is measured from the member root."""
    prefix = member.rstrip("/") + "/"
    ext_counts: dict[str, int] = {}
    shallow: dict[str, int] = {}
    n = 0
    for rel in probe["rel_paths"]:
        if not rel.startswith(prefix):
            continue
        sub = rel[len(prefix):]
        n += 1
        ext = Path(sub).suffix.lower()
        if ext:
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        depth = sub.count("/")
        name = sub.rsplit("/", 1)[-1]
        if depth <= MARKER_DEPTH and (name not in shallow or depth < shallow[name]):
            shallow[name] = depth
    return {"file_count": n, "ext_counts": ext_counts, "shallow_files": shallow}


def _all_dirs(probe: dict) -> set[str]:
    """Every directory path implied by rel_paths (posix, target-relative)."""
    dirs: set[str] = set()
    for rel in probe["rel_paths"]:
        parts = rel.split("/")
        for i in range(1, len(parts)):
            dirs.add("/".join(parts[:i]))
    return dirs


def _seg_match(path: str, pattern: str) -> bool:
    """Path-aware glob: `*` matches within ONE segment, never across `/` (fnmatch's `*` does,
    which wrongly makes `packages/*` swallow `packages/web/src`). `**` matches any run of
    segments. Segment counts must line up otherwise."""
    import fnmatch
    pp, cp = pattern.split("/"), path.split("/")
    if "**" in pp:
        i = pp.index("**")
        head, tail = pp[:i], pp[i + 1:]
        if len(cp) < len(head) + len(tail):
            return False
        return (all(fnmatch.fnmatch(c, p) for c, p in zip(cp[:len(head)], head)) and
                (not tail or all(fnmatch.fnmatch(c, p) for c, p in zip(cp[-len(tail):], tail))))
    if len(pp) != len(cp):
        return False
    return all(fnmatch.fnmatch(c, p) for c, p in zip(cp, pp))


def _resolve_members(patterns: list[str], probe: dict) -> list[str]:
    """Resolve workspace member globs (`packages/*`) to concrete directory paths that hold files.
    A literal dir passes through. Nearest-ancestor semantics: a DECLARED member always beats the
    top-level-directory heuristic, and a member nested inside another member is not separate."""
    dirs = _all_dirs(probe)
    out: list[str] = []
    for raw in patterns:
        pat = raw.strip().strip("/")
        if not pat or pat == ".":
            continue
        if pat in dirs:
            out.append(pat)
            continue
        out.extend(d for d in dirs if _seg_match(d, pat))
    resolved = sorted(set(out))
    # Drop descendants: a member that lives inside another member is part of it, not its own.
    return [m for m in resolved if not any(m != o and m.startswith(o + "/") for o in resolved)]


def _workspace_members(target: Path, probe: dict) -> list[str] | None:
    """Declared workspace members, or None if the target declares no workspace.

    Declaration beats heuristic (the universal config rule  -  pnpm/Cargo/Nx/uv all detect
    structure this way before falling back to guessing). Returns concrete member dir paths.
    """
    patterns: list[str] = []

    f = target / "pnpm-workspace.yaml"
    if f.is_file():
        patterns += _parse_yaml_packages(f)

    pj = target / "package.json"
    if pj.is_file():
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
            ws = data.get("workspaces")
            if isinstance(ws, dict):
                ws = ws.get("packages")
            if isinstance(ws, list):
                patterns += [str(x) for x in ws]
        except (json.JSONDecodeError, OSError):
            pass

    for toml_name, path in (("Cargo.toml", ("workspace", "members")),
                            ("pyproject.toml", ("tool", "uv", "workspace", "members"))):
        tf = target / toml_name
        if tf.is_file():
            patterns += _parse_toml_list(tf, path)

    gw = target / "go.work"
    if gw.is_file():
        patterns += _parse_go_work(gw)

    if not patterns:
        return None
    return _resolve_members(patterns, probe)


def _parse_yaml_packages(f: Path) -> list[str]:
    """Minimal reader for pnpm-workspace.yaml's `packages:` list (no yaml dependency)."""
    out: list[str] = []
    in_pkgs = False
    for line in f.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("packages:"):
            in_pkgs = True
            rest = s[len("packages:"):].strip()
            if rest.startswith("["):  # inline list
                out += [x.strip().strip("'\"") for x in rest.strip("[]").split(",") if x.strip()]
                in_pkgs = False
            continue
        if in_pkgs:
            if s.startswith("- "):
                out.append(s[2:].strip().strip("'\""))
            elif not line.startswith((" ", "\t", "-")):
                in_pkgs = False
    return [p for p in out if p]


def _parse_toml_list(f: Path, path: tuple) -> list[str]:
    """Read a nested string-list from a TOML file (e.g. [workspace] members). Best-effort; if
    tomllib is unavailable or the key is absent, returns []."""
    try:
        import tomllib
    except ModuleNotFoundError:
        return []
    try:
        data = tomllib.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    for key in path:
        if not isinstance(data, dict):
            return []
        data = data.get(key)
        if data is None:
            return []
    return [str(x) for x in data] if isinstance(data, list) else []


def _parse_go_work(f: Path) -> list[str]:
    """Read `use` directives from a go.work file (single-line and block form)."""
    out: list[str] = []
    in_block = False
    for line in f.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if in_block:
            if s.startswith(")"):
                in_block = False
            elif s:
                out.append(s.strip("'\""))
            continue
        if s.startswith("use ("):
            in_block = True
        elif s.startswith("use "):
            out.append(s[4:].strip().strip("'\""))
    return [p.lstrip("./") for p in out if p and p not in (")", "(")]


def _classify(carts: list[dict], probe: dict) -> tuple[dict, dict]:
    """Score every cartridge against a probe; return (winner, scores).

    Below MIN_CONFIDENT_SCORE we say `generic` rather than guess  -  an honest "I don't know"
    beats a confident wrong workbench.
    """
    scores = {c["domain"]: _score(c, probe) for c in carts}
    best = max(scores.items(), key=lambda kv: kv[1])
    if best[1] >= MIN_CONFIDENT_SCORE:
        return next(c for c in carts if c["domain"] == best[0]), scores
    return next(c for c in carts if c["domain"] == "generic"), scores


def _compose(carts: list[dict], probe: dict, primary: dict, target: Path) -> dict:
    """Classify each subsystem in its own right.

    A target is frequently not one thing. The first real target was a 12-app monorepo where a
    JS/Electron viewer, a PDF tool and a dozen Python CLIs sat side by side  -  and a single
    cartridge was mounted across all of them. Whole-target classification is the right *primary*
    answer and the wrong *only* answer.

    DECLARATION beats heuristic: if the target declares a workspace (pnpm/Cargo/uv/go.work/
    package.json), its members are the subsystem list  -  even when they nest below the top level
    (`packages/web`). Absent a declaration, fall back to top-level directories. Either way,
    subsystems below MIN_SUBSYSTEM_FILES are skipped: too small to classify honestly.
    """
    declared = _workspace_members(target, probe)
    if declared is not None:
        source = "workspace-manifest"
        candidates = [(m, _slice_probe(probe, m)) for m in declared]
    else:
        source = "top-level-dirs"
        candidates = [(name, _sub_probe(probe, name))
                      for name, _ in sorted(probe["sub_files"].items(), key=lambda kv: -kv[1])]

    subs = []
    for name, sp in candidates:
        if sp["file_count"] < MIN_SUBSYSTEM_FILES:
            continue
        cart, scores = _classify(carts, sp)
        subs.append({
            "name": name,
            "file_count": sp["file_count"],
            "domain": cart["domain"],
            "score": scores[cart["domain"]],
            "mounted": cart.get("mounted", []),
            "policy": cart.get("policy", {}),
        })
    subs.sort(key=lambda s: -s["file_count"])

    named = {s["domain"] for s in subs if s["domain"] != "generic"}
    composite = len(named) > 1 or bool(named - {primary["domain"]})
    return {
        "composite": composite,
        "primary": primary["domain"],
        "subsystem_source": source,
        "subsystems": subs,
    }


def _score(cart: dict, probe: dict) -> float:
    """Score a cartridge against the probe.

    Two signals, deliberately different in kind:

    * **Markers are decisive.** A `pyproject.toml` means Python regardless of file counts. Scored
      once at their shallowest occurrence  -  a monorepo whose sub-apps each carry a
      `requirements.txt` gets the signal at half weight, not Nx weight.
    * **Extensions are mass, measured as a SHARE of the target**  -  not a damped count.

    The share matters. The first real target (a 12-app monorepo, 396 source files) was
    misclassified `data-curation` because `1 + log10(n)` compressed 1->396 into 1.0->3.6: two `.db`
    files and four `.jsonl` outscored 396 `.py`. Absolute counts make a single file worth
    hundreds; a share makes 0.7%-of-the-tree read as the noise it is.
    """
    detect = cart.get("detect") or {}
    total = max(probe["file_count"], 1)
    score = 0.0
    for marker, weight in (detect.get("markers") or {}).items():
        depth = probe["shallow_files"].get(marker)
        if depth is None:
            continue
        score += float(weight) * (1.0 if depth == 0 else MARKER_NESTED_FACTOR)
    for ext, weight in (detect.get("extensions") or {}).items():
        n = probe["ext_counts"].get(ext, 0)
        if n:
            score += float(weight) * (n / total) * SHARE_SCALE
    return round(score, 3)


def _entry_points(cart: dict, probe: dict) -> list[str]:
    hints = cart.get("entry_hints") or []
    if not hints:
        return []
    found = []
    paths = set(probe["rel_paths"])
    for hint in hints:
        if hint in paths:
            found.append(hint)
            continue
        # allow the hint one or two levels down (src/main.py, app/cli.py)
        for rel in probe["rel_paths"]:
            if rel.endswith("/" + hint) and rel.count("/") <= 2:
                found.append(rel)
                break
    return sorted(set(found))


def _signature(probe: dict) -> dict:
    return {"file_count": probe["file_count"], "newest_mtime": probe["newest_mtime"]}


WORKSPACE_FILE = "workspace.json"


def _load_workspace() -> dict:
    """The genesis-recorded workspace identity (id + intent + authority), or {} if none.

    Its presence is what distinguishes a project that BEGAN here (Start New) from one merely
    attached to. Either way attach maps the same surface; this only adds the intent + identity."""
    p = state_root() / WORKSPACE_FILE
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _evidence_density(file_count: int) -> str:
    """How much material exists yet - the axis that replaces 'project type' as the thing that
    varies between Start-New and Attach-Existing. Buckets, not a hard classification."""
    if file_count <= 0:
        return "empty"
    if file_count <= 8:
        return "nascent"
    if file_count <= 40:
        return "sparse"
    return "populated"


def _is_nascent(density: str) -> bool:
    return density in ("empty", "nascent")


def _build_map(target: Path, cart: dict, probe: dict, scores: dict, comp: dict,
               workspace: dict | None = None) -> dict:
    top_ext = sorted(probe["ext_counts"].items(), key=lambda kv: -kv[1])[:8]
    by_domain: dict[str, int] = {}
    for s in comp["subsystems"]:
        by_domain[s["domain"]] = by_domain.get(s["domain"], 0) + 1
    subsystems = [
        {"name": s["name"], "file_count": s["file_count"],
         "domain": s["domain"], "score": s["score"]}
        for s in comp["subsystems"]
    ]
    # Anything too small to classify still exists; report it rather than silently dropping it.
    # Only meaningful for the top-level-dir heuristic  -  under a declared workspace, members can
    # nest and top-level dirs are not the unit, so listing them as "minor" would mislead.
    classified = {s["name"] for s in comp["subsystems"]}
    minor = []
    if comp.get("subsystem_source") == "top-level-dirs":
        minor = [{"name": d, "file_count": n, "domain": None, "score": None}
                 for d, n in sorted(probe["top_dirs"].items(), key=lambda kv: -kv[1])
                 if d not in classified]

    limits = [
        "Structural only: this map describes SHAPE, not MEANING.",
        "No summaries, no embeddings, no semantic retrieval  -  nothing here was read by a model.",
        "Subsystems are top-level directories, classified by the same cartridge scoring as the "
        "whole target. They are not semantically identified components.",
        "Entry points are filename conventions from the cartridge, not verified entrypoints.",
    ]
    if comp["composite"]:
        limits.append(
            "This target is COMPOSITE: its subsystems do not share one domain. `domain` is the "
            "whole-target answer; for work inside a subsystem, read workbench.by_subsystem  -  it "
            "is authoritative there."
        )
    density = _evidence_density(probe["file_count"])
    nascent = _is_nascent(density)
    # domain_status: for a project with real material the domain is a detection; for a nascent
    # one it is only a SUGGESTION - too little exists to identify a type, and the workspace intent
    # (if any) outranks it. This is E3's "profiles are defaults, not identities" made explicit.
    domain_status = "suggested" if nascent else "detected"
    if nascent:
        limits.append(
            "NASCENT workspace (evidence density: " + density + "). Too little material exists to "
            "identify a project TYPE - `domain` here is a SUGGESTION, not an identity. Let the "
            "intent and the work drive structure; a profile can be adopted as artifacts accumulate."
        )
    result = {
        "target": str(target),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "domain": cart["domain"],
        "domain_status": domain_status,
        "domain_summary": cart.get("summary", ""),
        "domain_scores": scores,
        "composite": comp["composite"],
        "evidence_density": density,
        "nascent": nascent,
        "shape": {
            "file_count": probe["file_count"],
            "dir_count": probe["dir_count"],
            "top_extensions": [{"ext": e, "count": n} for e, n in top_ext],
            "truncated": probe["truncated"],
        },
        "subsystems": subsystems + minor[:12],
        "subsystem_source": comp.get("subsystem_source"),
        "subsystem_domains": by_domain,
        "entry_points": _entry_points(cart, probe),
        "vcs": "git" if (target / ".git").exists() else None,
        "signature": _signature(probe),
        "limits": limits,
    }
    if workspace:
        # Surface the genesis-recorded identity: this project BEGAN here from an intention.
        result["intent"] = workspace.get("intent")
        result["workspace"] = {k: workspace.get(k) for k in
                               ("workspace_id", "name", "authority", "profile_hint", "created_at")}
    return result


# The universal hands + memory: every target needs to read, find, write, and remember, whatever
# its domain. Unioned into every workbench so an agent following `attach` always has them, and so
# new hands (C-series) are added in ONE place. (Only tools that already exist are surfaced.)
BASE_MOUNT = ["read_file", "glob", "repo_search", "write_file", "edit", "fs_op", "project_run",
              "diff", "journal", "evidence"]


def _build_workbench(cart: dict, comp: dict) -> dict:
    """Mount the primary cartridge's tools, plus the universal base, plus every subsystem's.

    The union is deliberate and it is still selection, not surrender: every tool is there because
    the target's domain, the base hands, or some subsystem needs it. `by_subsystem` is the
    authoritative view  -  a tool's policy is only meaningful against a specific domain
    (`import_graph` is trustworthy on the Python apps and mute on the JS one), so an agent working
    inside a subsystem reads that entry, not the union.
    """
    mounted = list(cart.get("mounted") or [])
    home = suite_home()
    for t in BASE_MOUNT:
        # Only surface a base tool that actually exists  -  otherwise the workbench would advertise
        # a phantom an agent then fails to call.
        if t not in mounted and (home / "tools" / t / "tool.json").is_file():
            mounted.append(t)
    for s in comp["subsystems"]:
        for t in s["mounted"]:
            if t not in mounted:
                mounted.append(t)
    wb = {
        "mounted": mounted,
        "policy": cart.get("policy", {}),
        "primary_domain": cart["domain"],
    }
    if comp["composite"]:
        wb["by_subsystem"] = {
            s["name"]: {"domain": s["domain"], "mounted": s["mounted"], "policy": s["policy"]}
            for s in comp["subsystems"]
        }
    return wb


OVERRIDES_FILENAME = "policy_overrides.json"


def _overrides_path() -> Path:
    """Operator policy overrides live in the STATE ROOT, deliberately NOT in the workbench.

    The workbench is rewritten wholesale by `refresh`; the state root is durable memory. Putting
    overrides here is the entire reason they survive a re-map: refresh cannot clobber what it
    does not own. They are also applied at READ time and never written back into profile.json,
    so a stored profile stays a faithful record of what was DETECTED, and the override stays a
    separate, visible statement of what the operator DECIDED.
    """
    return state_root() / OVERRIDES_FILENAME


def _load_overrides(target: Path) -> dict:
    """Overrides for this target: the `*` block (all targets) under the target-specific block.

    Shape: {"<target path>" | "*": {"<tool_id>": {confidence?, note?, tool_args?}}}
    A malformed file must not take the front door down - a bad override degrades to none.
    """
    path = _overrides_path()
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    merged: dict = {}
    key = target.resolve().as_posix()
    for block_key in ("*", key, str(target.resolve())):
        block = raw.get(block_key)
        if isinstance(block, dict):
            for tool_id, frag in block.items():
                if isinstance(frag, dict):
                    merged.setdefault(tool_id, {}).update(frag)
    return merged


def _merge_policy(policy: dict, overrides: dict) -> "tuple[dict, list[str]]":
    """Layer overrides over a cartridge policy. Returns (policy, overridden tool ids).

    `tool_args` merges key-wise so an operator can pin ONE argument without restating the
    cartridge's others; every other field replaces outright.
    """
    if not overrides:
        return dict(policy or {}), []
    out = {k: dict(v) if isinstance(v, dict) else v for k, v in (policy or {}).items()}
    touched = []
    for tool_id, frag in overrides.items():
        entry = dict(out.get(tool_id) or {})
        for field, value in frag.items():
            if field == "tool_args" and isinstance(value, dict):
                entry["tool_args"] = {**(entry.get("tool_args") or {}), **value}
            else:
                entry[field] = value
        entry["overridden"] = True  # an agent must SEE that this is operator policy, not cartridge
        out[tool_id] = entry
        touched.append(tool_id)
    return out, sorted(touched)


def _apply_overrides(workbench: dict, cart: dict, target: Path) -> dict:
    """Fold operator overrides into both the workbench AND the cart that drives `next`.

    Both, because the payoff is not a cosmetic note: `_policy_args` reads the cart to pre-bind
    arguments into the suggested calls, so an override that did not reach the cart would be
    advertised and then not applied.
    """
    overrides = _load_overrides(target)
    if not overrides:
        return workbench
    merged, touched = _merge_policy(workbench.get("policy") or {}, overrides)
    workbench["policy"] = merged
    cart["policy"] = merged
    workbench["policy_overrides"] = {
        "source": str(_overrides_path()),
        "tools": touched,
        "note": "operator overrides layered over the cartridge policy; they survive refresh",
    }
    return workbench


def _policy_args(cart: dict, tool_id: str) -> dict:
    """The `tool_args` a cartridge pre-binds for a tool  -  the policy layer's payload.

    A cartridge can carry project-specific configuration a tool needs to behave (e.g. the custom
    entrypoint decorators that keep `dead_code` from calling live handlers dead). `attach` folds
    these into the `next` calls so the agent's invocation is correct by construction  -  it never
    has to know the policy exists. Tools stay decoupled: no tool reads the profile; the front
    door hands them the right args. See _design/CHARTER.md sec 4 and _design/PLAN.md Phase 2.
    """
    return dict((cart.get("policy") or {}).get(tool_id, {}).get("tool_args") or {})


def _module_docstring(path: Path) -> str:
    """Cheap purpose signal from a file's head: a Python module docstring, or the first
    doc-ish lines of anything else. Bounded; never reads more than the head of the file."""
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:2000]
    except OSError:
        return ""
    if path.suffix == ".py":
        import ast
        try:
            doc = ast.get_docstring(ast.parse(head))
            if doc:
                return doc.strip()[:400]
        except SyntaxError:
            pass
    # markdown/text/other: first few non-blank, non-fence lines
    lines = [ln.strip() for ln in head.splitlines() if ln.strip() and not ln.startswith("```")]
    return " ".join(lines[:5])[:400]


def _gather_signals(target: Path, pmap: dict, probe: dict) -> str:
    """Assemble cheap, bounded signals for one summary call  -  no per-file LLM work, and no second
    filesystem walk: representative files come from the paths the probe already collected."""
    subs = pmap.get("subsystems", [])
    parts: list[str] = [
        f"Detected kind: {pmap.get('domain')} - {pmap.get('domain_summary', '')}",
        "Top-level subsystems: " + (", ".join(
            f"{s['name']}({s['file_count']} files, {s.get('domain') or '?'})"
            for s in subs[:10]) or "(none)"),
        "Entry points: " + (", ".join(pmap.get("entry_points", [])) or "(none)"),
        "Top file types: " + (", ".join(
            f"{e['ext']}x{e['count']}"
            for e in pmap.get("shape", {}).get("top_extensions", [])[:6]) or "(none)"),
    ]
    rel_paths = probe.get("rel_paths", [])
    # README at the root, from the already-collected paths.
    readme = next((r for r in rel_paths
                   if "/" not in r and r.lower().startswith("readme")), None)
    if readme:
        parts.append("README:\n" + _module_docstring(target / readme))

    # One representative .py per top subsystem, plus the entry points  -  from rel_paths, no re-walk.
    doc_files = list(pmap.get("entry_points", []))
    for s in subs[:6]:
        name = s.get("name")
        if not name:
            continue
        head = next((r for r in rel_paths if r.startswith(f"{name}/") and r.endswith(".py")), None)
        if head:
            doc_files.append(head)

    seen: set[str] = set()
    for rel in doc_files[:8]:
        if rel in seen:
            continue
        seen.add(rel)
        doc = _module_docstring(target / rel)
        if doc:
            parts.append(f"{rel}: {doc}")
    return "\n".join(p for p in parts if p)


def _synopsis(target: Path, pmap: dict, probe: dict) -> dict | None:
    """A short, model-written PURPOSE statement grounded in gathered signals  -  or None when no
    summary backend is reachable (attach then stays structural). Bounded to one call; the caller
    persists it in the map so re-engage never re-summarizes (Gf)."""
    if not summarize_shared.available():
        return None
    signals = _gather_signals(target, pmap, probe)
    purpose = summarize_shared.summarize_project(signals)
    if not purpose:
        return None
    return {"purpose": purpose, "model": summarize_shared.probe().get("model"),
            "grounded_in": "README + module docstrings + structure (no file read by the reader)"}


def _next_steps(mode: str, cart: dict, stale: bool, *, nascent: bool = False,
                has_intent: bool = False) -> list[dict]:
    steps: list[dict] = []
    if mode == "reengaged" and stale:
        steps.append({
            "why": "The target changed since it was mapped.",
            "call": {"tool": "attach", "args": {"refresh": True}},
        })
    steps.append({
        "why": ("Read the recorded intent and any decisions so far - the thread this workspace "
                "began with." if has_intent else
                "Read the durable history of this target before acting."),
        "call": {"tool": "journal", "args": {"action": "list", "limit": 10}},
    })
    if nascent:
        # A near-empty workspace: code-analysis steps are pointless (there is no code yet). Point
        # at GROWTH instead - give it structure, then re-map as artifacts accumulate. This is the
        # Start-New half of the loop; it converges on the same map once material exists.
        steps.append({
            "why": ("Materialize the structure the intent implies - dirs, files, a PROJECT_PLAN. "
                    "Browse archetypes first, then create from a map."),
            "call": {"tool": "scaffold_project", "args": {"action": "archetypes"}},
        })
        steps.append({
            "why": "Record what you decided to build and why, so the next agent inherits it.",
            "call": {"tool": "journal", "args": {"action": "add", "title": "...", "summary": "..."}},
        })
        steps.append({
            "why": "Re-map once files exist: the domain firms up from a suggestion to a detection.",
            "call": {"tool": "attach", "args": {"refresh": True}},
        })
        return steps
    if mode == "mapped":
        steps.append({
            "why": "Record that you attached, so the next agent inherits the thread.",
            "call": {"tool": "journal", "args": {"action": "add", "title": "Attached", "summary": "..."}},
        })
    mounted = cart.get("mounted") or []
    if "report" in mounted:
        steps.append({
            "why": "Macro structure of the target. Deterministic  -  trust it.",
            "call": {"tool": "report", "args": {"path": "."}},
        })
    if "symbol_graph" in mounted:
        summaries_exist = (output_root() / "symbol_graph" / "summaries.json").is_file()
        steps.append({
            "why": ("Resolved who-calls-whom. Use refs before touching any symbol - inbound is "
                    "the real caller list."
                    + (" Per-module summaries are already cached; refs returns them."
                       if summaries_exist else
                       " Run action=summarize once to cache per-module purpose lines "
                       "(only changed files cost inference afterwards).")),
            "call": {"tool": "symbol_graph",
                     "args": {"action": "stats" if summaries_exist else "summarize"}},
        })
    if "dead_code" in mounted:
        steps.append({
            "why": "Unused-symbol leads. Policy is pre-bound: framework entrypoints are already "
                   "recognized, so trust only high/medium findings and verify before deleting.",
            "call": {"tool": "dead_code", "args": {"root": ".", **_policy_args(cart, "dead_code")}},
        })
    return steps


def _apply_scope(result: dict, scope: str) -> dict:
    """Narrow a full attach result to ONE subsystem  -  the narrowing half of composition.

    Nearest-ancestor resolution made structural: an agent working inside a subsystem asks for
    its scope and gets exactly that subsystem's workbench, policy, and pre-bound next  -  not the
    union, and not a documentation note telling it which part of the union applies. For a
    composite target the answer comes from `by_subsystem`; for a uniform (non-composite) target
    every subsystem shares the primary domain, so the primary workbench IS the scoped answer.
    """
    wb = result.get("workbench") or {}
    pmap = result.get("project_map") or {}
    by = wb.get("by_subsystem") or {}
    known = {s["name"] for s in (pmap.get("subsystems") or []) if s.get("name")}

    if scope in by:
        entry = by[scope]
        sub_cart = {"domain": entry["domain"], "mounted": entry.get("mounted", []),
                    "policy": entry.get("policy", {})}
    elif scope in known:
        # uniform target: the subsystem's domain is the primary domain.
        sub_cart = {"domain": wb.get("primary_domain"), "mounted": wb.get("mounted", []),
                    "policy": wb.get("policy", {})}
    else:
        return {"ok": False, "error": f"no subsystem '{scope}' in this target",
                "available_scopes": sorted(known or by)}

    scoped = dict(result)
    scoped["scope"] = scope
    scoped["workbench"] = {
        "scoped_to": scope,
        "domain": sub_cart["domain"],
        "mounted": sub_cart["mounted"],
        "policy": sub_cart["policy"],
    }
    scoped["next"] = _next_steps("mapped", sub_cart, False)
    return scoped


@tool_main
def run(args: dict) -> dict:
    home = suite_home()
    # ONE BOUND TARGET. `attach` used to prefer an arbitrary `target` argument over
    # the canonical root, which made the agent's front door a SECOND target authority:
    # an instance bound to A could be asked to attach to B. T6 ended that.
    #
    # The argument survives only as a redundant assertion of the same target - useful
    # for a caller that wants to be explicit - and is refused when it disagrees. It
    # cannot rebind the sidecar. Attaching elsewhere means installing an instance
    # there (Charter SIDECAR:INSTANCE-OWNERSHIP).
    # ONE BOUND TARGET - BUT SCOPE IS NOT REBINDING.
    #
    # `attach` used to prefer an arbitrary `target` argument over the canonical root,
    # which made the agent's front door a SECOND target authority: an instance bound
    # to A could be asked to attach to B. T6 ended that.
    #
    # The distinction that matters is identity-level vs scope-level. A path INSIDE the
    # bound target is a narrower view of the same reality - `genesis` scaffolds a new
    # project in a subdirectory and then orients on it, which is the product working on
    # its target. A path OUTSIDE is a different reality, and asking for it is asking
    # this instance to be a different instance.
    #
    # A first version required exact equality and broke genesis, which is how the
    # difference surfaced: the rule is containment, not identity of the path.
    bound = project_root()
    target = bound
    requested = args.get("target")
    if requested:
        asked = Path(requested).expanduser().resolve()
        if asked != bound and bound not in asked.parents:
            return {"ok": False, "tool": "attach",
                    "error": f"this instance is bound to {bound}; it cannot attach to "
                             f"{asked}, which lies outside that target. Install an "
                             "instance into that target instead.",
                    "bound_target": str(bound)}
        target = asked
    if not target.is_dir():
        return {"ok": False, "error": f"target is not a directory: {target}"}
    scope = args.get("scope")

    wb = _workbench()
    profile_path, map_path = wb / "profile.json", wb / "map.json"
    have = profile_path.exists() and map_path.exists()
    forced = bool(args.get("refresh")) or bool(args.get("domain"))

    # ---- RE-ENGAGE ---------------------------------------------------------------
    if have and not forced:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        pmap = json.loads(map_path.read_text(encoding="utf-8"))
        # THE PROFILE'S RECORDED TARGET IS A DISPLAY VALUE, NOT A BINDING.
        #
        # This compared a stored ABSOLUTE path against the resolved target, so moving a
        # target and its instance together - which T6 exists to make safe - made the
        # front door refuse: "this workbench is attached to X, not Y". The relationship
        # had not broken; only a string written down beside it had gone stale.
        #
        # Where an instance exists, IDENTITY decides what the target is (T6), so a
        # matching uuid means this workbench belongs to this target wherever it now
        # lives. The path comparison survives only for the uninstalled case, which has
        # no identity to consult - the same environment-governs-development rule the
        # roots already follow.
        known = Path(profile.get("target", ""))
        bound_uuid = instance_uuid()
        same_instance = bool(bound_uuid) and profile.get("instance") == bound_uuid
        if not same_instance and known.resolve() != target:
            return {
                "ok": False,
                "error": (f"this workbench is attached to {known}, not {target}. "
                          f"Pass refresh:true to re-attach it to the new target."),
                "attached_to": str(known),
            }
        probe = _probe(target)
        now, then = _signature(probe), pmap.get("signature", {})
        stale = now != then
        cart = {"domain": profile["domain"], "mounted": profile.get("mounted", []),
                "policy": profile.get("policy") or (profile.get("workbench") or {}).get("policy", {})}
        workbench = profile.get("workbench") or {
            "mounted": profile.get("mounted", []), "policy": profile.get("policy", {})}
        workbench = _apply_overrides(dict(workbench), cart, target)
        # Density is recomputed from the CURRENT probe (files may have grown since the map was
        # written), and the live workspace intent is surfaced - so re-engaging a workspace that
        # began nascent and has since acquired artifacts firms up automatically.
        workspace = _load_workspace()
        density = _evidence_density(probe["file_count"])
        nascent = _is_nascent(density)
        # Recompute domain_status alongside density so they can never contradict: a workspace
        # mapped while nascent that has since grown must not report nascent=False yet
        # domain_status="suggested". (A full refresh re-detects the domain itself; this keeps the
        # cheaper re-engage path internally consistent in the meantime.)
        pmap = {**pmap, "evidence_density": density, "nascent": nascent,
                "domain_status": "suggested" if nascent else "detected"}
        if workspace:
            pmap["intent"] = workspace.get("intent")
            pmap["workspace"] = {k: workspace.get(k) for k in
                                 ("workspace_id", "name", "authority", "profile_hint", "created_at")}
        result = {
            "ok": True,
            "mode": "reengaged",
            "target": str(target),
            "project_map": pmap,
            "workbench": workbench,
            "staleness": {
                "stale": stale,
                "mapped_at": pmap.get("generated_at"),
                "signature_then": then,
                "signature_now": now,
            },
            "next": _next_steps("reengaged", cart, stale, nascent=nascent,
                                has_intent=bool(workspace.get("intent"))),
        }
        # Re-engage READS the persisted revision; it does not re-observe. Recomposing
        # here would spend every contributor on every attach and defeat the whole point
        # of persisting. A stale target earns a fresh revision only on refresh, which is
        # the same coarse signal `staleness` already reports.
        held = awareness_shared.load_current()
        # Projected, not recomposed. The held revision is still the current knowledge;
        # `stale` says whether it still describes the target. Returning it verbatim let
        # the envelope claim freshness the outer `staleness` block was simultaneously
        # denying, in one response.
        result["awareness"] = (awareness_shared.project_freshness(held, stale) if held
                               else awareness_shared.build(pmap, probe, stale))
        return _apply_scope(result, scope) if scope else result

    # ---- MAP ---------------------------------------------------------------------
    carts = _cartridges(home)
    probe = _probe(target)
    detected, scores = _classify(carts, probe)

    if args.get("domain"):
        chosen = next((c for c in carts if c["domain"] == args["domain"]), None)
        if chosen is None:
            return {"ok": False, "error": f"unknown domain '{args['domain']}'",
                    "known": sorted(scores)}
    else:
        chosen = detected

    comp = _compose(carts, probe, chosen, target)
    workspace = _load_workspace()
    pmap = _build_map(target, chosen, probe, scores, comp, workspace)
    # Gf: a model-written PURPOSE grounded in cheap signals, so a fresh agent can state what the
    # target IS without reading a file. One bounded call; persisted in the map, so re-engage
    # reuses it for free. Absent a summary backend, the map stays structural (limit noted).
    synopsis = _synopsis(target, pmap, probe)
    if synopsis:
        pmap["synopsis"] = synopsis
    else:
        pmap["limits"].append(
            "No semantic synopsis: no summary backend reachable. This map is structural only; "
            "it describes SHAPE, not PURPOSE.")
    workbench = _build_workbench(chosen, comp)
    profile = {
        "target": str(target),
        # Recorded so a relocated instance recognises its own workbench. The uuid is the
        # binding; the path above is only what a reader wants to see.
        "instance": instance_uuid(),
        "attached_at": pmap["generated_at"],
        "domain": chosen["domain"],
        "selected_by": "explicit" if args.get("domain") else "detected",
        "composite": comp["composite"],
        "workbench": workbench,
        # Flattened for readers that only want the tool list.
        "mounted": workbench["mounted"],
        "policy": workbench["policy"],
    }

    wb.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    map_path.write_text(json.dumps(pmap, indent=2) + "\n", encoding="utf-8")

    # Overrides are layered AFTER the profile is persisted, onto a copy: the stored profile stays
    # a faithful record of what was DETECTED, while the answer the agent gets reflects what the
    # operator DECIDED. That separation is what lets refresh re-detect without losing the decision.
    workbench = _apply_overrides(json.loads(json.dumps(workbench)), chosen, target)

    result = {
        "ok": True,
        "mode": "mapped",
        "target": str(target),
        "project_map": pmap,
        "workbench": workbench,
        "written": {"profile": str(profile_path), "map": str(map_path)},
        "next": _next_steps("mapped", chosen, False, nascent=pmap.get("nascent", False),
                            has_intent=bool(workspace.get("intent"))),
    }
    result["awareness"] = awareness_shared.build(pmap, probe, False)
    return _apply_scope(result, scope) if scope else result
