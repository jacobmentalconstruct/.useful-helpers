"""
FILE:       src/ui/mapper_view.py
ROLE:       Human "Operator" view #1  -  a friendly face over the projectmapper app, with an
            interactive include/exclude checkbox tree.
DOMAIN:     ui
DOES:       Pick any folder; a lazy tristate checkbox tree shows what would be captured (dot
            sidecars + heavy build dirs hidden, like the engine). Model A: everything is
            selected by default  -  untick folders/files to leave them out. Choose forms (SQLite
            always; optional Markdown map + file dump), where to save, then Generate. The run
            dispatches through the one governed core.invoke() seam on a worker thread
            (projectmapper is Apply -> authority-checked + audit-logged), passing the unticked
            paths as `exclude_paths`. Results show the artifact path + volumetrics with
            Open-folder / Copy-path actions.
DEPENDS ON: src.core.invoke, src.lib.theme, (stdlib) os, queue, sys, threading, pathlib, tkinter
WIRES TO:   core.invoke -> apps/projectmapper (the one seam; governance applies identically)
NOTES:      "Dumb shell" discipline  -  no snapshot logic here; the app owns it. The tree only
            computes a *selection* (the minimal set of top-most unticked paths) and hands it to
            the headless tool as data. Full per-node state + roll-up keeps GUI and engine
            consistent (re-checking inside an unticked folder makes the folder tristate, so the
            engine descends and only the still-unticked siblings are pruned). Lazy: a folder's
            children materialize when it is expanded, so big trees stay responsive.
"""
from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from src.core import invoke as invoke_mod
from src.lib import theme

_POLL_MS = 100
_TOOL_ID = "projectmapper"
_DUMMY = "\x00dummy"          # lazy-expand placeholder suffix
_MAX_PER_DIR = 3000           # soft cap on children rendered per folder

CHECKED, UNCHECKED, TRISTATE = "checked", "unchecked", "tristate"

# Heavy non-dot dirs the engine also prunes  -  hidden so the tree mirrors what is captured
# (dot-folders are always hidden by the sidecar convention).
_TREE_HIDE = {"node_modules", "venv", "dist", "build", "out", "target", "bin", "obj",
              "_artifacts", "logs", "_logs", "__pycache__"}


