"""
FILE:       src/ui/installer_view.py
ROLE:       Human "one-click installer"  -  deploy the toolkit into a project you pick.
DOMAIN:     ui
DOES:       Pick a target project folder; Preview shows a dry-run plan; Install copies the clean
            toolkit into <target>/.useful-helpers/ (host AGENTS.md pointer + .gitignore entry
            optional). All work crosses the one governed core.invoke() seam on a worker thread
            (sidecar_install is Apply -> authority-checked + audit-logged); Preview is dry-run,
            Install is confirm.
DEPENDS ON: src.core.invoke, src.lib.theme, (stdlib) os, queue, sys, threading, pathlib, tkinter
WIRES TO:   core.invoke -> tools/sidecar_install (the one seam; governance applies identically)
NOTES:      "Dumb shell"  -  no install logic here; the tool owns it. Preview first, then Install.
"""
from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, ttk

from src.core import invoke as invoke_mod
from src.lib import theme

_POLL_MS = 100
_TOOL_ID = "sidecar_install"


class InstallerView:
    """Compact installer: pick a project, preview, install the .useful-helpers sidecar."""

    def __init__(self, parent, paths):
        self.paths = paths
        self._results: "queue.Queue" = queue.Queue()
        self._running = False
        self._last_sidecar: str | None = None
        self.frame = ttk.Frame(parent, padding=14)
        self._build()
        self._poll(parent)

    def _build(self) -> None:
        f = self.frame
        ttk.Label(f, text="Install the toolkit into a project", style="Heading.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(f, text="Drops a self-contained sidecar folder  -  nothing collides with the "
                  "host project or its git.", style="Muted.TLabel").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(2, 12))

        self.target_var = tk.StringVar()
        self.folder_var = tk.StringVar(value=".useful-helpers")
        self.agents_var = tk.BooleanVar(value=True)
        self.gitignore_var = tk.BooleanVar(value=True)
        self.overwrite_var = tk.BooleanVar(value=False)
        self.update_var = tk.BooleanVar(value=False)

        ttk.Label(f, text="Target project").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(f, textvariable=self.target_var).grid(row=2, column=1, sticky="we", pady=3)
        ttk.Button(f, text="Browse...", command=self._browse).grid(row=2, column=2, sticky="w",
                                                                 padx=(8, 0))
        ttk.Label(f, text="Sidecar folder").grid(row=3, column=0, sticky="w", pady=3)
        ttk.Entry(f, textvariable=self.folder_var).grid(row=3, column=1, sticky="we", pady=3)

        opts = ttk.Frame(f)
        opts.grid(row=4, column=1, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Checkbutton(opts, text="Host AGENTS.md pointer (if absent)",
                        variable=self.agents_var).pack(anchor="w")
        ttk.Checkbutton(opts, text="Add to host .gitignore (git repos)",
                        variable=self.gitignore_var).pack(anchor="w")
        ttk.Checkbutton(opts, text="Update in place (preserve memory) if already installed",
                        variable=self.update_var).pack(anchor="w")
        ttk.Checkbutton(opts, text="Overwrite an existing sidecar (clean reinstall  -  wipes memory)",
                        variable=self.overwrite_var).pack(anchor="w")

        btns = ttk.Frame(f)
        btns.grid(row=5, column=1, columnspan=2, sticky="e", pady=(10, 6))
        self.preview_btn = ttk.Button(btns, text="Preview", command=lambda: self._go(True))
        self.preview_btn.pack(side="left", padx=(0, 6))
        self.install_btn = ttk.Button(btns, text="Install", style="Accent.TButton",
                                      command=lambda: self._go(False))
        self.install_btn.pack(side="left")

        self.output = tk.Text(f, height=13, bg=theme.PALETTE["bg_secondary"],
                              fg=theme.PALETTE["status"], font=theme.FONT_MONO, relief="flat",
                              insertbackground="white", highlightthickness=1,
                              highlightbackground=theme.PALETTE["border"])
        self.output.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=(4, 8))
        self.open_btn = ttk.Button(f, text="Open sidecar folder", command=self._open,
                                   state="disabled")
        self.open_btn.grid(row=7, column=2, sticky="e")

        f.columnconfigure(1, weight=1)
        f.rowconfigure(6, weight=1)
        self._write("pick a target project, then Preview.")

    def _browse(self) -> None:
        d = filedialog.askdirectory(title="Choose the project to install the toolkit into")
        if d:
            self.target_var.set(d)

    def _args(self, dry_run: bool) -> dict:
        target = self.target_var.get().strip()
        if not target:
            raise ValueError("choose a target project folder first")
        return {"target": target, "folder": self.folder_var.get().strip() or ".useful-helpers",
                "dry_run": dry_run, "confirm": not dry_run,
                "overwrite": bool(self.overwrite_var.get()),
                "update": bool(self.update_var.get()),
                "write_agents": bool(self.agents_var.get()),
                "gitignore": bool(self.gitignore_var.get())}

    def _go(self, dry_run: bool) -> None:
        if self._running:
            return
        try:
            args = self._args(dry_run)
        except ValueError as e:
            self._write(f"input error: {e}")
            return
        self._running = True
        self._pending_dry = dry_run
        self.preview_btn.config(state="disabled")
        self.install_btn.config(state="disabled", text="Working...")
        self.open_btn.config(state="disabled")
        self._write(("previewing..." if dry_run else "installing...") + f" {args['target']}")
        threading.Thread(target=self._worker, args=(args,), daemon=True).start()

    def _worker(self, args: dict) -> None:
        result = invoke_mod.invoke(self.paths, _TOOL_ID, args, client="gui")
        self._results.put(result)

    def _poll(self, widget) -> None:
        try:
            while True:
                self._render(self._results.get_nowait())
        except queue.Empty:
            pass
        widget.after(_POLL_MS, lambda: self._poll(widget))

    def _render(self, result) -> None:
        self._running = False
        self.preview_btn.config(state="normal")
        self.install_btn.config(state="normal", text="Install")
        if not result.ok:
            self.output.config(fg=theme.PALETTE["danger"])
            self._write(f"[FAILED] {result.error or (result.output or {})}")
            return
        o = result.output or {}
        dry = o.get("dry_run", True)
        lines = ["PLAN (dry-run):" if dry else "✓ Installed",
                 f"  sidecar:   {o.get('sidecar')}",
                 f"  files:     {o.get('file_count')}",
                 f"  AGENTS.md: {o.get('host_agents')}",
                 f"  gitignore: {o.get('gitignore')}"]
        if not dry:
            lines += [f"  written:   {o.get('written_count')}",
                      f"  host AGENTS.md written: {o.get('wrote_host_agents')}",
                      f"  .gitignore updated:     {o.get('gitignore_updated')}"]
            self._last_sidecar = o.get("sidecar")
            self.open_btn.config(state="normal")
        else:
            lines.append("  -> press Install to apply.")
        self.output.config(fg=theme.PALETTE["status"])
        self._write("\n".join(lines))

    def _open(self) -> None:
        if not self._last_sidecar:
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(self._last_sidecar)  # noqa: S606 (operator-invoked local path)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", self._last_sidecar])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", self._last_sidecar])
        except OSError as e:
            self._write(f"could not open folder: {e}")

    def _write(self, text: str) -> None:
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("end", text)
        self.output.config(state="disabled")

    def run_sync(self, args: dict):
        """Bounded, mainloop-free dispatch for the install-probe."""
        result = invoke_mod.invoke(self.paths, _TOOL_ID, args)
        self._render(result)
        return result


def build(parent, paths) -> InstallerView:
    view = InstallerView(parent, paths)
    view.frame.pack(fill="both", expand=True)
    return view
