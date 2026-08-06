"""
FILE:       src/ui/planner_view.py
ROLE:       Human "cockpit" - plan a NEW project from an intention, curate it, and build it.
DOMAIN:     ui
DOES:       Intent -> Propose (draft an editable project map via the planner engine) -> Preview
            (dry-run the whole plan) -> Build (materialize as one resumable operation). Every call
            crosses the one governed core.invoke() seam on a worker thread (the `plan` tool is
            Apply -> authority-checked + audit-logged); Preview writes nothing, Build confirms.
DEPENDS ON: src.core.invoke, src.lib.theme, (stdlib) json, os, queue, sys, threading, tkinter
WIRES TO:   core.invoke -> tools/plan (the E6 engine; genesis+scaffold+provenance+journal beneath).
NOTES:      "Dumb shell" - no planning or build logic here; the `plan` tool owns all of it. The map
            box is EDITABLE JSON so the human curates the proposed structure before anything is
            built. Preview-first; the Build progress is the engine's own per-stage trail.
"""
from __future__ import annotations

import json
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk

from src.core import invoke as invoke_mod
from src.lib import theme

_POLL_MS = 100
_TOOL_ID = "plan"


def _slug(value: str) -> str:
    out = "".join(c if (c.isalnum() or c in "-_") else "-" for c in value.lower()).strip("-")
    return out or "new-project"


