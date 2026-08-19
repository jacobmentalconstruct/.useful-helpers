"""
FILE:       src/ui/registry_view.py
ROLE:       Render the registry as launchable entries; running a tool dispatches invoke().
DOMAIN:     ui
DOES:       Left pane: all registered tools grouped by category with authority badges (live
            registry read  -  nothing hardcoded). Right pane: the selected tool's summary + a
            form generated from its input_schema; Run collects args and dispatches through the
            governed core.invoke() on a worker thread, then renders the structured result.
DEPENDS ON: src.core.registry, src.core.invoke, src.lib.theme, (stdlib) tkinter, json, threading
WIRES TO:   core.invoke (the one seam  -  governance applies to GUI calls identically)
NOTES:      "Dumb shell" discipline: no business logic here  -  schema in, args out, one seam.
            Empty form fields are OMITTED from args (tool defaults apply). Worker-thread
            results are marshaled to the Tk thread via an after()-poll queue. run_tool_sync()
            exists for the bounded ui-probe (no mainloop needed).
"""
from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from tkinter import ttk

from src.core import invoke as invoke_mod
from src.core import registry
from src.lib import theme

_POLL_MS = 100


def _parse_value(raw: str, prop_type: str):
    """Convert a form string to the schema's type. Empty handled by caller (omitted)."""
    if prop_type == "integer":
        return int(raw)
    if prop_type == "number":
        return float(raw)
    if prop_type == "boolean":
        return raw.strip().lower() in ("true", "1", "yes", "on")
    if prop_type in ("object", "array"):
        return json.loads(raw)
    return raw


