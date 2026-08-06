from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

# Import the CLI from the sibling module
try:
    # Try relative import (standard when running via 'python -m src.app')
    from .linenumberizer import main as ln_main
except ImportError:
    try:
        # Fallback for direct script execution ('python app.py')
        import linenumberizer
        ln_main = linenumberizer.main
    except ImportError as e:
        raise SystemExit("Could not import linenumberizer.py. Ensure it sits next to this GUI file.\n" + str(e))

APP_TITLE = "LineNumberizer – Helper"

STYLES = ("pipe", "colon", "bracket")
AST_MODES = ("tree", "flat", "semantic")

# ----------------------------
# Path utilities
# ----------------------------

def split_stem_ext(path: str):
    base = os.path.basename(path)
    stem, ext = os.path.splitext(base)
    return stem, ext

def default_output_for(input_path: str, op: str, style: str, ast_mode: str) -> str:
    """Return the suggested output path per user preference (underscore tag)."""
    if not input_path:
        return ""
    folder = os.path.dirname(os.path.abspath(input_path))
    stem, ext = split_stem_ext(input_path)
    if op == "annotate":
        out_name = f"{stem}._lineNUMBERED.{style}{ext}"
    elif op == "strip":
        out_name = f"{stem}._stripped{ext}"
    elif op == "map":
        out_name = f"{stem}._linemap.json"
    elif op == "ast":
        out_name = f"{stem}._ast.{ast_mode}.json"
    else:
        out_name = f"{stem}.out"
    return os.path.join(folder, out_name)

# ----------------------------
# Worker
# ----------------------------

def run_cli_async(argv, on_done):
    def _worker():
        try:
            rc = ln_main(argv)
        except Exception as e:
            on_done(False, f"error: {e}")
            return
        ok = (rc == 0)
        on_done(ok, f"Completed with exit code {rc}")
    t = threading.Thread(target=_worker, daemon=True)
    t.start()

# ----------------------------
# GUI
# ----------------------------