class PlannerView:
    """Plan a new project: intent -> propose -> preview -> build."""

    def __init__(self, parent, paths):
        self.paths = paths
        self._results: "queue.Queue" = queue.Queue()
        self._running = False
        self._last_dir: str | None = None
        self.frame = ttk.Frame(parent, padding=14)
        self._build()
        self._poll(parent)

    # ---------------------------------------------------------------- layout
    def _build(self) -> None:
        f = self.frame
        ttk.Label(f, text="Plan a new project", style="Heading.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(f, text="State an intent, let it propose a structure, curate it, then build. "
                  "Nothing is written until you press Build.", style="Muted.TLabel").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(2, 12))

        ttk.Label(f, text="What are you making?").grid(row=2, column=0, sticky="nw", pady=3)
        self.intent = tk.Text(f, height=3, bg=theme.PALETTE["bg_secondary"],
                              fg=theme.PALETTE["text"], font=theme.FONT_MONO, relief="flat",
                              insertbackground="white", highlightthickness=1,
                              highlightbackground=theme.PALETTE["border"], wrap="word")
        self.intent.grid(row=2, column=1, columnspan=2, sticky="we", pady=3)

        self.name_var = tk.StringVar()
        self.subfolder_var = tk.StringVar()
        self.archetype_var = tk.StringVar(value="(let it decide)")

        ttk.Label(f, text="Project name").grid(row=3, column=0, sticky="w", pady=3)
        name_e = ttk.Entry(f, textvariable=self.name_var)
        name_e.grid(row=3, column=1, columnspan=2, sticky="we", pady=3)
        name_e.bind("<FocusOut>", self._default_subfolder)

        ttk.Label(f, text="Subfolder").grid(row=4, column=0, sticky="w", pady=3)
        ttk.Entry(f, textvariable=self.subfolder_var).grid(row=4, column=1, sticky="we", pady=3)
        ttk.Label(f, text="created inside the current workspace", style="Muted.TLabel").grid(
            row=4, column=2, sticky="w", padx=(8, 0))

        ttk.Label(f, text="Archetype").grid(row=5, column=0, sticky="w", pady=3)
        ttk.Combobox(f, textvariable=self.archetype_var, state="readonly",
                     values=["(let it decide)", "python-cli", "web-app", "records-project"]).grid(
            row=5, column=1, sticky="w", pady=3)

        btns = ttk.Frame(f)
        btns.grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 4))
        self.propose_btn = ttk.Button(btns, text="1. Propose structure",
                                      command=lambda: self._go("propose"))
        self.propose_btn.pack(side="left", padx=(0, 6))
        self.preview_btn = ttk.Button(btns, text="2. Preview", command=lambda: self._go("preview"))
        self.preview_btn.pack(side="left", padx=(0, 6))
        self.build_btn = ttk.Button(btns, text="3. Build", style="Accent.TButton",
                                    command=lambda: self._go("build"))
        self.build_btn.pack(side="left")

        ttk.Label(f, text="Proposed structure (editable JSON map)").grid(
            row=7, column=0, columnspan=3, sticky="w", pady=(8, 2))
        self.map_box = tk.Text(f, height=10, bg=theme.PALETTE["bg_secondary"],
                               fg=theme.PALETTE["text"], font=theme.FONT_MONO, relief="flat",
                               insertbackground="white", highlightthickness=1,
                               highlightbackground=theme.PALETTE["border"], wrap="none")
        self.map_box.grid(row=8, column=0, columnspan=3, sticky="nsew")

        self.output = tk.Text(f, height=9, bg=theme.PALETTE["bg_secondary"],
                              fg=theme.PALETTE["status"], font=theme.FONT_MONO, relief="flat",
                              insertbackground="white", highlightthickness=1,
                              highlightbackground=theme.PALETTE["border"])
        self.output.grid(row=9, column=0, columnspan=3, sticky="nsew", pady=(8, 6))
        self.open_btn = ttk.Button(f, text="Open project folder", command=self._open,
                                   state="disabled")
        self.open_btn.grid(row=10, column=2, sticky="e")

        f.columnconfigure(1, weight=1)
        f.rowconfigure(8, weight=1)
        f.rowconfigure(9, weight=1)
        self._write("state an intent + name, then press Propose.")

    # ---------------------------------------------------------------- helpers
    def _default_subfolder(self, _evt=None) -> None:
        if not self.subfolder_var.get().strip() and self.name_var.get().strip():
            self.subfolder_var.set(_slug(self.name_var.get()))

    def _intent(self) -> str:
        return self.intent.get("1.0", "end").strip()

    def _map(self) -> "dict | None":
        raw = self.map_box.get("1.0", "end").strip()
        if not raw:
            return None
        return json.loads(raw)  # caller guards ValueError

    def _archetype(self) -> "str | None":
        v = self.archetype_var.get()
        return None if v.startswith("(") else v

    def _args(self, action: str) -> dict:
        intent = self._intent()
        if not intent:
            raise ValueError("state what you're making (the intent) first")
        name = self.name_var.get().strip() or "untitled-project"
        if action == "propose":
            return {"action": "propose", "intent": intent, "name": name,
                    "archetype": self._archetype()}
        try:
            pmap = self._map()
        except ValueError as e:
            raise ValueError(f"the structure box is not valid JSON: {e}") from e
        if not pmap:
            raise ValueError("press Propose first (or paste a project map) to fill the structure")
        args = {"action": action, "intent": intent, "name": name, "map": pmap,
                "root": self.subfolder_var.get().strip() or _slug(name)}
        if action == "build":
            args["apply"] = True
        return args

    # ---------------------------------------------------------------- dispatch (worker thread)
    def _go(self, action: str) -> None:
        if self._running:
            return
        try:
            args = self._args(action)
        except ValueError as e:
            self._write(f"input error: {e}")
            return
        self._running = True
        self._pending = action
        for b in (self.propose_btn, self.preview_btn, self.build_btn):
            b.config(state="disabled")
        self.open_btn.config(state="disabled")
        self._write({"propose": "proposing a structure...",
                     "preview": "previewing the full plan...",
                     "build": "building (genesis -> scaffold -> provenance -> journal)..."}[action])
        threading.Thread(target=self._worker, args=(args,), daemon=True).start()

    def _worker(self, args: dict) -> None:
        self._results.put((args.get("action"), invoke_mod.invoke(self.paths, _TOOL_ID, args)))

    def _poll(self, widget) -> None:
        try:
            while True:
                action, result = self._results.get_nowait()
                self._render(action, result)
        except queue.Empty:
            pass
        widget.after(_POLL_MS, lambda: self._poll(widget))

    # ---------------------------------------------------------------- render
    def _render(self, action, result) -> None:
        self._running = False
        for b in (self.propose_btn, self.preview_btn, self.build_btn):
            b.config(state="normal")
        if not result.ok:
            self.output.config(fg=theme.PALETTE["danger"])
            self._write(f"[FAILED] {result.error or (result.output or {}).get('error')}")
            return
        o = result.output or {}
        self.output.config(fg=theme.PALETTE["status"])
        if action == "propose":
            self._set_map(o.get("map") or {})
            note = "  (no model reachable - editable archetype)" if o.get("degraded") else ""
            self._write(f"proposed from {o.get('source')}{note}.\n"
                        "Edit the structure above if you like, then press Preview.")
        elif action == "preview":
            lines = ["PLAN (nothing written):",
                     f"  dirs:  {len(o.get('planned_dirs', []))}",
                     f"  files: {len(o.get('planned_files', []))}  (+ PROJECT_PLAN.md)"]
            lines += ["  will:"] + [f"    - {w}" for w in o.get("will", [])]
            lines.append("  -> press Build to create it.")
            self._write("\n".join(lines))
        elif action == "build":
            lines = ["✓ Built" if o.get("created") else "[incomplete]"]
            for t in o.get("trail", []):
                mark = "ok" if t.get("ok") else "FAIL"
                extra = " (skipped)" if t.get("skipped") else ""
                lines.append(f"  {mark:>4}  {t.get('step')}{extra}")
            th = o.get("trace_hint")
            if th:
                lines.append(f"  why it exists:  provenance trace project:{o.get('name')}")
            self._write("\n".join(lines))
            base = next((t.get("base") for t in o.get("trail", []) if t.get("base")), None)
            if base:
                self._last_dir = base
                self.open_btn.config(state="normal")

    # ---------------------------------------------------------------- misc
    def _set_map(self, m: dict) -> None:
        self.map_box.delete("1.0", "end")
        self.map_box.insert("end", json.dumps(m, indent=2))

    def _open(self) -> None:
        if not self._last_dir:
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(self._last_dir)  # noqa: S606 (operator-invoked local path)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", self._last_dir])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", self._last_dir])
        except OSError as e:
            self._write(f"could not open folder: {e}")

    def _write(self, text: str) -> None:
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("end", text)
        self.output.config(state="disabled")

    def run_sync(self, args: dict):
        """Bounded, mainloop-free dispatch for the plan-probe."""
        result = invoke_mod.invoke(self.paths, _TOOL_ID, args)
        self._render(args.get("action"), result)
        return result


def build(parent, paths) -> PlannerView:
    view = PlannerView(parent, paths)
    view.frame.pack(fill="both", expand=True)
    return view
