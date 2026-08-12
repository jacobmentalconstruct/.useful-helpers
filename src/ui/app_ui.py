"""
FILE:       src/ui/app_ui.py
ROLE:       Human entrance  -  registry-driven Tk main window (supersedes the old menu).
DOMAIN:     ui
DOES:       run(): build the Tk root (THEME_SPEC styling), mount the registry view, mainloop.
            run_probe(): bounded headless-ish verification  -  build the full UI, drive one
            governed invoke() through the view, pump a few update cycles, tear down. No
            mainloop, so it terminates deterministically (smoke/CI safe).
DEPENDS ON: src.ui.registry_view, src.lib.theme, (stdlib) tkinter, json
WIRES TO:   registry_view -> core.invoke (the one governed seam)
NOTES:      "Dumb shell" pattern: no business logic here. This window only hosts views
            and routes their calls through the governed seam.

"""
from __future__ import annotations

import json


def _build_root(paths):
    import tkinter as tk

    from src.lib import theme
    from src.ui import registry_view

    root = tk.Tk()
    root.title("Useful Helpers  -  Suite Control Panel")
    root.geometry("1100x720")
    theme.apply_style(root)
    view = registry_view.build(root, paths)
    return root, view


def run(paths) -> int:
    """Launch the registry-driven control panel (blocks in mainloop)."""
    root, _view = _build_root(paths)
    root.mainloop()
    return 0


def run_probe(paths, tool_id: str = "ping", args_json: str = "", cycles: int = 5) -> int:
    """Build the real UI, run one tool through the view synchronously, pump, tear down.
    Prints a one-line JSON verdict; exit 0 iff the UI built and the call succeeded."""
    args = json.loads(args_json) if args_json.strip() else {"message": "ui-probe"}
    root, view = _build_root(paths)
    try:
        tool_count = sum(1 for iid in _iter_tree(view.tree) if iid in view.tools)
        result = view.run_tool_sync(tool_id, args)
        for _ in range(max(1, cycles)):
            root.update()
        verdict = {"ok": bool(result.ok), "tool": tool_id,
                   "tools_rendered": tool_count, "error": result.error}
    finally:
        root.destroy()
    print(json.dumps(verdict))
    return 0 if verdict["ok"] else 1


def _iter_tree(tree, parent=""):
    for iid in tree.get_children(parent):
        yield iid
        yield from _iter_tree(tree, iid)


# --- Operator view: Project Snapshot (projectmapper front-end) ----------

def _build_mapper_root(paths):
    import tkinter as tk

    from src.lib import theme
    from src.ui import mapper_view

    root = tk.Tk()
    root.title("Useful Helpers  -  Project Snapshot")
    root.geometry("760x820")
    theme.apply_style(root)
    view = mapper_view.build(root, paths)
    return root, view


def run_mapper(paths) -> int:
    """Launch the compact project-snapshot window (blocks in mainloop)."""
    root, _view = _build_mapper_root(paths)
    root.mainloop()
    return 0


def _build_planner_root(paths):
    import tkinter as tk

    from src.lib import theme
    from src.ui import planner_view

    root = tk.Tk()
    root.title("Useful Helpers  -  Plan a new project")
    root.geometry("760x760")
    theme.apply_style(root)
    view = planner_view.build(root, paths)
    return root, view


def run_planner(paths) -> int:
    """Launch the project-planner cockpit (blocks in mainloop)."""
    root, _view = _build_planner_root(paths)
    root.mainloop()
    return 0


def run_planner_probe(paths, cycles: int = 3) -> int:
    """Build the real planner window, run one `plan propose` through it, pump, tear down.
    Uses an archetype so it is deterministic and needs no model. Mainloop-free (CI safe)."""
    root, view = _build_planner_root(paths)
    try:
        view.intent.insert("end", "a small tool")
        view.name_var.set("probe-proj")
        result = view.run_sync({"action": "propose", "intent": "a small tool",
                                "name": "probe-proj", "archetype": "python-cli"})
        for _ in range(max(1, cycles)):
            root.update()
        o = result.output or {}
        verdict = {"ok": bool(result.ok), "tool": "plan",
                   "proposed": bool(o.get("map")), "error": result.error}
    finally:
        root.destroy()
    print(json.dumps(verdict))
    return 0 if verdict["ok"] else 1


def run_mapper_probe(paths, root_dir: str = ".", markdown: bool = False,
                     save_to: str = "", cycles: int = 3) -> int:
    """Build the real mapper window, run one snapshot through it, pump, tear down.
    Prints a one-line JSON verdict; exit 0 iff the UI built and the snapshot succeeded."""
    args = {"action": "compile", "root": root_dir, "name": "probe_snapshot"}
    if markdown:
        args["markdown"] = True
    if save_to:
        args["out"] = f"{save_to}/probe_snapshot_snapshot.sqlite3"
    root, view = _build_mapper_root(paths)
    try:
        result = view.run_generate_sync(args)
        for _ in range(max(1, cycles)):
            root.update()
        o = result.output or {}
        verdict = {"ok": bool(result.ok), "tool": "projectmapper",
                   "file_count": o.get("file_count"), "error": result.error}
    finally:
        root.destroy()
    print(json.dumps(verdict))
    return 0 if verdict["ok"] else 1
