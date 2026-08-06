"""
FILE:       tools/secret_audit/cli.py
ROLE:       Redacted secret surface scanner.
DOMAIN:     tool
DOES:       Scan text files for obvious committed secrets and return redacted findings.
DEPENDS ON: tools._toolkit, (stdlib) pathlib, re
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      A first-pass surface scan, not a proof of absence. High signal for triage.
"""
from __future__ import annotations

import re
from pathlib import Path

from tools._toolkit import tool_main

_PRUNE = {".git", ".venv", "node_modules", "__pycache__", "dist", "build"}
_PATTERNS = {
    "generic_assignment": re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"]?([A-Za-z0-9_\-./+=]{12,})"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


def _redact(text: str) -> str:
    if len(text) <= 8:
        return "<redacted>"
    return text[:4] + "<redacted>" + text[-4:]


def _textish(path: Path) -> bool:
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".sqlite3", ".db", ".pyc"}:
        return False
    try:
        return b"\x00" not in path.read_bytes()[:2048]
    except OSError:
        return False


@tool_main
def run(args: dict) -> dict:
    root = Path(args.get("root") or ".").resolve()
    project = Path.cwd().resolve()
    try:
        root.relative_to(project)
    except ValueError:
        return {"ok": False, "error": "root must stay inside the project workspace"}
    limit = max(1, min(int(args.get("limit", 100)), 1000))
    findings = []
    scanned = 0
    for path in root.rglob("*"):
        if len(findings) >= limit:
            break
        if any(part in _PRUNE for part in path.relative_to(root).parts):
            continue
        if not path.is_file() or not _textish(path):
            continue
        scanned += 1
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            for name, pattern in _PATTERNS.items():
                m = pattern.search(line)
                if not m:
                    continue
                secret = m.group(2) if name == "generic_assignment" and len(m.groups()) >= 2 else m.group(0)
                findings.append({"path": path.relative_to(root).as_posix(), "line": lineno,
                                 "kind": name, "preview": line.replace(secret, _redact(secret)).strip()[:240]})
                break
            if len(findings) >= limit:
                break
    return {"tool": "secret_audit", "root": root.as_posix(), "scanned_files": scanned,
            "finding_count": len(findings), "truncated": len(findings) >= limit,
            "findings": findings, "caveat": "heuristic scan; absence of findings is not proof of no secrets"}
