"""
FILE:       tools/scaffold_shared.py
ROLE:       The scaffold CONTRACT - validate a project map, then turn it into a real file tree.
DOMAIN:     tool (shared substrate)
DOES:       validate_map(map): enforce the work-order contract (names, relative paths, no escapes,
            no duplicates, file/dir conflicts) and return a normalized plan or a precise error.
            plan_tree(map, base): resolve every node to an absolute path, flag collisions, and
            render the exact bytes each file would receive - WITHOUT writing. render_file(): stamp
            a FILE/ROLE/DOES header (in the right comment style) around a planned stub, or pass
            explicit content through verbatim. ARCHETYPES: a few reusable starting maps.
DEPENDS ON: tools._toolkit (resolve_within_roots); (stdlib) posixpath
WIRES TO:   tools/scaffold_project/cli.py (the materializer).
NOTES:      The tool is deliberately DUMB: it plans nothing and decides nothing, it honors a
            contract the agent fed it. All intelligence (what the project should be) lives in the
            agent/planner above; this layer's whole job is to be a faithful, preview-first,
            escape-proof materializer. It creates ONLY the project tree - no sidecar traces,
            nothing outside the resolved base - so a scaffolded project is born precept-clean and
            can exist without ever knowing a sidecar could attach to it.

            CONTRACT (the "work order") - one JSON object:
              name:      str, required. A human/slug name for the project.
              plan:      str, optional. The natural-language plan -> PROJECT_PLAN.md.
              archetype: str, optional. A built-in starting map, OVERLAID by `tree` below.
              tree:      list of nodes. Each node is exactly one of:
                {"dir": "<relpath>"}                                  a directory
                {"file": "<relpath>", ...}                            a file, where extras are:
                   content:    str  - written VERBATIM (the agent owns it fully; no header added)
                   template:   str  - a named boilerplate body (BOILERPLATE) used when no content
                   role/does/depends_on/wires_to/plan: str - stamped into the file's header
              A node with neither content nor template becomes a documented STUB: just the header.
"""
from __future__ import annotations

import posixpath

from tools._toolkit import resolve_within_roots

# ---------------------------------------------------------------- comment styles for headers
# (open, line_prefix, close). A header is stamped only into files we GENERATE (stub/template),
# never into a file whose bytes the agent supplied verbatim via `content`.
_C_BLOCK = ("/*", " * ", " */")
_HASH = ("", "# ", "")
COMMENT_STYLES = {
    ".py": ('"""', "", '"""'), ".pyw": ('"""', "", '"""'),
    ".js": _C_BLOCK, ".jsx": _C_BLOCK, ".ts": _C_BLOCK, ".tsx": _C_BLOCK,
    ".java": _C_BLOCK, ".c": _C_BLOCK, ".h": _C_BLOCK, ".cpp": _C_BLOCK, ".go": _C_BLOCK,
    ".rs": _C_BLOCK, ".css": _C_BLOCK,
    ".sh": _HASH, ".rb": _HASH, ".yaml": _HASH, ".yml": _HASH, ".toml": _HASH,
    ".ini": _HASH, ".cfg": _HASH, ".ps1": _HASH,
    ".md": ("<!--", "", "-->"), ".html": ("<!--", "", "-->"),
}

# Files where a code-style header would be wrong or harmful: leave them to content/template only.
_NO_HEADER = {".json", ".txt", ".csv", ".lock", ".env", ".gitignore"}

# Named boilerplate bodies. Kept tiny and honest - a starting point, not a framework.
BOILERPLATE = {
    "python_entry": (
        "from __future__ import annotations\n\n\n"
        "def main() -> int:\n"
        '    """Entry point. Replace with the real thing."""\n'
        "    print(\"hello from {name}\")\n"
        "    return 0\n\n\n"
        'if __name__ == \"__main__\":\n'
        "    raise SystemExit(main())\n"),
    "python_module": (
        "from __future__ import annotations\n\n\n"
        "# TODO: implement per the header above.\n"),
    "gitignore_python": (
        "__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n_artifacts/\n.pytest_cache/\n"),
    "readme": ("# {name}\n\n{plan}\n\n## Layout\n\nSee PROJECT_PLAN.md for the full plan.\n"),
    "html_index": (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\">\n"
        "  <title>{name}</title>\n</head>\n<body>\n  <h1>{name}</h1>\n</body>\n</html>\n"),
}


def _ext(path: str) -> str:
    dot = path.rfind(".")
    slash = max(path.rfind("/"), path.rfind("\\"))
    return path[dot:].lower() if dot > slash else ""