class MapperView:
    """projectmapper front-end with an include/exclude checkbox tree."""

    def __init__(self, parent, paths):
        self.paths = paths
        self._results: "queue.Queue" = queue.Queue()
        self._running = False
        self._last_dir: str | None = None
        self._last_path: str | None = None
        # tree/selection state
        self._root_path: str = ""
        self._state: dict[str, str] = {}       # iid(abs posix path) -> checked/unchecked/tristate
        self._is_dir: dict[str, bool] = {}
        self._loaded: set[str] = set()
        self._exclude_names: set[str] = set()
        self.frame = ttk.Frame(parent, padding=12)
        self._make_icons(parent)
        self._build()
        self._poll(parent)

    # ---- checkbox icons -------------------------------------------------
    def _make_icons(self, parent) -> None:
        border, accent, muted = (theme.PALETTE["border"], theme.PALETTE["accent"],
                                 theme.PALETTE["muted"])
        self._img: dict[str, tk.PhotoImage] = {}
        # unchecked: hollow box
        u = tk.PhotoImage(master=parent, width=14, height=14)
        for box in ((0, 0, 14, 1), (0, 13, 14, 14), (0, 0, 1, 14), (13, 0, 14, 14)):
            u.put((border,), to=box)
        self._img[UNCHECKED] = u
        # checked: filled accent + white tick
        c = tk.PhotoImage(master=parent, width=14, height=14)
        c.put((accent,), to=(0, 0, 14, 14))
        c.put(("#FFFFFF",), to=(3, 7, 6, 10))
        c.put(("#FFFFFF",), to=(6, 5, 11, 8))
        self._img[CHECKED] = c
        # tristate: filled muted + white dash
        t = tk.PhotoImage(master=parent, width=14, height=14)
        t.put((muted,), to=(0, 0, 14, 14))
        t.put(("#FFFFFF",), to=(3, 6, 11, 9))
        self._img[TRISTATE] = t

    # ---- layout ---------------------------------------------------------
    def _build(self) -> None:
        f = self.frame
        ttk.Label(f, text="Project Snapshot", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(f, text="Pick a folder, untick anything you don't want, then Generate a "
                  "shareable map / file dump.", style="Muted.TLabel").pack(anchor="w",
                                                                           pady=(2, 10))

        self.source_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.save_var = tk.StringVar()
        self.exclude_var = tk.StringVar()
        self.markdown_var = tk.BooleanVar(value=True)
        self.gitignore_var = tk.BooleanVar(value=False)
        self.into_map_var = tk.BooleanVar(value=False)

        top = ttk.Frame(f)
        top.pack(fill="x")
        self._row_path(top, 0, "Source folder", self.source_var, self._browse_source,
                       extra=("Rescan", self._rescan))
        ttk.Label(top, text="Snapshot name").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(top, textvariable=self.name_var).grid(row=1, column=1, sticky="we", pady=3)
        opts = ttk.Frame(top)
        opts.grid(row=1, column=2, sticky="w", padx=(8, 0))
        ttk.Checkbutton(opts, text="Map + dump (.md)", variable=self.markdown_var).pack(side="left")
        ttk.Checkbutton(opts, text="Honor .gitignore", variable=self.gitignore_var,
                        command=self._rescan).pack(side="left", padx=(10, 0))
        ttk.Label(top, text="Exclude names").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(top, textvariable=self.exclude_var).grid(row=2, column=1, sticky="we", pady=3)
        ttk.Button(top, text="Apply", command=self._rescan).grid(row=2, column=2, sticky="w",
                                                                 padx=(8, 0))
        top.columnconfigure(1, weight=1)

        # Selection toolbar + tree (the centerpiece).
        bar = ttk.Frame(f)
        bar.pack(fill="x", pady=(10, 2))
        ttk.Label(bar, text="Include / exclude  (untick to leave out)",
                  style="Muted.TLabel").pack(side="left")
        ttk.Button(bar, text="None", command=lambda: self._set_all(UNCHECKED)).pack(side="right")
        ttk.Button(bar, text="All", command=lambda: self._set_all(CHECKED)).pack(side="right",
                                                                                 padx=(0, 6))
        tree_wrap = ttk.Frame(f)
        tree_wrap.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_wrap, show="tree", selectmode="browse")
        ysb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        ysb.pack(side="right", fill="y")
        self.tree.bind("<ButtonRelease-1>", self._on_click)
        self.tree.bind("<<TreeviewOpen>>", self._on_open)

        # Save + generate.
        bottom = ttk.Frame(f)
        bottom.pack(fill="x", pady=(10, 0))
        self._row_path(bottom, 0, "Save to", self.save_var, self._browse_save,
                       hint="(blank = _artifacts/projectmapper)")
        ttk.Checkbutton(bottom, text="Save inside project as a .map sidecar",
                        variable=self.into_map_var).grid(row=1, column=1, sticky="w")
        self.gen_btn = ttk.Button(bottom, text="Generate snapshot", style="Accent.TButton",
                                  command=self._on_generate)
        self.gen_btn.grid(row=1, column=2, sticky="e", pady=(4, 0))
        bottom.columnconfigure(1, weight=1)

        self.output = tk.Text(f, height=7, bg=theme.PALETTE["bg_secondary"],
                              fg=theme.PALETTE["status"], font=theme.FONT_MONO, relief="flat",
                              insertbackground="white", highlightthickness=1,
                              highlightbackground=theme.PALETTE["border"])
        self.output.pack(fill="x", pady=(8, 6))
        actions = ttk.Frame(f)
        actions.pack(fill="x")
        self.open_btn = ttk.Button(actions, text="Open folder", command=self._open_folder,
                                   state="disabled")
        self.open_btn.pack(side="right", padx=(6, 0))
        self.copy_btn = ttk.Button(actions, text="Copy path", command=self._copy_path,
                                   state="disabled")
        self.copy_btn.pack(side="right")
        self._write("ready  -  pick a source folder.")

    def _row_path(self, parent, row, label, var, browse, hint="", extra=None) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="we", pady=3)
        bar = ttk.Frame(parent)
        bar.grid(row=row, column=2, sticky="w", padx=(8, 0))
        ttk.Button(bar, text="Browse...", command=browse).pack(side="left")
        if extra:
            ttk.Button(bar, text=extra[0], command=extra[1]).pack(side="left", padx=(6, 0))
        if hint:
            ttk.Label(bar, text=hint, style="Muted.TLabel").pack(side="left", padx=(8, 0))

    # ---- browse ---------------------------------------------------------
    def _browse_source(self) -> None:
        d = filedialog.askdirectory(title="Choose a project / folder to snapshot")
        if d:
            self.source_var.set(d)
            if not self.name_var.get().strip():
                self.name_var.set(Path(d).name)
            self._rescan()

    def _browse_save(self) -> None:
        d = filedialog.askdirectory(title="Choose where to save the snapshot")
        if d:
            self.save_var.set(d)

    # ---- tree build (lazy) ----------------------------------------------
    def _gitignore_names(self, root: Path) -> set[str]:
        names: set[str] = set()
        gi = root / ".gitignore"
        if not gi.exists():
            return names
        for line in gi.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("!"):
                continue
            s = s.strip("/")
            if s and "/" not in s and "*" not in s and "?" not in s:
                names.add(s)
        return names

    def _rescan(self) -> None:
        self.tree.delete(*self.tree.get_children(""))
        self._state.clear()
        self._is_dir.clear()
        self._loaded.clear()
        src = self.source_var.get().strip()
        if not src or not Path(src).is_dir():
            self._write("pick a valid source folder, then Rescan.")
            return
        self._root_path = str(Path(src).resolve()).replace("\\", "/")
        self._exclude_names = set(_TREE_HIDE) | {
            x.strip() for x in self.exclude_var.get().split(",") if x.strip()}
        if self.gitignore_var.get():
            self._exclude_names |= self._gitignore_names(Path(self._root_path))
        self._populate(self._root_path, "")
        self._write("tick/untick to shape the snapshot; expand folders to refine.")

    def _populate(self, scan_path: str, tree_parent: str) -> None:
        try:
            entries = list(os.scandir(scan_path))
        except OSError:
            return
        entries.sort(key=lambda e: (not _safe_is_dir(e), e.name.lower()))
        shown = 0
        for e in entries:
            isdir = _safe_is_dir(e)
            name = e.name
            if isdir and (name.startswith(".") or name in self._exclude_names):
                continue
            if shown >= _MAX_PER_DIR:
                self.tree.insert(tree_parent, "end",
                                 text=f"  ... more items not shown (>{_MAX_PER_DIR})")
                break
            child = e.path.replace("\\", "/")
            st = self._state.get(child) or self._inherit(tree_parent)
            self._state[child] = st
            self._is_dir[child] = isdir
            self.tree.insert(tree_parent, "end", iid=child, text=f" {name}",
                             image=self._img[st], open=False)
            if isdir:
                self.tree.insert(child, "end", iid=child + _DUMMY, text="")
            shown += 1
        self._loaded.add(tree_parent or self._root_path)

    def _inherit(self, tree_parent: str) -> str:
        pst = self._state.get(tree_parent, CHECKED)
        return UNCHECKED if pst == UNCHECKED else CHECKED

    def _on_open(self, _e=None) -> None:
        iid = self.tree.focus()
        if iid and self._is_dir.get(iid) and iid not in self._loaded:
            for ch in self.tree.get_children(iid):
                if ch.endswith(_DUMMY):
                    self.tree.delete(ch)
            self._populate(iid, iid)

    # ---- checkbox state machine -----------------------------------------
    def _on_click(self, event) -> None:
        if "image" not in self.tree.identify_element(event.x, event.y):
            return
        iid = self.tree.identify_row(event.y)
        if not iid or iid.endswith(_DUMMY) or iid not in self._state:
            return
        cur = self._state.get(iid, CHECKED)
        new = CHECKED if cur in (UNCHECKED, TRISTATE) else UNCHECKED
        self._set_subtree(iid, new)
        self._rollup_from(self.tree.parent(iid))
        self._refresh_images()

    def _set_subtree(self, iid: str, state: str) -> None:
        self._state[iid] = state
        for ch in self.tree.get_children(iid):
            if not ch.endswith(_DUMMY) and ch in self._state:
                self._set_subtree(ch, state)

    def _rollup_from(self, iid: str) -> None:
        while iid:
            kids = [c for c in self.tree.get_children(iid)
                    if not c.endswith(_DUMMY) and c in self._state]
            if kids:
                states = {self._state[c] for c in kids}
                self._state[iid] = (CHECKED if states == {CHECKED}
                                    else UNCHECKED if states == {UNCHECKED} else TRISTATE)
            iid = self.tree.parent(iid)

    def _set_all(self, state: str) -> None:
        for top in self.tree.get_children(""):
            if top in self._state:
                self._set_subtree(top, state)
        self._refresh_images()

    def _refresh_images(self) -> None:
        def walk(iid):
            for ch in self.tree.get_children(iid):
                if ch.endswith(_DUMMY) or ch not in self._state:
                    continue
                self.tree.item(ch, image=self._img[self._state[ch]])
                walk(ch)
        walk("")

    def _deselected_rel_paths(self) -> list[str]:
        """Minimal top-most unticked paths, root-relative posix (model A blacklist)."""
        out: list[str] = []

        def visit(iid):
            st = self._state.get(iid, CHECKED)
            parent = self.tree.parent(iid)
            pst = self._state.get(parent, CHECKED) if parent else CHECKED
            if st == UNCHECKED and pst != UNCHECKED:
                out.append(iid[len(self._root_path) + 1:])
                return  # boundary  -  its subtree is covered
            for ch in self.tree.get_children(iid):
                if not ch.endswith(_DUMMY) and ch in self._state:
                    visit(ch)

        for top in self.tree.get_children(""):
            if top in self._state:
                visit(top)
        return out

    # ---- generate (worker thread -> after-poll) --------------------------
    def _collect_args(self) -> dict:
        root = self.source_var.get().strip()
        if not root:
            raise ValueError("choose a source folder first")
        if not Path(root).is_dir():
            raise ValueError(f"not a folder: {root}")
        name = self.name_var.get().strip() or Path(root).name
        args: dict = {"action": "compile", "root": root, "name": name}
        if self.markdown_var.get():
            args["markdown"] = True
        if self.gitignore_var.get():
            args["respect_gitignore"] = True
        excludes = [x.strip() for x in self.exclude_var.get().split(",") if x.strip()]
        if excludes:
            args["exclude"] = excludes
        deselected = self._deselected_rel_paths()
        if deselected:
            args["exclude_paths"] = deselected
        if self.into_map_var.get():
            parent = Path(root) / ".map"
            args["out"] = str(parent / f"{name}_snapshot.sqlite3")
        else:
            save = self.save_var.get().strip()
            if save:
                parent = Path(save)
                args["out"] = str(parent / f"{name}_snapshot.sqlite3")
            else:
                parent = Path.cwd() / "_artifacts" / "projectmapper"
        self._pending_dir = str(parent.resolve())
        self._pending_path = str((parent / f"{name}_snapshot.sqlite3").resolve())
        return args

    def _on_generate(self) -> None:
        if self._running:
            return
        try:
            args = self._collect_args()
        except ValueError as e:
            self._write(f"input error: {e}")
            return
        self._running = True
        self.gen_btn.config(state="disabled", text="Scanning...")
        self.open_btn.config(state="disabled")
        self.copy_btn.config(state="disabled")
        n = len(args.get("exclude_paths", []))
        self._write(f"scanning {args['root']} ... ({n} path(s) deselected)")
        threading.Thread(target=self._worker, args=(args,), daemon=True).start()

    def _worker(self, args: dict) -> None:
        result = invoke_mod.invoke(self.paths, _TOOL_ID, args)
        self._results.put((result, self._pending_dir, self._pending_path))

    def _poll(self, widget) -> None:
        try:
            while True:
                self._render(*self._results.get_nowait())
        except queue.Empty:
            pass
        widget.after(_POLL_MS, lambda: self._poll(widget))

    def _render(self, result, out_dir: str, out_path: str) -> None:
        self._running = False
        self.gen_btn.config(state="normal", text="Generate snapshot")
        if not result.ok:
            self.output.config(fg=theme.PALETTE["danger"])
            self._write(f"[FAILED] {result.error or (result.output or {})}")
            return
        o = result.output or {}
        outs = o.get("outputs", {})
        lines = [
            "✓ Snapshot written",
            f"  {out_path}",
            f"  {o.get('file_count', '?')} files - {o.get('text_file_count', '?')} captured "
            f"- {o.get('deselected_count', 0)} deselected - {o.get('skipped_count', '?')} skipped",
            f"  sha256 {str(o.get('artifact_sha256', ''))[:12]}...",
        ]
        if "tree_md" in outs or "filedump_md" in outs:
            lines.append("  + project map + file dump (.md) alongside")
        self.output.config(fg=theme.PALETTE["status"])
        self._write("\n".join(lines))
        self._last_dir, self._last_path = out_dir, out_path
        self.open_btn.config(state="normal")
        self.copy_btn.config(state="normal")

    # ---- result actions -------------------------------------------------
    def _open_folder(self) -> None:
        if not self._last_dir:
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(self._last_dir)  # noqa: S606 (operator-invoked, local path)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", self._last_dir])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", self._last_dir])
        except OSError as e:
            self._write(f"could not open folder: {e}")

    def _copy_path(self) -> None:
        if not self._last_path:
            return
        self.frame.clipboard_clear()
        self.frame.clipboard_append(self._last_path)
        self._write(f"copied to clipboard:\n  {self._last_path}")

    def _write(self, text: str) -> None:
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("end", text)
        self.output.config(state="disabled")

    # ---- probe support (bounded, mainloop-free) -------------------------
    def run_generate_sync(self, args: dict):
        """Run one snapshot inline and render  -  for the bounded map-probe verification."""
        result = invoke_mod.invoke(self.paths, _TOOL_ID, args)
        parent = Path(args["out"]).parent if args.get("out") else (
            Path.cwd() / "_artifacts" / "projectmapper")
        name = args.get("name") or Path(args["root"]).name
        self._render(result, str(parent.resolve()),
                     str((parent / f"{name}_snapshot.sqlite3").resolve()))
        return result


def _safe_is_dir(entry) -> bool:
    try:
        return entry.is_dir()
    except OSError:
        return False


def build(parent, paths) -> MapperView:
    """Construct the project-snapshot view under `parent`."""
    view = MapperView(parent, paths)
    view.frame.pack(fill="both", expand=True)
    return view
