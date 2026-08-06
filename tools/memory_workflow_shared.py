"""
FILE:       tools/memory_workflow_shared.py
ROLE:       Shared deterministic helpers for memory/session/workflow tools.
DOMAIN:     tool
DOES:       Provides workflow templates, task decomposition, semantic chunks, simple retrieval,
            session JSONL persistence, rules evaluation, and memory flush summaries.
DEPENDS ON: (stdlib) ast, collections, datetime, hashlib, json, pathlib, re
WIRES TO:   workflow_templates, workflow_decompose, session_record, session_replay,
            semantic_chunk, rag_retrieve, rules_eval, memory_flush
NOTES:      PATTERN from _theCELL SessionManager, SemanticChunker, RAGRetrieval,
            CognitiveMemory, workflow JSONs, and RulesEngine. Deterministic and local-only.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from tools._toolkit import suite_home

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
TASK_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(?P<text>.+)$")

BUILTIN_TEMPLATES = {
    "code_review": {
        "id": "code_review",
        "label": "Code Review",
        "description": "Inspect a change for behavioral risk, tests, and follow-up work.",
        "steps": [
            {"id": "scope", "title": "Identify changed files and stated goal",
             "system_prompt": "Map the change scope before judging it.",
             "user_content": "Summarize the changed files, intended behavior, and likely risk areas."},
            {"id": "review", "title": "Find correctness and regression issues",
             "system_prompt": "Prioritize concrete bugs over style commentary.",
             "user_content": "List findings with file/line evidence, ordered by severity."},
            {"id": "tests", "title": "Check test coverage and residual risk",
             "system_prompt": "Tie verification to the actual behavior under review.",
             "user_content": "Name the tests run, missing coverage, and any remaining risk."},
        ],
    },
    "documentation_writer": {
        "id": "documentation_writer",
        "label": "Documentation Writer",
        "description": "Turn implementation facts into concise user-facing documentation.",
        "steps": [
            {"id": "inventory", "title": "Inventory public capabilities",
             "system_prompt": "Extract public behavior and inputs before writing prose.",
             "user_content": "List commands, arguments, outputs, and safety guards."},
            {"id": "draft", "title": "Draft documentation",
             "system_prompt": "Write accurate docs without marketing padding.",
             "user_content": "Create concise usage docs with examples and constraints."},
            {"id": "verify", "title": "Verify against source",
             "system_prompt": "Check every claim against the implemented surface.",
             "user_content": "Flag stale, missing, or unsupported statements."},
        ],
    },
    "prompt_engineer": {
        "id": "prompt_engineer",
        "label": "Prompt Engineer",
        "description": "Audit and improve prompts with a deterministic quality rubric.",
        "steps": [
            {"id": "audit", "title": "Audit prompt weaknesses",
             "system_prompt": "Evaluate clarity, role, format, constraints, examples, and failure modes.",
             "user_content": "Score each prompt and list weaknesses by dimension."},
            {"id": "rewrite", "title": "Rewrite variants",
             "system_prompt": "Produce tighter variants that preserve the intended behavior.",
             "user_content": "Create direct, structured, and safety-forward prompt variants."},
            {"id": "rubric", "title": "Create evaluation rubric",
             "system_prompt": "Make prompt quality measurable.",
             "user_content": "Define pass/fail checks and scoring guidance."},
        ],
    },
}

DEFAULT_RULES = {
    "max_hunk_size": 10000,
    "protected_files": ["LICENSE.md", "setup_env.bat", ".gitignore", "requirements.txt"],
    "forbidden_patterns": ["sk-proj-", "ghp_", "password ="],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def tokens(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text or "")]


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def workspace_path(value: str, *, must_exist: bool = False) -> Path:
    if not value:
        raise ValueError("path is required")
    root = Path.cwd().resolve()
    path = (root / value).resolve()
    if not inside(root, path):
        raise ValueError("path must stay inside the workspace")
    if must_exist and not path.exists():
        raise FileNotFoundError(path)
    return path


def artifact_root() -> Path:
    # Generated session/flush state belongs to the toolkit, not the host project (which stays
    # ignorant of the sidecar). Inputs are still read from the work-target cwd via workspace_path().
    return suite_home() / "_artifacts" / "memory_workflow"


def slug(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", (value or "").strip()).strip("._")
    return safe or "default"


def session_dir(name: str, root: str = "") -> Path:
    base = workspace_path(root) if root else artifact_root() / "sessions"
    return base / slug(name or "default")


def session_paths(name: str, root: str = "") -> dict:
    d = session_dir(name, root)
    return {
        "dir": d,
        "metadata": d / "metadata.json",
        "memory": d / "memory.jsonl",
        "tasks": d / "tasks.json",
        "flush": d / "flush_summary.md",
    }


def read_text_sources(args: dict) -> tuple[str, list[dict]]:
    chunks = []
    sources = []
    if args.get("text") is not None:
        text = str(args.get("text") or "")
        chunks.append(text)
        sources.append({"source": "inline", "chars": len(text)})
    paths = []
    if args.get("path"):
        paths.append(str(args["path"]))
    for raw in args.get("paths") or []:
        paths.append(str(raw))
    for raw in paths:
        path = workspace_path(raw, must_exist=True)
        if not path.is_file():
            raise ValueError(f"path is not a file: {path}")
        text = path.read_text(encoding="utf-8", errors="replace")
        chunks.append(text)
        sources.append({"source": path.relative_to(Path.cwd()).as_posix(), "chars": len(text)})
    return "\n\n".join(chunks), sources


def chunk_text(text: str, filename: str = "", *, chunk_size: int = 1500, overlap: int = 0) -> list[dict]:
    filename = filename or "inline.txt"
    if filename.endswith(".py"):
        py_chunks = _chunk_python(text, filename)
        if py_chunks:
            return py_chunks
    if filename.lower().endswith((".md", ".markdown", ".rst")):
        md_chunks = _chunk_markdown(text, filename)
        if md_chunks:
            return md_chunks
    return _chunk_windows(text, filename, chunk_size=max(100, int(chunk_size or 1500)),
                          overlap=max(0, int(overlap or 0)))


def _chunk_python(source: str, filename: str) -> list[dict]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    lines = source.splitlines()
    rows = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        start = int(getattr(node, "lineno", 1))
        end = int(getattr(node, "end_lineno", start))
        content = "\n".join(lines[start - 1:end])
        kind = "class" if isinstance(node, ast.ClassDef) else "function"
        rows.append(_chunk_row(filename, f"{kind} {node.name}", kind, content, start, end, len(rows)))
    return rows


def _chunk_markdown(text: str, filename: str) -> list[dict]:
    lines = text.splitlines()
    starts = []
    for idx, line in enumerate(lines, start=1):
        if re.match(r"^#{1,6}\s+\S", line):
            starts.append(idx)
    if not starts:
        return []
    rows = []
    for pos, start in enumerate(starts):
        end = (starts[pos + 1] - 1) if pos + 1 < len(starts) else len(lines)
        title = lines[start - 1].strip("# ").strip() or f"Section {pos + 1}"
        content = "\n".join(lines[start - 1:end])
        rows.append(_chunk_row(filename, title, "section", content, start, end, pos))
    return rows


def _chunk_windows(text: str, filename: str, *, chunk_size: int, overlap: int) -> list[dict]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    rows = []
    current = []
    current_chars = 0
    start_line = 1
    idx = 0
    for line_no, line in enumerate(lines, start=1):
        current.append(line)
        current_chars += len(line) + 1
        if current_chars >= chunk_size:
            rows.append(_chunk_row(filename, f"Chunk {idx + 1}", "text_block",
                                   "\n".join(current), start_line, line_no, idx))
            idx += 1
            if overlap > 0:
                carry = "\n".join(current)[-overlap:].splitlines()
                current = carry
                current_chars = sum(len(x) + 1 for x in current)
                start_line = max(start_line, line_no - len(current) + 1)
            else:
                current = []
                current_chars = 0
                start_line = line_no + 1
    if current:
        rows.append(_chunk_row(filename, f"Chunk {idx + 1}", "text_block",
                               "\n".join(current), start_line, len(lines), idx))
    return rows


def _chunk_row(source: str, name: str, kind: str, content: str, start: int, end: int, idx: int) -> dict:
    row = {
        "id": hashlib.sha1(f"{source}:{start}:{end}:{content}".encode("utf-8")).hexdigest()[:16],
        "source": source,
        "name": name,
        "type": kind,
        "content": content,
        "start_line": start,
        "end_line": end,
        "index": idx,
        "tokens": len(tokens(content)),
    }
    row["fingerprint"] = fingerprint({"source": source, "start": start, "end": end, "content": content})[:24]
    return row


def chunks_from_args(args: dict) -> tuple[list[dict], list[dict]]:
    if isinstance(args.get("chunks"), list):
        return [dict(c) for c in args["chunks"]], [{"source": "chunks", "chunks": len(args["chunks"])}]
    if args.get("chunks_path"):
        path = workspace_path(str(args["chunks_path"]), must_exist=True)
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data.get("chunks", data) if isinstance(data, dict) else data
        return [dict(c) for c in rows], [{"source": path.relative_to(Path.cwd()).as_posix(), "chunks": len(rows)}]
    text, sources = read_text_sources(args)
    filename = str(args.get("filename") or (sources[0]["source"] if sources else "inline.txt"))
    rows = chunk_text(text, filename, chunk_size=int(args.get("chunk_size", 1500)),
                      overlap=int(args.get("overlap", 0)))
    return rows, sources


def retrieve(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    q = Counter(tokens(query))
    scored = []
    for c in chunks:
        body = c.get("content", "")
        ct = Counter(tokens(body))
        lexical = sum(min(q[t], ct[t]) for t in q)
        if lexical == 0:
            continue
        denom = max(1, len(q) + len(ct))
        score = lexical / denom
        item = {k: v for k, v in c.items() if k != "content"}
        item["score"] = round(score, 6)
        item["preview"] = re.sub(r"\s+", " ", body).strip()[:240]
        scored.append(item)
    scored.sort(key=lambda r: (-r["score"], r.get("source", ""), r.get("start_line", 0)))
    return scored[:max(1, min(int(top_k or 5), 50))]


def format_context(results: list[dict], chunks: list[dict]) -> str:
    by_id = {c.get("id"): c for c in chunks}
    lines = ["### RETRIEVED CONTEXT ###"]
    for idx, item in enumerate(results, start=1):
        full = by_id.get(item.get("id"), {})
        label = f"[{idx}] {item.get('source', 'unknown')}:{item.get('start_line', '?')}-{item.get('end_line', '?')}"
        if item.get("name"):
            label += f" ({item['name']})"
        lines.append(label)
        lines.append(str(full.get("content") or item.get("preview") or "").strip())
        lines.append("")
    return "\n".join(lines).rstrip()


def decompose(goal: str, text: str = "", template: dict | None = None, max_steps: int = 8) -> list[dict]:
    rows = []
    if template:
        for step in template.get("steps", []):
            rows.append(dict(step))
    for line in (text or "").splitlines():
        m = TASK_RE.match(line)
        if m:
            rows.append({"title": m.group("text").strip()})
    if not rows and goal:
        parts = [p.strip() for p in re.split(r"\b(?:then|and then|;)\b", goal) if p.strip()]
        for part in parts or [goal]:
            rows.append({"title": part})
    normalized = []
    prev = None
    for idx, row in enumerate(rows[:max(1, min(int(max_steps or 8), 30))], start=1):
        sid = slug(row.get("id") or f"step_{idx}")
        item = {
            "id": sid,
            "title": row.get("title") or row.get("label") or f"Step {idx}",
            "system_prompt": row.get("system_prompt", "Complete this workflow step carefully."),
            "user_content": row.get("user_content") or row.get("title") or goal,
            "depends_on": [prev] if prev else [],
        }
        normalized.append(item)
        prev = sid
    return normalized


def load_template(template_id: str = "", path: str = "") -> dict:
    if path:
        p = workspace_path(path, must_exist=True)
        return json.loads(p.read_text(encoding="utf-8"))
    tid = template_id or "code_review"
    if tid not in BUILTIN_TEMPLATES:
        raise KeyError(f"unknown template: {tid}")
    return json.loads(json.dumps(BUILTIN_TEMPLATES[tid]))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def ensure_session(name: str, description: str = "", root: str = "") -> dict:
    paths = session_paths(name, root)
    meta = {
        "name": slug(name or "default"),
        "description": description,
        "created_at": utc_now(),
        "memory_path": paths["memory"].as_posix(),
        "task_path": paths["tasks"].as_posix(),
    }
    if paths["metadata"].exists():
        old = json.loads(paths["metadata"].read_text(encoding="utf-8"))
        old.setdefault("created_at", meta["created_at"])
        old.setdefault("memory_path", meta["memory_path"])
        old.setdefault("task_path", meta["task_path"])
        if description:
            old["description"] = description
        meta = old
    write_json(paths["metadata"], meta)
    if not paths["tasks"].exists():
        write_json(paths["tasks"], [])
    return meta


def session_status(name: str, root: str = "") -> dict:
    paths = session_paths(name, root)
    events = read_jsonl(paths["memory"])
    meta = json.loads(paths["metadata"].read_text(encoding="utf-8")) if paths["metadata"].exists() else {}
    return {
        "session": slug(name or "default"),
        "exists": paths["metadata"].exists(),
        "path": paths["dir"].as_posix(),
        "events": len(events),
        "roles": dict(Counter(str(e.get("role", "")) for e in events)),
        "kinds": dict(Counter(str(e.get("kind", "message")) for e in events)),
        "metadata": meta,
    }


def evaluate_rules(path: str = "", content: str = "", rules: dict | None = None) -> dict:
    active = dict(DEFAULT_RULES)
    active.update(rules or {})
    violations = []
    if path:
        norm = path.replace("\\", "/")
        for protected in active.get("protected_files", []):
            if protected and protected.replace("\\", "/") in norm:
                violations.append({"rule": "protected_file", "pattern": protected,
                                   "message": f"Path is protected by rule: {protected}"})
    if len(content or "") > int(active.get("max_hunk_size", 99999)):
        violations.append({"rule": "max_hunk_size", "limit": active.get("max_hunk_size"),
                           "message": "Content exceeds max_hunk_size"})
    for pattern in active.get("forbidden_patterns", []):
        if pattern and pattern in (content or ""):
            violations.append({"rule": "forbidden_pattern", "pattern": pattern,
                               "message": f"Content contains forbidden pattern: {pattern}"})
    return {"rules": active, "violations": violations, "allowed": not violations}


def summarize_events(events: list[dict], limit: int = 12) -> dict:
    role_counts = Counter(str(e.get("role", "")) for e in events)
    kind_counts = Counter(str(e.get("kind", "message")) for e in events)
    terms = Counter()
    for event in events:
        terms.update(t for t in tokens(str(event.get("content", ""))) if len(t) > 4)
    highlights = []
    for event in events[-max(1, int(limit or 12)):]:
        text = re.sub(r"\s+", " ", str(event.get("content", ""))).strip()
        highlights.append({"at": event.get("at"), "role": event.get("role"),
                           "kind": event.get("kind", "message"), "preview": text[:180]})
    return {
        "events": len(events),
        "roles": dict(role_counts),
        "kinds": dict(kind_counts),
        "top_terms": [t for t, _ in terms.most_common(12)],
        "highlights": highlights,
    }