def _clean_relpath(raw: str) -> "tuple[str, str]":
    """Normalize a contract path and reject anything that is not a safe, relative, in-tree path.
    Returns (posix_relpath, "") or ("", error)."""
    s = str(raw or "").strip().replace("\\", "/")
    if not s:
        return "", "empty path"
    if s.startswith("/") or (len(s) > 1 and s[1] == ":"):
        return "", f"path must be relative, not absolute: {raw!r}"
    norm = posixpath.normpath(s)
    if norm == "." or norm.startswith("..") or "/../" in norm or norm.endswith("/.."):
        return "", f"path escapes the project root: {raw!r}"
    return norm, ""


def validate_map(project_map: dict) -> "tuple[dict | None, str]":
    """Enforce the work-order contract. Returns (normalized_map, "") or (None, error).

    `normalized_map` has: name, plan, dirs (sorted unique), files (list of validated file nodes,
    each with a resolved relpath). This is where the tool refuses to guess - a malformed map is a
    hard error naming the offending node, never a silent best-effort.
    """
    if not isinstance(project_map, dict):
        return None, "project map must be a JSON object"
    name = str(project_map.get("name") or "").strip()
    if not name:
        return None, "map.name is required"

    archetype = project_map.get("archetype")
    nodes: list = []
    if archetype:
        base = ARCHETYPES.get(str(archetype))
        if base is None:
            return None, (f"unknown archetype {archetype!r}; "
                          f"known: {sorted(ARCHETYPES)}")
        nodes.extend(base.get("tree", []))
    nodes.extend(project_map.get("tree") or [])
    if not nodes:
        return None, "map has no tree nodes and no archetype to expand"

    dirs: set[str] = set()
    files: dict[str, dict] = {}   # relpath -> node (later wins, so overlay works)
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            return None, f"tree[{i}] must be an object, got {type(node).__name__}"
        has_dir, has_file = "dir" in node, "file" in node
        if has_dir == has_file:
            return None, f"tree[{i}] must have exactly one of 'dir' or 'file'"
        if has_dir:
            rel, err = _clean_relpath(node["dir"])
            if err:
                return None, f"tree[{i}].dir: {err}"
            dirs.add(rel)
            continue
        rel, err = _clean_relpath(node["file"])
        if err:
            return None, f"tree[{i}].file: {err}"
        if "content" in node and "template" in node:
            return None, f"tree[{i}] ({rel}): give at most one of 'content' or 'template'"
        tmpl = node.get("template")
        if tmpl is not None and str(tmpl) not in BOILERPLATE:
            return None, (f"tree[{i}] ({rel}): unknown template {tmpl!r}; "
                          f"known: {sorted(BOILERPLATE)}")
        files[rel] = {"rel": rel, **{k: v for k, v in node.items() if k != "file"}}

    # a path cannot be both a file and a declared dir, and no file may sit under another file
    for f in files:
        if f in dirs:
            return None, f"{f} is declared as both a file and a directory"
    return {"name": name, "plan": str(project_map.get("plan") or "").strip(),
            "dirs": sorted(dirs), "files": [files[k] for k in sorted(files)]}, ""


def _header(rel: str, node: dict, name: str) -> str:
    """Stamp a FILE/ROLE/DOES header in the file's comment style. Empty when the type takes none."""
    ext = _ext(rel)
    if ext in _NO_HEADER or ext not in COMMENT_STYLES:
        return ""
    open_tok, line_pre, close_tok = COMMENT_STYLES[ext]
    fields = [("FILE", rel), ("ROLE", node.get("role") or "(planned)"),
              ("DOES", node.get("does") or node.get("plan") or "(to be implemented)")]
    if node.get("depends_on"):
        fields.append(("DEPENDS ON", node["depends_on"]))
    if node.get("wires_to"):
        fields.append(("WIRES TO", node["wires_to"]))
    fields.append(("STATUS", "PLANNED"))
    body = "\n".join(f"{line_pre}{k+':':<12}{v}" for k, v in fields)
    if open_tok in ('"""',):
        return f'{open_tok}\n{body}\n{close_tok}\n'
    return f"{open_tok}\n{body}\n{close_tok}\n"


def render_file(node: dict, name: str, plan: str) -> str:
    """The exact bytes a planned file would receive.

    - explicit `content`: verbatim (the agent owns it; no header).
    - `template`: the boilerplate body, header stamped above it.
    - neither: a documented STUB - just the header.
    Template/plan/name placeholders ({name},{plan}) are filled by str.replace, never .format,
    so literal braces in agent content can never blow up templating.
    """
    if "content" in node:
        return str(node["content"])
    header = _header(node["rel"], node, name)
    body = ""
    if node.get("template"):
        body = BOILERPLATE[str(node["template"])]
        body = body.replace("{name}", name).replace("{plan}", plan or name)
    if header and body:
        return header + "\n" + body
    return header or body


