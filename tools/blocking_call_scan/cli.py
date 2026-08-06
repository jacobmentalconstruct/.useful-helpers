"""
FILE:       tools/blocking_call_scan/cli.py
ROLE:       Blocking-call scanner for Python code.
DOMAIN:     tool
DOES:       Finds likely synchronous sleeps, subprocess calls, network calls, and filesystem
            operations with line anchors and risk labels.
DEPENDS ON: tools._toolkit, tools.code_intel_shared, (stdlib) ast
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Read-only. Cannot yet distinguish sync from async context, so its output
            is a lead, not a verdict. See _design/CHARTER.md sec 4.
"""
from __future__ import annotations

import ast
from collections import Counter

from tools._toolkit import tool_main
from tools.code_intel_shared import call_name, parse_python_files, resolve_root

PATTERNS = {
    "sleep": {"time.sleep", "sleep"},
    "subprocess": {
        "subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_call",
        "subprocess.check_output", "os.system", "os.popen",
    },
    "network": {
        "requests.get", "requests.post", "requests.put", "requests.delete", "requests.request",
        "urllib.request.urlopen", "httpx.get", "httpx.post", "socket.socket",
    },
    "filesystem": {
        "open", "Path.read_text", "Path.read_bytes", "Path.write_text", "Path.write_bytes",
        "shutil.rmtree", "shutil.copy", "shutil.copytree",
    },
}


class ScanVisitor(ast.NodeVisitor):
    def __init__(self, path: str):
        self.path = path
        self.context: list[tuple[str, str]] = []
        self.findings: list[dict] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.context.append(("function", node.name))
        self.generic_visit(node)
        self.context.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.context.append(("async_function", node.name))
        self.generic_visit(node)
        self.context.pop()

    def visit_Call(self, node: ast.Call) -> None:
        name = call_name(node)
        for category, names in PATTERNS.items():
            matched = ""
            if name in names:
                matched = name
            elif any(name.endswith(f".{candidate}") for candidate in names if "." not in candidate):
                matched = name
            if not matched:
                continue
            # Only the NEAREST enclosing function determines event-loop exposure: a blocking
            # call in a sync helper nested inside an async def does not stall the loop.
            in_async = bool(self.context) and self.context[-1][0] == "async_function"
            risk = ("high" if category in {"sleep", "subprocess", "network"} else "medium") \
                if in_async else "informational"
            self.findings.append({
                "path": self.path,
                "line": int(getattr(node, "lineno", 1) or 1),
                "call": name,
                "category": category,
                "context": ".".join(name for _, name in self.context) or "<module>",
                "async_context": in_async,
                "risk": risk,
            })
            break
        self.generic_visit(node)


@tool_main
def run(args: dict) -> dict:
    root, error = resolve_root(args.get("root"))
    if error:
        return {"ok": False, "error": error}
    assert root is not None

    max_files = max(1, min(int(args.get("max_files", 500)), 5000))
    limit = max(1, min(int(args.get("limit", 100)), 1000))
    parsed = parse_python_files(root, max_files=max_files)

    matches = []
    for p in parsed:
        if p.tree is None:
            continue
        visitor = ScanVisitor(p.rel)
        visitor.visit(p.tree)
        matches.extend(visitor.findings)

    # Split: only event-loop-exposed (async-context) calls are findings; the rest is context.
    findings = [m for m in matches if m["async_context"]]
    informational = [m for m in matches if not m["async_context"]]
    risk_rank = {"high": 3, "medium": 2, "low": 1}
    findings.sort(key=lambda r: (risk_rank.get(r["risk"], 0), r["category"], r["path"], -r["line"]),
                  reverse=True)
    by_category = Counter(f["category"] for f in findings)
    parse_errors = [{"path": p.rel, "error": p.error} for p in parsed if p.error]
    return {
        "tool": "blocking_call_scan",
        "root": root.as_posix(),
        "file_count": len(parsed),
        "finding_count": len(findings),
        "findings": findings[:limit],
        "informational_count": len(informational),
        "informational": informational[:limit],
        "by_category": dict(sorted(by_category.items())),
        "parse_errors": parse_errors,
        "truncated": len(parsed) >= max_files or len(matches) > limit,
        "warnings": [
            "Only blocking calls whose nearest enclosing function is `async def` are findings "
            "(they can stall the event loop). Sync-context calls are informational, not defects.",
        ],
        "summary": {
            "files": len(parsed),
            "findings": len(findings),
            "informational": len(informational),
            "returned": min(len(findings), limit),
            "parse_errors": len(parse_errors),
        },
    }

