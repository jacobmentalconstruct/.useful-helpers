"""
FILE:       tools/ui_callback_graph/cli.py
ROLE:       Tkinter callback/call graph extractor.
DOMAIN:     tool
DOES:       Detects command=/bind callbacks and conservative intra-file function call edges
            for Python Tkinter code without launching any GUI.
DEPENDS ON: tools._toolkit, tools.code_intel_shared, (stdlib) ast
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Static callback-wiring extraction; no GUI is launched.
"""
from __future__ import annotations

import ast
from collections import defaultdict

from tools._toolkit import tool_main
from tools.code_intel_shared import CallCollector, expr_to_str, parse_python_files, resolve_root


class FunctionIndex(ast.NodeVisitor):
    def __init__(self, path: str):
        self.path = path
        self.class_stack: list[str] = []
        self.nodes: dict[str, ast.AST] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._add(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._add(node)
        self.generic_visit(node)

    def _add(self, node: ast.AST) -> None:
        name = str(getattr(node, "name", ""))
        qual = ".".join([*self.class_stack, name]) if self.class_stack else name
        self.nodes[f"{self.path}::{qual}"] = node


class CallbackVisitor(ast.NodeVisitor):
    def __init__(self, path: str):
        self.path = path
        self.var_to_widget: dict[str, str] = {}
        self.events: list[dict] = []
        self._seq = 0

    def _widget_id(self, typ: str, line: int) -> str:
        self._seq += 1
        return f"{self.path}:w{self._seq}:{typ}:L{line}"

    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.value, ast.Call):
            typ = _widget_type(node.value)
            if typ:
                wid = self._widget_id(typ, _line(node))
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.var_to_widget[target.id] = wid
                    elif isinstance(target, ast.Attribute):
                        self.var_to_widget[expr_to_str(target)] = wid
                for kw in node.value.keywords:
                    if kw.arg == "command":
                        self.events.append({"path": self.path, "line": _line(node),
                                            "widget": wid, "event": "command",
                                            "handler": expr_to_str(kw.value)})
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            receiver = expr_to_str(node.func.value)
            wid = self.var_to_widget.get(receiver, receiver)
            if method == "bind" and node.args:
                event = expr_to_str(node.args[0])
                handler = expr_to_str(node.args[1]) if len(node.args) > 1 else ""
                self.events.append({"path": self.path, "line": _line(node),
                                    "widget": wid, "event": event, "handler": handler})
            elif method in {"add_command", "add_cascade"}:
                for kw in node.keywords:
                    if kw.arg == "command":
                        self.events.append({"path": self.path, "line": _line(node),
                                            "widget": wid, "event": method,
                                            "handler": expr_to_str(kw.value)})
        self.generic_visit(node)


WIDGET_NAMES = {
    "Button", "Checkbutton", "Radiobutton", "Menu", "Combobox", "Treeview", "Entry",
    "Text", "Listbox", "Scale", "Spinbox",
}


def _line(node: ast.AST) -> int:
    return int(getattr(node, "lineno", 1) or 1)


def _widget_type(call: ast.Call) -> str:
    fn = call.func
    if isinstance(fn, ast.Attribute) and fn.attr in WIDGET_NAMES:
        return fn.attr
    if isinstance(fn, ast.Name) and fn.id in WIDGET_NAMES:
        return fn.id
    return ""


def _resolve_handler(handler: str, function_keys: set[str]) -> str:
    if not handler or handler == "lambda":
        return ""
    if handler.startswith("self."):
        tail = handler.split(".", 1)[1]
        matches = [k for k in function_keys if k.endswith(f".{tail}")]
        return matches[0] if len(matches) == 1 else ""
    tail = handler.split(".")[-1]
    matches = [k for k in function_keys if k.endswith(f"::{tail}") or k.endswith(f".{tail}")]
    return matches[0] if len(matches) == 1 else ""


def _resolve_call(call: str, function_keys: set[str]) -> str:
    return _resolve_handler(call, function_keys)


@tool_main
def run(args: dict) -> dict:
    root, error = resolve_root(args.get("root"))
    if error:
        return {"ok": False, "error": error}
    assert root is not None

    max_files = max(1, min(int(args.get("max_files", 500)), 5000))
    parsed = parse_python_files(root, max_files=max_files)

    functions: dict[str, ast.AST] = {}
    events = []
    for p in parsed:
        if p.tree is None:
            continue
        idx = FunctionIndex(p.rel)
        idx.visit(p.tree)
        functions.update(idx.nodes)
        cb = CallbackVisitor(p.rel)
        cb.visit(p.tree)
        events.extend(cb.events)

    function_keys = set(functions.keys())
    edges = []
    unresolved = []
    for event in events:
        target = _resolve_handler(event["handler"], function_keys)
        if target:
            edges.append({"from": f"event:{event['widget']}:{event['event']}",
                          "to": f"func:{target}", "kind": "event_to_handler", **event})
        else:
            unresolved.append(event)

    for fn_key, node in functions.items():
        calls = CallCollector()
        calls.visit(node)
        for call, line in calls.calls:
            dst = _resolve_call(call, function_keys)
            if dst and dst != fn_key:
                edges.append({"from": f"func:{fn_key}", "to": f"func:{dst}",
                              "kind": "calls", "path": fn_key.split("::", 1)[0],
                              "line": line, "call": call})

    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        adjacency[edge["from"]].append(edge["to"])

    parse_errors = [{"path": p.rel, "error": p.error} for p in parsed if p.error]
    return {
        "tool": "ui_callback_graph",
        "root": root.as_posix(),
        "event_count": len(events),
        "function_count": len(functions),
        "edge_count": len(edges),
        "events": events,
        "edges": edges,
        "unresolved_events": unresolved,
        "adjacency": dict(sorted(adjacency.items())),
        "parse_errors": parse_errors,
        "truncated": len(parsed) >= max_files,
        "summary": {
            "files": len(parsed),
            "events": len(events),
            "functions": len(functions),
            "edges": len(edges),
            "unresolved_events": len(unresolved),
            "parse_errors": len(parse_errors),
        },
    }

