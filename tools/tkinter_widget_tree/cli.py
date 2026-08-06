"""
FILE:       tools/tkinter_widget_tree/cli.py
ROLE:       Tkinter/ttk widget tree extractor.
DOMAIN:     tool
DOES:       Parses Python files, detects Tk roots/widgets/layout/config/command/bind calls,
            and returns a conservative UI structure map without launching the UI.
DEPENDS ON: tools._toolkit, tools.code_intel_shared, (stdlib) ast
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Static AST walk of Tk widget construction; no GUI is launched.
"""
from __future__ import annotations

import ast
from collections import Counter

from tools._toolkit import tool_main
from tools.code_intel_shared import expr_to_str, parse_python_files, resolve_root

ROOT_NAMES = {"Tk"}
LAYOUT_METHODS = {"pack", "grid", "place"}
CONFIG_METHODS = {"config", "configure"}
MENU_METHODS = {"add_command", "add_separator", "add_cascade"}
WIDGET_NAMES = {
    "Frame", "Label", "Button", "Entry", "Text", "Canvas", "Menu", "Scrollbar",
    "Listbox", "Toplevel", "Checkbutton", "Radiobutton", "Spinbox", "Scale",
    "PanedWindow", "LabelFrame", "Message", "Combobox", "Treeview", "Notebook",
    "Separator", "Progressbar",
}


class TkVisitor(ast.NodeVisitor):
    def __init__(self, path: str):
        self.path = path
        self.var_to_id: dict[str, str] = {}
        self.windows: list[dict] = []
        self.widgets: list[dict] = []
        self._seq = 0

    def _id(self, prefix: str) -> str:
        self._seq += 1
        return f"{self.path}:{prefix}{self._seq}"

    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.value, ast.Call):
            call = node.value
            if self._is_root(call):
                wid = self._id("win")
                row = {"id": wid, "path": self.path, "line": _line(node), "kind": "window",
                       "type": expr_to_str(call.func), "titles": [], "geometry": [], "config": []}
                self.windows.append(row)
                self._assign_targets(node.targets, wid)
            else:
                widget_type = self._widget_type(call)
                if widget_type:
                    wid = self._id("w")
                    parent_expr = expr_to_str(call.args[0]) if call.args else ""
                    parent_id = self.var_to_id.get(parent_expr, "")
                    kwargs = _kwargs(call)
                    row = {"id": wid, "path": self.path, "line": _line(node), "kind": "widget",
                           "type": widget_type, "parent_expr": parent_expr, "parent_id": parent_id,
                           "kwargs": kwargs, "layout": [], "config": [], "commands": [], "binds": []}
                    if "command" in kwargs:
                        row["commands"].append(kwargs["command"])
                    self.widgets.append(row)
                    self._assign_targets(node.targets, wid)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute):
            receiver = expr_to_str(node.func.value)
            recv_id = self.var_to_id.get(receiver, "")
            method = node.func.attr
            sig = _call_sig(node)
            if recv_id:
                target = self._find(recv_id)
                if target:
                    if method in LAYOUT_METHODS and target.get("kind") == "widget":
                        target["layout"].append(f"{method}({sig})")
                    elif method in CONFIG_METHODS:
                        target["config"].append(f"{method}({sig})")
                    elif method == "bind" and target.get("kind") == "widget":
                        target["binds"].append(sig)
                    elif method == "title" and target.get("kind") == "window":
                        target["titles"].append(sig)
                    elif method == "geometry" and target.get("kind") == "window":
                        target["geometry"].append(sig)
                    elif method in MENU_METHODS and target.get("kind") == "widget":
                        target.setdefault("menu_methods", []).append(f"{method}({sig})")
                        for kw in node.keywords:
                            if kw.arg == "command":
                                target["commands"].append(expr_to_str(kw.value))
        self.generic_visit(node)

    def _assign_targets(self, targets: list[ast.expr], value_id: str) -> None:
        for target in targets:
            if isinstance(target, ast.Name):
                self.var_to_id[target.id] = value_id
            elif isinstance(target, ast.Attribute):
                self.var_to_id[expr_to_str(target)] = value_id

    def _find(self, item_id: str) -> dict | None:
        for row in self.windows:
            if row["id"] == item_id:
                return row
        for row in self.widgets:
            if row["id"] == item_id:
                return row
        return None

    def _is_root(self, call: ast.Call) -> bool:
        fn = call.func
        if isinstance(fn, ast.Attribute) and fn.attr in ROOT_NAMES:
            return True
        if isinstance(fn, ast.Name) and fn.id in ROOT_NAMES:
            return True
        return False

    def _widget_type(self, call: ast.Call) -> str:
        fn = call.func
        if isinstance(fn, ast.Attribute) and fn.attr in WIDGET_NAMES:
            return fn.attr
        if isinstance(fn, ast.Name) and fn.id in WIDGET_NAMES:
            return fn.id
        return ""


def _line(node: ast.AST) -> int:
    return int(getattr(node, "lineno", 1) or 1)


def _kwargs(call: ast.Call) -> dict[str, str]:
    return {kw.arg: expr_to_str(kw.value) for kw in call.keywords if kw.arg}


def _call_sig(call: ast.Call) -> str:
    parts = [expr_to_str(arg) for arg in call.args]
    parts.extend(f"{kw.arg}={expr_to_str(kw.value)}" for kw in call.keywords if kw.arg)
    return ", ".join(parts)


@tool_main
def run(args: dict) -> dict:
    root, error = resolve_root(args.get("root"))
    if error:
        return {"ok": False, "error": error}
    assert root is not None

    max_files = max(1, min(int(args.get("max_files", 500)), 5000))
    parsed = parse_python_files(root, max_files=max_files)

    windows = []
    widgets = []
    for p in parsed:
        if p.tree is None:
            continue
        visitor = TkVisitor(p.rel)
        visitor.visit(p.tree)
        windows.extend(visitor.windows)
        widgets.extend(visitor.widgets)

    widget_types = Counter(w["type"] for w in widgets)
    parse_errors = [{"path": p.rel, "error": p.error} for p in parsed if p.error]
    return {
        "tool": "tkinter_widget_tree",
        "root": root.as_posix(),
        "file_count": len(parsed),
        "window_count": len(windows),
        "widget_count": len(widgets),
        "windows": windows,
        "widgets": widgets,
        "widget_types": dict(sorted(widget_types.items())),
        "parse_errors": parse_errors,
        "truncated": len(parsed) >= max_files,
        "summary": {
            "files": len(parsed),
            "windows": len(windows),
            "widgets": len(widgets),
            "widget_types": len(widget_types),
            "parse_errors": len(parse_errors),
        },
    }