class App(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=12)
        self.master = master
        self.grid(sticky="nsew")

        # --- Color Palette (Systems Thinker Edition) ---
        self.C_PRI  = "#1E1E2F"   # Primary Background
        self.C_SEC  = "#252526"   # Secondary Background
        self.C_DEEP = "#151521"   # Console/Log Background
        self.C_INP  = "#2A2A3F"   # Input fields
        self.C_ACC  = "#007ACC"   # Active Blue Accent
        self.C_SUC  = "#90EE90"   # Success Green
        self.C_ERR  = "#C23621"   # Warning Red
        self.C_TXT  = "#CCCCCC"   # Default Text (Light Grey)

        master.configure(bg=self.C_PRI)
        self._setup_theme()

        # Vars
        self.var_file = tk.StringVar()
        self.var_out = tk.StringVar()
        self.var_op = tk.StringVar(value="annotate")
        self.var_style = tk.StringVar(value=STYLES[0])
        self.var_start = tk.IntVar(value=1)
        self.var_width = tk.IntVar(value=0)
        self.var_ast_mode = tk.StringVar(value=AST_MODES[0])

        # Layout config
        master.title(APP_TITLE)
        master.minsize(650, 400)
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(12, weight=1)

        # File input
        ttk.Label(self, text="Input file").grid(row=0, column=0, sticky="w")
        row0 = ttk.Frame(self)
        row0.grid(row=0, column=1, sticky="ew", pady=(0, 6))
        row0.columnconfigure(0, weight=1)
        ttk.Entry(row0, textvariable=self.var_file).grid(row=0, column=0, sticky="ew")
        ttk.Button(row0, text="Browse…", command=self.pick_file).grid(row=0, column=1, padx=(6,0))

        # Operation
        ttk.Label(self, text="Operation").grid(row=1, column=0, sticky="w")
        row1 = ttk.Frame(self)
        row1.grid(row=1, column=1, sticky="w", pady=(0, 6))
        for i, (val, text) in enumerate((
            ("annotate", "Annotate"),
            ("strip", "Strip"),
            ("map", "Map"),
            ("ast", "AST (Python)"),
        )):
            rb = ttk.Radiobutton(row1, value=val, text=text, variable=self.var_op, command=self._update_out_suggestion)
            rb.grid(row=0, column=i, padx=(0,12))

        # Annotate options
        self.annot_frame = ttk.LabelFrame(self, text="Annotate options")
        self.annot_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10), ipadx=5, ipady=5)
        for c in range(0, 6):
            self.annot_frame.columnconfigure(c, weight=0)
        self.annot_frame.columnconfigure(3, weight=1)

        ttk.Label(self.annot_frame, text="Style").grid(row=0, column=0, sticky="w", padx=(5,0))
        style_cb = ttk.Combobox(self.annot_frame, values=STYLES, textvariable=self.var_style, width=10, state="readonly")
        style_cb.grid(row=0, column=1, sticky="w", padx=(6, 18))
        style_cb.bind("<<ComboboxSelected>>", lambda e: self._update_out_suggestion())

        ttk.Label(self.annot_frame, text="Start").grid(row=0, column=2, sticky="e")
        ttk.Spinbox(self.annot_frame, from_=1, to=10_000_000, textvariable=self.var_start, width=8).grid(row=0, column=3, sticky="w", padx=(6, 18))

        ttk.Label(self.annot_frame, text="Min Width (0=auto)").grid(row=0, column=4, sticky="e")
        ttk.Spinbox(self.annot_frame, from_=0, to=12, textvariable=self.var_width, width=6).grid(row=0, column=5, sticky="w", padx=(6,5))

        # AST options
        self.ast_frame = ttk.LabelFrame(self, text="AST options (Python)")
        self.ast_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10), ipadx=5, ipady=5)
        self.ast_frame.columnconfigure(1, weight=1)
        ttk.Label(self.ast_frame, text="Mode").grid(row=0, column=0, sticky="w", padx=(5,0))
        ast_cb = ttk.Combobox(self.ast_frame, values=AST_MODES, textvariable=self.var_ast_mode, width=10, state="readonly")
        ast_cb.grid(row=0, column=1, sticky="w", padx=(6, 18))
        ast_cb.bind("<<ComboboxSelected>>", lambda e: self._update_out_suggestion())

        # Output
        ttk.Label(self, text="Output path").grid(row=4, column=0, sticky="w")
        row3 = ttk.Frame(self)
        row3.grid(row=4, column=1, sticky="ew", pady=(0, 6))
        row3.columnconfigure(0, weight=1)
        ttk.Entry(row3, textvariable=self.var_out).grid(row=0, column=0, sticky="ew")
        ttk.Button(row3, text="Change…", command=self.pick_out).grid(row=0, column=1, padx=(6,0))

        # Action buttons
        bar = ttk.Frame(self)
        bar.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 6))
        bar.columnconfigure(0, weight=1)
        self.btn_run = ttk.Button(bar, text="Run Operation", command=self.on_run, style="Accent.TButton")
        self.btn_run.grid(row=0, column=1, sticky="e")

        # Log output (Deep Background Box)
        ttk.Label(self, text="System Log").grid(row=6, column=0, sticky="w", pady=(5,0))
        
        log_container = tk.Frame(self, bg=self.C_DEEP, bd=1, relief="solid", highlightthickness=0)
        log_container.grid(row=7, column=0, columnspan=2, sticky="nsew", pady=(2, 0))
        
        self.log_scroll = tk.Scrollbar(log_container, bg=self.C_SEC)
        self.log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log = tk.Text(log_container, height=8, wrap="word", bg=self.C_DEEP, fg=self.C_SUC, 
                           font=("Consolas", 10), relief="flat", padx=10, pady=10, 
                           yscrollcommand=self.log_scroll.set, insertbackground="#FFF")
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_scroll.config(command=self.log.yview)
        
        self.log.configure(state="disabled")

        self._update_controls()

    # ------------- Theming helpers -------------
    def _setup_theme(self):
        style = ttk.Style(self.master)
        style.theme_use("clam")

        # Global
        style.configure(".", background=self.C_PRI, foreground=self.C_TXT, font=("Segoe UI", 9))
        style.configure("TFrame", background=self.C_PRI)
        style.configure("TLabel", background=self.C_PRI, foreground=self.C_TXT)
        
        # Radiobuttons
        style.configure("TRadiobutton", background=self.C_PRI, foreground=self.C_TXT, indicatorcolor=self.C_INP)
        style.map("TRadiobutton", background=[("active", self.C_PRI)], indicatorcolor=[("selected", self.C_ACC)])

        # LabelFrames
        style.configure("TLabelframe", background=self.C_PRI, bordercolor=self.C_SEC)
        style.configure("TLabelframe.Label", background=self.C_PRI, foreground=self.C_ACC, font=("Segoe UI", 9, "bold"))

        # Inputs (Entry, Combobox, Spinbox)
        style.configure("TEntry", fieldbackground=self.C_INP, foreground="#FFF", bordercolor=self.C_SEC, lightcolor=self.C_INP, darkcolor=self.C_INP, insertcolor="#FFF")
        style.map("TEntry", fieldbackground=[("disabled", self.C_PRI)], foreground=[("disabled", "#555")])

        style.configure("TCombobox", fieldbackground=self.C_INP, background=self.C_SEC, foreground="#FFF", arrowcolor=self.C_ACC, bordercolor=self.C_SEC)
        style.map("TCombobox", 
                  fieldbackground=[("readonly", self.C_INP), ("disabled", self.C_PRI)], 
                  selectbackground=[("readonly", self.C_ACC)], 
                  selectforeground=[("readonly", "#FFF")],
                  foreground=[("disabled", "#555")])

        style.configure("TSpinbox", fieldbackground=self.C_INP, background=self.C_SEC, foreground="#FFF", arrowcolor=self.C_ACC, bordercolor=self.C_SEC)
        style.map("TSpinbox", fieldbackground=[("disabled", self.C_PRI)], foreground=[("disabled", "#555")])

        # Buttons
        style.configure("TButton", background=self.C_SEC, foreground="#FFF", bordercolor=self.C_SEC, focuscolor=self.C_ACC, font=("Segoe UI", 9))
        style.map("TButton", background=[("active", self.C_ACC)], foreground=[("active", "#FFF")])
        
        # Highlighted Accent Button (Run)
        style.configure("Accent.TButton", background=self.C_ACC, foreground="#FFF", font=("Segoe UI", 9, "bold"))
        style.map("Accent.TButton", background=[("active", "#005a9e")], foreground=[("active", "#FFF")])


    # ------------- UI helpers -------------
    def pick_file(self):
        path = filedialog.askopenfilename(title="Choose a text file")
        if path:
            self.var_file.set(path)
            self._update_out_suggestion()

    def pick_out(self):
        base = self.var_out.get() or default_output_for(self.var_file.get(), self.var_op.get(), self.var_style.get(), self.var_ast_mode.get())
        initialdir = os.path.dirname(base) if base else None
        initialfile = os.path.basename(base) if base else None
        path = filedialog.asksaveasfilename(title="Save output as", initialdir=initialdir, initialfile=initialfile)
        if path:
            self.var_out.set(path)

    def _update_out_suggestion(self):
        self.var_out.set(default_output_for(self.var_file.get(), self.var_op.get(), self.var_style.get(), self.var_ast_mode.get()))
        self._update_controls()

    def _update_controls(self):
        annot = (self.var_op.get() == "annotate")
        for child in self.annot_frame.winfo_children():
            try:
                child.configure(state=("!disabled" if annot else "disabled"))
            except tk.TclError:
                pass

        ast_enabled = (self.var_op.get() == "ast")
        for child in self.ast_frame.winfo_children():
            try:
                child.configure(state=("!disabled" if ast_enabled else "disabled"))
            except tk.TclError:
                pass

    def _append_log(self, msg: str):
        self.log.configure(state="normal")
        self.log.insert("end", msg.rstrip()+"\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def on_run(self):
        infile = self.var_file.get().strip()
        if not infile:
            messagebox.showerror(APP_TITLE, "Please choose an input file.")
            return
        if not os.path.isfile(infile):
            messagebox.showerror(APP_TITLE, "Input path does not exist or is not a file.")
            return

        op = self.var_op.get()
        out = self.var_out.get().strip() or default_output_for(infile, op, self.var_style.get(), self.var_ast_mode.get())
        argv = [op, infile]

        if op == "annotate":
            argv += ["--out", out, "--style", self.var_style.get(), "--start", str(self.var_start.get()), "--width", str(self.var_width.get())]
        elif op == "strip":
            argv += ["--out", out]
        elif op == "map":
            argv += ["--out", out]
        elif op == "ast":
            argv += ["--out", out, "--mode", self.var_ast_mode.get()]
        else:
            messagebox.showerror(APP_TITLE, f"Unknown operation: {op}")
            return

        self.btn_run.configure(state="disabled")
        self._append_log(f"> linenumberizer {' '.join(argv)}")

        def done(ok: bool, msg: str):
            self.after(0, self._on_done, ok, msg)

        run_cli_async(argv, done)

    def _on_done(self, ok: bool, msg: str):
        self.btn_run.configure(state="normal")
        if ok:
            self._append_log(f"[SUCCESS] {msg}")
            messagebox.showinfo(APP_TITLE, "Operation completed successfully.")
        else:
            self._append_log(f"[ERROR] {msg}")
            messagebox.showerror(APP_TITLE, "Failed – see log for details.")

# ----------------------------
# Entrypoint
# ----------------------------

def main():
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.2)
    except tk.TclError:
        pass
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()