class RegistryView:
    """The registry-driven control panel widget tree."""

    def __init__(self, parent, paths):
        self.paths = paths
        self.tools = {t.id: t for t in registry.list_tools(paths)}
        self._fields: dict[str, tuple[tk.Variable, str]] = {}
        self._results: "queue.Queue" = queue.Queue()
        self._running = False
        self.frame = ttk.Frame(parent)
        self._build(parent)
        self._poll(parent)

    # ---- layout -------------------------------------------------------
    def _build(self, parent) -> None:
        paned = ttk.Panedwindow(self.frame, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Left: category-grouped tool tree with authority badges.
        left = ttk.Frame(paned)
        self.tree = ttk.Treeview(left, show="tree", selectmode="browse")
        ysb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        ysb.pack(side="right", fill="y")
        for auth, color in theme.AUTHORITY_COLORS.items():
            self.tree.tag_configure(f"auth_{auth}", foreground=color)
        by_cat: dict[str, list] = {}
        for t in self.tools.values():
            by_cat.setdefault(t.category, []).append(t)
        for cat in sorted(by_cat):
            node = self.tree.insert("", "end", text=f" {cat}", open=False)
            for t in sorted(by_cat[cat], key=lambda x: x.id):
                self.tree.insert(node, "end", iid=t.id,
                                 text=f" {t.id}   [{t.authority}]",
                                 tags=(f"auth_{t.authority}",))
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        paned.add(left, weight=1)

        # Right: detail + form + result.
        right = ttk.Frame(paned, padding=10)
        self.title_lbl = ttk.Label(right, text="Select a tool", style="Heading.TLabel")
        self.title_lbl.pack(anchor="w")
        self.summary_lbl = ttk.Label(right, text="", style="Muted.TLabel",
                                     wraplength=520, justify="left")
        self.summary_lbl.pack(anchor="w", pady=(2, 8))
        self.form = ttk.Frame(right)
        self.form.pack(fill="x")
        self.run_btn = ttk.Button(right, text="Run", style="Accent.TButton",
                                  command=self._on_run, state="disabled")
        self.run_btn.pack(anchor="e", pady=8)
        self.output = tk.Text(right, height=18, bg=theme.PALETTE["bg_secondary"],
                              fg=theme.PALETTE["status"], font=theme.FONT_MONO,
                              relief="flat", insertbackground="white",
                              highlightthickness=1,
                              highlightbackground=theme.PALETTE["border"])
        self.output.pack(fill="both", expand=True)
        paned.add(right, weight=3)

    # ---- selection -> schema form ---------------------------------------
    def _on_select(self, _event=None) -> None:
        sel = self.tree.selection()
        if not sel or sel[0] not in self.tools:
            return
        tool = self.tools[sel[0]]
        self.title_lbl.config(text=f"{tool.id}   [{tool.authority} - {tool.category}]")
        self.summary_lbl.config(text=tool.summary)
        for child in self.form.winfo_children():
            child.destroy()
        self._fields.clear()
        props = (tool.input_schema or {}).get("properties", {}) or {}
        required = set((tool.input_schema or {}).get("required", []) or [])
        for row, (name, spec) in enumerate(sorted(props.items())):
            spec = spec if isinstance(spec, dict) else {}
            ptype = spec.get("type", "string")
            mark = "*" if name in required else ""
            ttk.Label(self.form, text=f"{name}{mark}").grid(
                row=row, column=0, sticky="w", padx=(0, 8), pady=2)
            var = tk.StringVar(value="")
            enum = spec.get("enum")
            if ptype == "boolean":
                widget = ttk.Combobox(self.form, textvariable=var, width=38,
                                      values=("", "true", "false"), state="readonly")
            elif enum:
                widget = ttk.Combobox(self.form, textvariable=var, width=38,
                                      values=("",) + tuple(str(v) for v in enum),
                                      state="readonly")
            else:
                widget = ttk.Entry(self.form, textvariable=var, width=40)
            widget.grid(row=row, column=1, sticky="we", pady=2)
            hint = spec.get("description", "")
            if hint:
                ttk.Label(self.form, text=hint[:60], style="Muted.TLabel").grid(
                    row=row, column=2, sticky="w", padx=(8, 0))
            self._fields[name] = (var, ptype)
        self.form.columnconfigure(1, weight=1)
        self.run_btn.config(state="normal")
        self._write_output(f"ready: {tool.id}\n(empty fields are omitted; tool defaults apply)")

    def collect_args(self) -> dict:
        """Form -> args dict. Empty fields omitted; values coerced to schema types."""
        args: dict = {}
        errors: list[str] = []
        for name, (var, ptype) in self._fields.items():
            raw = var.get().strip()
            if raw == "":
                continue
            try:
                args[name] = _parse_value(raw, ptype)
            except (ValueError, json.JSONDecodeError) as e:
                errors.append(f"{name}: {e}")
        if errors:
            raise ValueError("; ".join(errors))
        return args

    # ---- dispatch (worker thread -> after-poll) --------------------------
    def _on_run(self) -> None:
        sel = self.tree.selection()
        if not sel or sel[0] not in self.tools or self._running:
            return
        tool_id = sel[0]
        try:
            args = self.collect_args()
        except ValueError as e:
            self._write_output(f"input error: {e}")
            return
        self._running = True
        self.run_btn.config(state="disabled", text="Running...")
        self._write_output(f"running {tool_id} ...")
        threading.Thread(target=self._worker, args=(tool_id, args), daemon=True).start()

    def _worker(self, tool_id: str, args: dict) -> None:
        result = invoke_mod.invoke(self.paths, tool_id, args, client="gui")
        self._results.put(result)

    def _poll(self, widget) -> None:
        try:
            while True:
                self._render_result(self._results.get_nowait())
        except queue.Empty:
            pass
        widget.after(_POLL_MS, lambda: self._poll(widget))

    def _render_result(self, result) -> None:
        self._running = False
        self.run_btn.config(state="normal", text="Run")
        head = f"[{'ok' if result.ok else 'FAILED'}] {result.tool_id}"
        # THE ERROR LEADS ON A FAILURE, and is no longer displaced by the payload. This
        # read `output if output is not None else error`, which was fine while a failed
        # call had no output. The seam now attaches `changed_paths`/`measurement` to
        # target-writing calls WHETHER OR NOT THEY SUCCEEDED - deliberately, since a
        # write that landed before a failure is exactly what a reader needs - and that
        # turned "here is why it failed" into a dict of measurement metadata with the
        # reason nowhere on screen. Both are shown, in the order a reader needs them.
        parts = []
        if not result.ok and result.error:
            parts.append(str(result.error))
        if result.output is not None:
            parts.append(json.dumps(result.output, indent=2))
        body = "\n\n".join(parts) or (result.error or "")
        color = theme.PALETTE["status"] if result.ok else theme.PALETTE["danger"]
        self.output.config(fg=color)
        self._write_output(f"{head}\n{body}")

    def _write_output(self, text: str) -> None:
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("end", text)
        self.output.config(state="disabled")

    # ---- probe support ---------------------------------------------------
    def run_tool_sync(self, tool_id: str, args: dict):
        """Bounded, mainloop-free dispatch for ui-probe: select, run inline, render."""
        if tool_id in self.tools:
            self.tree.selection_set(tool_id)
            self._on_select()
        result = invoke_mod.invoke(self.paths, tool_id, args, client="gui")
        self._render_result(result)
        return result


def build(parent, paths) -> RegistryView:
    """Construct the registry-driven widget tree under `parent`."""
    view = RegistryView(parent, paths)
    view.frame.pack(fill="both", expand=True, padx=10, pady=10)
    return view
