"""
FILE:       tools/packaging_more_shared.py
ROLE:       Shared helpers for T-packaging-more.
DOMAIN:     tool
DOES:       Builds codebase bundles, static project viewers, and starter app skeletons.
DEPENDS ON: (stdlib) ast, datetime, hashlib, html, json, mimetypes, pathlib, re
WIRES TO:   tempserver, codebase_bundle, app_factory
NOTES:      Deterministic, workspace-local packaging helpers.
"""
from __future__ import annotations

import ast
import hashlib
import html
import json
import mimetypes
import re
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".mypy_cache",
             ".pytest_cache", ".ruff_cache"}
TEXT_EXTS = {".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".css", ".html",
             ".htm", ".js", ".ts", ".bat", ".ps1", ".sh", ".cfg", ".ini", ".csv"}

APP_TEMPLATES = {
    "headless_cli": {
        "label": "Headless CLI",
        "description": "Small argparse-style Python app with health and run commands.",
        "files": ["app.py", "settings.json", "README.md", "smoke_test.py"],
    },
    "tkinter_shell": {
        "label": "Tkinter Shell",
        "description": "Tiny Tkinter launcher with a no-ui health path.",
        "files": ["app.py", "ui.py", "settings.json", "README.md", "smoke_test.py"],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def workspace_path(value: str, *, default: str = ".", must_exist: bool = False) -> Path:
    raw = value or default
    root = Path.cwd().resolve()
    path = (root / raw).resolve()
    if not inside(root, path):
        raise ValueError("path must stay inside the workspace")
    if must_exist and not path.exists():
        raise FileNotFoundError(path)
    return path


def slug(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", (value or "").strip()).strip("._")
    return safe or "bundle"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def guess_lang(path: Path) -> str:
    mt = mimetypes.guess_type(str(path))[0] or ""
    ext = path.suffix.lower()
    if ext == ".py":
        return "python"
    if ext in {".js", ".mjs", ".cjs"}:
        return "javascript"
    if ext == ".ts":
        return "typescript"
    if ext == ".json":
        return "json"
    if ext == ".css":
        return "css"
    if ext in {".html", ".htm"}:
        return "html"
    if ext in TEXT_EXTS or mt.startswith("text/"):
        return "text"
    return "binary"


def iter_files(root: Path, *, include: list[str] | None = None, exclude: list[str] | None = None,
               limit: int = 500) -> list[Path]:
    include = include or ["*"]
    exclude = exclude or []
    rows = []
    for path in sorted(root.rglob("*")):
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        rel = path.relative_to(root).as_posix()
        if path.is_dir():
            continue
        if exclude and any(path.match(pat) or rel == pat or rel.startswith(pat.rstrip("/") + "/") for pat in exclude):
            continue
        if not any(path.match(pat) or rel == pat or rel.startswith(pat.rstrip("/") + "/") for pat in include):
            continue
        rows.append(path)
        if len(rows) >= max(1, int(limit or 500)):
            break
    return rows


def file_record(root: Path, path: Path, *, max_bytes: int, include_binaries: bool) -> dict:
    raw = path.read_bytes()
    rel = path.relative_to(root).as_posix()
    lang = guess_lang(path)
    row = {
        "path": rel,
        "size": len(raw),
        "sha256": sha256_bytes(raw),
        "language": lang,
    }
    if lang == "binary" and not include_binaries:
        row["skipped"] = "binary"
        return row
    text = raw.decode("utf-8", errors="replace")
    encoded = text.encode("utf-8")
    row["truncated"] = bool(max_bytes and len(encoded) > max_bytes)
    if row["truncated"]:
        text = text[:max_bytes]
    row["content"] = text
    return row


def build_records(root: Path, *, max_bytes: int = 20000, include_binaries: bool = False,
                  include: list[str] | None = None, exclude: list[str] | None = None,
                  limit: int = 500) -> tuple[dict, list[dict]]:
    files = iter_files(root, include=include, exclude=exclude, limit=limit)
    records = [file_record(root, p, max_bytes=max_bytes, include_binaries=include_binaries) for p in files]
    meta = {
        "root": root.as_posix(),
        "generated_at": utc_now(),
        "file_count": len(records),
        "total_bytes": sum(r.get("size", 0) for r in records),
        "truncated_files": sum(1 for r in records if r.get("truncated")),
        "binary_skipped": sum(1 for r in records if r.get("skipped") == "binary"),
    }
    return meta, records


def jsonl_bundle(meta: dict, records: list[dict]) -> str:
    lines = [json.dumps({"type": "meta", **meta}, separators=(",", ":"))]
    lines.append(json.dumps({"type": "section", "name": "files"}, separators=(",", ":")))
    for row in records:
        lines.append(json.dumps({"type": "file", **row}, ensure_ascii=False, separators=(",", ":")))
    return "\n".join(lines) + "\n"


def ai_report(meta: dict, records: list[dict]) -> str:
    lines = [
        "# Codebase Bundle",
        "",
        f"- Root: {meta['root']}",
        f"- Generated: {meta['generated_at']}",
        f"- Files: {meta['file_count']}",
        f"- Bytes: {meta['total_bytes']}",
        "",
    ]
    for row in records:
        lines.append(f"## {row['path']}")
        lines.append(f"- language: {row['language']}")
        lines.append(f"- sha256: {row['sha256']}")
        if row.get("skipped"):
            lines.append(f"- skipped: {row['skipped']}")
            lines.append("")
            continue
        lines.append("")
        lines.append("```" + row["language"])
        lines.append(row.get("content", ""))
        lines.append("```")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def ast_jsonl(root: Path, records: list[dict]) -> str:
    lines = [json.dumps({"type": "meta", "root": root.as_posix(), "generated_at": utc_now(),
                         "scope": "*.py"}, separators=(",", ":"))]
    for row in records:
        if row.get("language") != "python" or "content" not in row:
            continue
        lines.append(json.dumps({"type": "ast_file", "path": row["path"]}, separators=(",", ":")))
        try:
            tree = ast.parse(row["content"])
        except Exception as exc:
            lines.append(json.dumps({"type": "ast_error", "path": row["path"], "error": str(exc)},
                                    separators=(",", ":")))
            continue
        for node in ast.walk(tree):
            item = {"type": "ast_node", "path": row["path"], "node": type(node).__name__}
            for attr in ("name", "id", "arg", "attr"):
                if hasattr(node, attr):
                    item["name"] = getattr(node, attr)
                    break
            if hasattr(node, "lineno"):
                item["lineno"] = getattr(node, "lineno")
            if hasattr(node, "end_lineno"):
                item["end_lineno"] = getattr(node, "end_lineno")
            lines.append(json.dumps(item, separators=(",", ":")))
    return "\n".join(lines) + "\n"


def viewer_html(meta: dict, records: list[dict]) -> str:
    files_json = json.dumps(records, ensure_ascii=False)
    meta_json = json.dumps(meta, ensure_ascii=False)
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Temp Project Viewer</title>
  <style>
    body {{ margin: 0; font: 14px system-ui, sans-serif; color: #172033; background: #f7f9fc; }}
    header {{ padding: 12px 16px; background: #10233f; color: white; }}
    main {{ display: grid; grid-template-columns: 320px 1fr; min-height: calc(100vh - 52px); }}
    aside {{ border-right: 1px solid #d8e0ea; background: white; overflow: auto; }}
    button {{ width: 100%; text-align: left; border: 0; background: transparent; padding: 7px 12px; cursor: pointer; }}
    button:hover {{ background: #edf4ff; }}
    pre {{ margin: 0; padding: 16px; white-space: pre-wrap; overflow: auto; }}
    .meta {{ color: #57708f; padding: 10px 12px; border-bottom: 1px solid #d8e0ea; }}
  </style>
</head>
<body>
<header><strong>Temp Project Viewer</strong> <span id="summary"></span></header>
<main>
  <aside><div class="meta" id="meta"></div><div id="files"></div></aside>
  <section><pre id="viewer">Select a file.</pre></section>
</main>
<script type="application/json" id="meta-json">{html.escape(meta_json)}</script>
<script type="application/json" id="files-json">{html.escape(files_json)}</script>
<script>
const meta = JSON.parse(document.getElementById('meta-json').textContent);
const files = JSON.parse(document.getElementById('files-json').textContent);
document.getElementById('summary').textContent = `- ${{meta.file_count}} files / ${{meta.total_bytes}} bytes`;
document.getElementById('meta').textContent = `${{meta.root}}`;
const list = document.getElementById('files');
const viewer = document.getElementById('viewer');
for (const file of files) {{
  const btn = document.createElement('button');
  btn.textContent = file.path;
  btn.onclick = () => {{
    viewer.textContent = file.content || `[${{file.language}} skipped: ${{file.skipped || 'no text content'}}]`;
  }};
  list.appendChild(btn);
}}
</script>
</body>
</html>
"""


def write_outputs(out_dir: Path, outputs: dict[str, str], *, overwrite: bool = False) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, content in outputs.items():
        path = out_dir / name
        if path.exists() and not overwrite:
            raise FileExistsError(f"output exists: {path}")
        path.write_text(content, encoding="utf-8")
        written.append({"path": path.as_posix(), "bytes": path.stat().st_size})
    return written


def app_template_files(template_id: str, name: str) -> dict[str, str]:
    app_name = name or "Stamped App"
    package_name = slug(app_name).lower()
    if template_id not in APP_TEMPLATES:
        raise KeyError(f"unknown template: {template_id}")
    common = {
        "settings.json": json.dumps({"app_title": app_name, "created_at": utc_now()}, indent=2) + "\n",
        "README.md": f"# {app_name}\n\nStamped by Useful Helpers Suite `app_factory`.\n\n",
        "smoke_test.py": "import subprocess\nimport sys\n\n\ndef test_health():\n    r = subprocess.run([sys.executable, 'app.py', '--health'], text=True, capture_output=True)\n    assert r.returncode == 0\n    assert 'ok' in r.stdout.lower()\n",
        "app_manifest.json": json.dumps({
            "app_id": "app_" + hashlib.sha1(app_name.encode("utf-8")).hexdigest()[:24],
            "name": app_name,
            "template": template_id,
            "package_name": package_name,
            "created_at": utc_now(),
        }, indent=2) + "\n",
    }
    if template_id == "headless_cli":
        common["app.py"] = (
            "import argparse\nimport json\nfrom pathlib import Path\n\n"
            "def health():\n    return {'ok': True, 'app': Path.cwd().name}\n\n"
            "def main():\n    parser = argparse.ArgumentParser()\n    parser.add_argument('--health', action='store_true')\n    parser.add_argument('--message', default='hello')\n    args = parser.parse_args()\n    if args.health:\n        print(json.dumps(health()))\n    else:\n        print(args.message)\n\n"
            "if __name__ == '__main__':\n    main()\n"
        )
    else:
        common["app.py"] = (
            "import argparse\nimport json\n\n"
            "def main():\n    parser = argparse.ArgumentParser()\n    parser.add_argument('--health', action='store_true')\n    parser.add_argument('--no-ui', action='store_true')\n    args = parser.parse_args()\n    if args.health or args.no_ui:\n        print(json.dumps({'ok': True, 'ui': not args.no_ui}))\n        return\n    from ui import launch\n    launch()\n\n"
            "if __name__ == '__main__':\n    main()\n"
        )
        common["ui.py"] = (
            "import tkinter as tk\n\n"
            "def launch():\n    root = tk.Tk()\n    root.title('Stamped App')\n    tk.Label(root, text='Stamped App').pack(padx=24, pady=24)\n    root.mainloop()\n"
        )
    return common


def plan_app(destination: Path, template_id: str, name: str) -> tuple[dict, list[dict], dict[str, str]]:
    files = app_template_files(template_id, name)
    planned = []
    for rel, content in sorted(files.items()):
        path = destination / rel
        planned.append({"path": path.as_posix(), "exists": path.exists(), "bytes": len(content.encode("utf-8"))})
    manifest = json.loads(files["app_manifest.json"])
    manifest["destination"] = destination.as_posix()
    return manifest, planned, files