def render_project_plan(norm: dict) -> str:
    """PROJECT_PLAN.md - the NL plan plus a table of every planned file and its role/does.
    This is the single place the plan is captured centrally, so files and plan cannot drift apart
    unnoticed: regenerate the scaffold and this doc is rebuilt from the same contract."""
    lines = [f"# {norm['name']}", "",
             norm["plan"] or "_No plan text supplied._", "",
             "## Planned files", "",
             "| file | role | does |", "|---|---|---|"]
    for f in norm["files"]:
        role = str(f.get("role") or "").replace("|", "\\|") or "-"
        does = str(f.get("does") or f.get("plan") or "").replace("|", "\\|") or "-"
        lines.append(f"| `{f['rel']}` | {role} | {does} |")
    lines += ["", "## Directories", ""]
    lines += [f"- `{d}/`" for d in norm["dirs"]] or ["_(none declared)_"]
    lines += ["", "---", "_Generated by scaffold_project from the project map._"]
    return "\n".join(lines) + "\n"


def plan_tree(norm: dict, base) -> "tuple[list, str]":
    """Resolve every node to an absolute path under `base`, confined to the roots. Returns
    (planned, "") where planned is a list of {kind, rel, abs, bytes?, collision} - or ("", error)
    if any path escapes. Writes nothing."""
    planned: list = []
    # implicit parent dirs for every file, so the plan is complete
    all_dirs = set(norm["dirs"])
    for f in norm["files"]:
        parent = posixpath.dirname(f["rel"])
        while parent:
            all_dirs.add(parent)
            parent = posixpath.dirname(parent)
    for d in sorted(all_dirs):
        p, err = resolve_within_roots(d, base=base)
        if err:
            return [], f"directory {d!r}: {err}"
        planned.append({"kind": "dir", "rel": d, "abs": p.as_posix(),
                        "collision": p.exists() and not p.is_dir()})
    for f in norm["files"]:
        p, err = resolve_within_roots(f["rel"], base=base)
        if err:
            return [], f"file {f['rel']!r}: {err}"
        content = render_file(f, norm["name"], norm["plan"])
        planned.append({"kind": "file", "rel": f["rel"], "abs": p.as_posix(),
                        "bytes": len(content.encode("utf-8")), "content": content,
                        "collision": p.exists()})
    # PROJECT_PLAN.md is always part of the deliverable
    pp, err = resolve_within_roots("PROJECT_PLAN.md", base=base)
    if not err:
        planned.append({"kind": "file", "rel": "PROJECT_PLAN.md", "abs": pp.as_posix(),
                        "content": render_project_plan(norm),
                        "bytes": len(render_project_plan(norm).encode("utf-8")),
                        "collision": pp.exists()})
    return planned, ""


# ---------------------------------------------------------------- archetypes (starting maps)
ARCHETYPES: dict[str, dict] = {
    "python-cli": {
        "label": "Python CLI",
        "description": "A headless Python CLI: package + entry point + tests + config.",
        "tree": [
            {"dir": "src"},
            {"dir": "tests"},
            {"file": "src/__init__.py", "role": "package marker", "does": "marks src as a package"},
            {"file": "src/app.py", "template": "python_entry",
             "role": "entry point", "does": "boots the CLI and dispatches commands"},
            {"file": "src/core.py", "template": "python_module",
             "role": "core logic", "does": "the domain logic the CLI drives"},
            {"file": "tests/test_smoke.py", "template": "python_module",
             "role": "smoke test", "does": "proves the entry point runs end to end"},
            {"file": "README.md", "template": "readme", "role": "readme"},
            {"file": ".gitignore", "template": "gitignore_python"},
            {"file": "requirements.txt", "content": "# add dependencies here, one per line\n"},
        ],
    },
    "web-app": {
        "label": "Static web app",
        "description": "A minimal static web app: index, style, script.",
        "tree": [
            {"dir": "assets"},
            {"file": "index.html", "template": "html_index", "role": "page shell"},
            {"file": "assets/style.css", "role": "styles", "does": "page styling"},
            {"file": "assets/app.js", "role": "behavior", "does": "client-side behavior"},
            {"file": "README.md", "template": "readme", "role": "readme"},
        ],
    },
    "records-project": {
        "label": "Records / data project",
        "description": "A body-of-records project: raw inputs, working set, outputs, notes.",
        "tree": [
            {"dir": "raw"}, {"dir": "working"}, {"dir": "output"}, {"dir": "notes"},
            {"file": "README.md", "template": "readme", "role": "readme"},
            {"file": "notes/INTAKE.md", "role": "intake log",
             "does": "what arrived, from where, when, and its provenance"},
        ],
    },
}
