"""gui_main.py — HyperNeuron Emitter v2 Tkinter GUI.

Tabs
----
Train      Select a corpus directory and run the BPE → NPMI → SVD pipeline.
           Writes tokenizer.json, embeddings.npy, inhibit_edges.json to the
           configured artifacts directory.

Embed      Embed a text snippet using the loaded DeterministicEmbedProvider.
           Displays token pills, vector heatmap bar, and first-8 values.

Nucleus    Run the Bootstrap Nucleus on two text snippets.
           Shows ConnectionStrength, RoutingProfile, and InteractionType.

Inspect    Load a JSON file of HyperHunk records and display surface richness
           for each hunk using the HunkSurveyor.

V1 reference: _BDHyperNeuronEMITTER/src/ui.py
V2 changes:
    - Replaced v1 core.* calls with v2 inference/nucleus/surveyor equivalents
    - Tab-based layout replaces single-panel layout
    - Added Nucleus Demo and Inspect tabs (new in v2)
    - Train now targets a corpus directory (not a single file)
    - Removed v1 Tokenize / Chunk / Reverse actions (Splitter owns those in v2)
"""

from __future__ import annotations

import json
import logging
import math
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# ── Colour palette (matches v1) ───────────────────────────────────────────────

BG_DARK    = "#0d1117"
BG_PANEL   = "#161b22"
BG_CARD    = "#1c2129"
FG_TEXT    = "#c9d1d9"
FG_DIM     = "#8b949e"
ACCENT_BLUE   = "#58a6ff"
ACCENT_PURPLE = "#bc8cff"
ACCENT_GREEN  = "#3fb950"
ACCENT_AMBER  = "#e3b341"
ACCENT_RED    = "#da3633"
BORDER     = "#30363d"


# ── Splash screen (preserved from v1) ────────────────────────────────────────

class SplashScreen(tk.Toplevel):
    """Borderless loading popup that draws the Emitter logo on a canvas."""

    WIDTH  = 380
    HEIGHT = 400

    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg=BG_DARK)
        self.attributes("-topmost", True)
        self._center()
        self.canvas = tk.Canvas(
            self, width=self.WIDTH, height=self.HEIGHT,
            bg=BG_DARK, highlightthickness=0,
        )
        self.canvas.pack()
        self._draw_logo()

    def _center(self):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - self.WIDTH)  // 2
        y  = (sh - self.HEIGHT) // 2
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

    def _draw_logo(self):
        c = self.canvas
        cx, cy = self.WIDTH // 2, 160

        hex_r   = 110
        hex_pts = _hex_points(cx, cy, hex_r)
        c.create_polygon(hex_pts, outline=ACCENT_BLUE, fill="", width=1.5)

        inner_r  = 70
        node_pts = _hex_points(cx, cy, inner_r)
        node_radii = [8, 6, 6, 7, 7, 8]

        for i in range(6):
            j  = (i + 1) % 6
            x1, y1 = node_pts[i * 2], node_pts[i * 2 + 1]
            x2, y2 = node_pts[j * 2], node_pts[j * 2 + 1]
            c.create_line(x1, y1, x2, y2, fill=ACCENT_BLUE, width=1.2)

        for a, b in [(0, 3), (1, 4), (2, 5)]:
            x1, y1 = node_pts[a * 2], node_pts[a * 2 + 1]
            x2, y2 = node_pts[b * 2], node_pts[b * 2 + 1]
            c.create_line(x1, y1, x2, y2, fill=ACCENT_PURPLE, width=0.8, dash=(4, 4))

        for i, r in enumerate(node_radii):
            nx, ny = node_pts[i * 2], node_pts[i * 2 + 1]
            colour = ACCENT_BLUE if i % 2 == 0 else ACCENT_PURPLE
            c.create_oval(nx - r, ny - r, nx + r, ny + r, fill=colour, outline="")

        c.create_text(cx, 290, text="HyperNeuron",
                      font=("Segoe UI", 22, "bold"), fill=ACCENT_BLUE)
        c.create_text(cx, 322, text="EMITTER v2  ·  RELATIONAL FIELD ENGINE",
                      font=("Segoe UI", 8), fill=FG_DIM)
        self._loading_text = c.create_text(
            cx, 360, text="Loading...", font=("Segoe UI", 9), fill=FG_DIM,
        )


def _hex_points(cx: float, cy: float, r: float) -> List[float]:
    pts: List[float] = []
    for i in range(6):
        angle = math.radians(60 * i - 90)
        pts.append(cx + r * math.cos(angle))
        pts.append(cy + r * math.sin(angle))
    return pts


# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(tk.Tk):
    """Tabbed v2 inspection window."""

    def __init__(self, artifacts_dir: str = "./artifacts", db_path: str = "./cold_anatomy.db"):
        super().__init__()
        self.title("HyperNeuron Emitter v2")
        self.configure(bg=BG_DARK)
        self.minsize(960, 660)
        self._center(1060, 740)

        self._artifacts_dir = tk.StringVar(value=str(artifacts_dir))
        self._db_path       = tk.StringVar(value=str(db_path))
        self._embed_provider: Optional[Any] = None
        self._ui_queue: "queue.Queue[tuple[Any, tuple[Any, ...], dict[str, Any]]]" = queue.Queue()
        self._closing = False

        self._build_styles()
        self._build_toolbar()
        self._build_notebook()
        self._build_statusbar()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(50, self._drain_ui_queue)

        # Auto-load provider if artifacts exist
        self._try_load_provider()

    # ── Geometry ──────────────────────────────────────────────────────────────

    def _center(self, w: int, h: int):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    # ── Styles ────────────────────────────────────────────────────────────────

    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Dark.TFrame",  background=BG_DARK)
        style.configure("Panel.TFrame", background=BG_PANEL)
        style.configure("Card.TFrame",  background=BG_CARD)
        style.configure("Dark.TLabel",   background=BG_DARK,  foreground=FG_TEXT,
                         font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=BG_DARK,  foreground=ACCENT_BLUE,
                         font=("Segoe UI", 11, "bold"))
        style.configure("Dim.TLabel",    background=BG_DARK,  foreground=FG_DIM,
                         font=("Segoe UI", 9))
        style.configure("Status.TLabel", background=BG_PANEL, foreground=FG_DIM,
                         font=("Segoe UI", 9), padding=(8, 4))
        style.configure("Toolbar.TButton", background=BG_PANEL, foreground=FG_TEXT,
                         borderwidth=1, focuscolor=ACCENT_BLUE, padding=(12, 6))
        style.map("Toolbar.TButton", background=[("active", BG_CARD)])
        style.configure("Accent.TButton", background=ACCENT_BLUE, foreground=BG_DARK,
                         borderwidth=0, padding=(14, 7), font=("Segoe UI", 9, "bold"))
        style.configure("Clear.TButton", background=ACCENT_RED, foreground="#ffffff",
                         borderwidth=0, padding=(14, 7), font=("Segoe UI", 9, "bold"))
        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_PANEL, foreground=FG_DIM,
                         padding=(14, 6), font=("Segoe UI", 9))
        style.map("TNotebook.Tab",
                  background=[("selected", BG_CARD)],
                  foreground=[("selected", ACCENT_BLUE)])

    # ── Toolbar ───────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        bar = ttk.Frame(self, style="Panel.TFrame")
        bar.pack(fill=tk.X)

        tk.Label(bar, text="  HyperNeuron  ", font=("Segoe UI", 12, "bold"),
                 foreground=ACCENT_BLUE, background=BG_PANEL).pack(side=tk.LEFT, padx=(8, 16))

        self._model_indicator = tk.Label(
            bar, text="● No model", font=("Segoe UI", 9), fg=FG_DIM, bg=BG_PANEL,
        )
        self._model_indicator.pack(side=tk.LEFT, padx=(0, 16))

        tk.Frame(bar, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=6)

        ttk.Button(bar, text="Load Provider", command=self._on_load_provider,
                   style="Toolbar.TButton").pack(side=tk.LEFT, padx=2, pady=4)
        ttk.Button(bar, text="Clear Results", command=self._on_clear,
                   style="Clear.TButton").pack(side=tk.RIGHT, padx=8, pady=4)

    # ── Notebook ──────────────────────────────────────────────────────────────

    def _build_notebook(self):
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 0))

        self._tab_train   = self._make_scrollable_tab("Train")
        self._tab_embed   = self._make_scrollable_tab("Embed")
        self._tab_nucleus = self._make_scrollable_tab("Nucleus")
        self._tab_inspect = self._make_scrollable_tab("Inspect")

        self._build_train_tab()
        self._build_embed_tab()
        self._build_nucleus_tab()
        self._build_inspect_tab()

    def _make_scrollable_tab(self, title: str) -> tk.Frame:
        """Create a tab with a scrollable inner frame. Returns the inner frame."""
        outer = ttk.Frame(self._nb, style="Dark.TFrame")
        self._nb.add(outer, text=f"  {title}  ")

        canvas = tk.Canvas(outer, bg=BG_DARK, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        inner = ttk.Frame(canvas, style="Dark.TFrame")

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=inner, anchor=tk.NW)
        canvas.configure(yscrollcommand=sb.set)
        canvas.bind("<Configure>",
                    lambda e, c=canvas, w=win: c.itemconfig(w, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        return inner

    # ── Train tab ─────────────────────────────────────────────────────────────

    def _build_train_tab(self):
        p = self._tab_train
        pad = {"padx": 16, "pady": 6}

        ttk.Label(p, text="Train BPE Embeddings", style="Header.TLabel").pack(
            anchor=tk.W, **pad)
        ttk.Label(p, text="Point at a corpus directory of .txt files to train the BPE tokenizer,\n"
                           "build the NPMI co-occurrence matrix, and compute SVD embeddings.",
                  style="Dim.TLabel").pack(anchor=tk.W, padx=16, pady=(0, 12))

        # Corpus dir row
        self._corpus_var = tk.StringVar()
        row_corpus = ttk.Frame(p, style="Dark.TFrame")
        row_corpus.pack(fill=tk.X, padx=16, pady=4)
        ttk.Label(row_corpus, text="Corpus dir:", style="Dark.TLabel", width=14).pack(side=tk.LEFT)
        tk.Entry(row_corpus, textvariable=self._corpus_var, bg=BG_PANEL, fg=FG_TEXT,
                 insertbackground=ACCENT_BLUE, font=("Consolas", 9), relief=tk.FLAT,
                 width=48).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(row_corpus, text="Browse", style="Toolbar.TButton",
                   command=self._browse_corpus).pack(side=tk.LEFT)

        # Artifacts dir row
        row_art = ttk.Frame(p, style="Dark.TFrame")
        row_art.pack(fill=tk.X, padx=16, pady=4)
        ttk.Label(row_art, text="Artifacts dir:", style="Dark.TLabel", width=14).pack(side=tk.LEFT)
        tk.Entry(row_art, textvariable=self._artifacts_dir, bg=BG_PANEL, fg=FG_TEXT,
                 insertbackground=ACCENT_BLUE, font=("Consolas", 9), relief=tk.FLAT,
                 width=48).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(row_art, text="Browse", style="Toolbar.TButton",
                   command=lambda: self._browse_dir(self._artifacts_dir)).pack(side=tk.LEFT)

        # Vocab + dims
        param_row = ttk.Frame(p, style="Dark.TFrame")
        param_row.pack(fill=tk.X, padx=16, pady=4)
        ttk.Label(param_row, text="Vocab size:", style="Dark.TLabel").pack(side=tk.LEFT)
        self._vocab_var = tk.IntVar(value=8192)
        tk.Spinbox(param_row, from_=1000, to=50000, increment=1000,
                   textvariable=self._vocab_var, width=8, bg=BG_PANEL, fg=FG_TEXT,
                   buttonbackground=BG_CARD, font=("Consolas", 9), relief=tk.FLAT,
                   ).pack(side=tk.LEFT, padx=(4, 24))
        ttk.Label(param_row, text="SVD dims:", style="Dark.TLabel").pack(side=tk.LEFT)
        self._dims_var = tk.IntVar(value=300)
        tk.Spinbox(param_row, from_=50, to=1000, increment=50,
                   textvariable=self._dims_var, width=6, bg=BG_PANEL, fg=FG_TEXT,
                   buttonbackground=BG_CARD, font=("Consolas", 9), relief=tk.FLAT,
                   ).pack(side=tk.LEFT, padx=4)

        ttk.Button(p, text="Run Training Pipeline", style="Accent.TButton",
                   command=self._on_train).pack(anchor=tk.W, padx=16, pady=(12, 4))

        # Progress / results display area
        self._train_results = tk.Frame(p, bg=BG_CARD, padx=12, pady=10)
        self._train_results.pack(fill=tk.X, padx=16, pady=8)
        self._train_log_var = tk.StringVar(value="No training run yet.")
        tk.Label(self._train_results, textvariable=self._train_log_var,
                 font=("Consolas", 9), fg=FG_DIM, bg=BG_CARD,
                 justify=tk.LEFT, anchor=tk.W).pack(fill=tk.X)

    def _browse_corpus(self):
        d = filedialog.askdirectory(title="Select corpus directory")
        if d:
            self._corpus_var.set(d)

    def _browse_dir(self, var: tk.StringVar):
        d = filedialog.askdirectory(title="Select directory")
        if d:
            var.set(d)

    def _queue_ui(self, callback, *args, **kwargs):
        if not self._closing:
            self._ui_queue.put((callback, args, kwargs))

    def _drain_ui_queue(self):
        if self._closing:
            return
        while True:
            try:
                callback, args, kwargs = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                callback(*args, **kwargs)
            except Exception:
                log.exception("Queued UI callback failed: %r", callback)
        if not self._closing:
            self.after(50, self._drain_ui_queue)

    def _on_close(self):
        self._closing = True
        self.destroy()

    def _on_train(self):
        corpus = self._corpus_var.get().strip()
        if not corpus:
            messagebox.showwarning("Train", "Please select a corpus directory first.")
            return

        self._set_status("Training... (this may take a while)")
        self._model_indicator.config(text="● Training...", fg=ACCENT_AMBER)
        self._train_log_var.set("Starting training pipeline...")

        def _run():
            try:
                # Import training modules
                from ..core.engine.training.bpe_trainer import BPETrainer
                from ..core.engine.training.cooccurrence import compute_counts
                from ..core.engine.training.npmi_matrix import build_npmi_matrix_with_inhibits
                from ..core.engine.training.spectral import compute_embeddings
                import numpy as np

                artifacts_dir = Path(self._artifacts_dir.get().strip() or "./artifacts")
                artifacts_dir.mkdir(parents=True, exist_ok=True)
                vocab_size = self._vocab_var.get()
                dims       = self._dims_var.get()

                self._queue_ui(self._train_log_var.set, "Step 1/4 — BPE training...")

                # Import the BPE-encode helper from app.py
                from .. import app as _app

                trainer = BPETrainer(vocab_size=vocab_size)
                trainer.train(corpus)
                trainer.save(artifacts_dir / "tokenizer.json")

                self._queue_ui(
                    self._train_log_var.set,
                    f"Step 2/4 — Encoding corpus ({len(trainer.vocab)} tokens)...",
                )

                corpus_token_ids = _app._encode_corpus_to_token_ids(
                    Path(corpus), trainer.vocab, trainer.merges, trainer.end_of_word,
                )

                self._queue_ui(
                    self._train_log_var.set,
                    f"Step 3/4 — NPMI matrix ({len(corpus_token_ids)} sequences)...",
                )

                matrix_result = compute_counts(corpus_token_ids, window_size=5)
                npmi_result = build_npmi_matrix_with_inhibits(
                    pair_counts=matrix_result.pair_counts,
                    token_counts=matrix_result.token_counts,
                    vocab_size=len(trainer.vocab),
                )

                self._queue_ui(self._train_log_var.set, f"Step 4/4 — SVD (k={dims})...")

                k = min(dims, npmi_result.matrix.shape[0] - 1)
                embeddings = compute_embeddings(npmi_result.matrix, k=k)
                np.save(str(artifacts_dir / "embeddings.npy"), embeddings)

                inhibit_data = [
                    {"token_a": e.token_a, "token_b": e.token_b, "weight": e.weight}
                    for e in npmi_result.inhibit_edges
                ]
                with open(artifacts_dir / "inhibit_edges.json", "w") as f:
                    json.dump(inhibit_data, f, indent=2)

                summary = (
                    f"Training complete!\n"
                    f"  Vocabulary: {len(trainer.vocab)} tokens\n"
                    f"  Embeddings: {embeddings.shape}\n"
                    f"  Inhibit edges: {len(inhibit_data)}\n"
                    f"  Artifacts: {artifacts_dir}"
                )
                self._queue_ui(self._train_log_var.set, summary)
                self._queue_ui(self._on_load_provider)

            except Exception as exc:
                msg = f"Training failed: {exc}"
                log.error(msg, exc_info=True)
                self._queue_ui(self._train_log_var.set, msg)
                self._queue_ui(self._model_indicator.config, text="● Error", fg=ACCENT_RED)
                self._queue_ui(self._set_status, msg)

        threading.Thread(target=_run, daemon=True).start()

    # ── Embed tab ─────────────────────────────────────────────────────────────

    def _build_embed_tab(self):
        p = self._tab_embed

        ttk.Label(p, text="Embed Text", style="Header.TLabel").pack(
            anchor=tk.W, padx=16, pady=(12, 4))
        ttk.Label(p, text="Enter text to embed using the loaded DeterministicEmbedProvider.\n"
                           "Displays BPE tokens, vector heatmap, and first-8 dimension values.",
                  style="Dim.TLabel").pack(anchor=tk.W, padx=16, pady=(0, 8))

        self._embed_text = tk.Text(
            p, width=80, height=6, bg=BG_PANEL, fg=FG_TEXT,
            insertbackground=ACCENT_BLUE, selectbackground=ACCENT_PURPLE,
            font=("Consolas", 10), relief=tk.FLAT, padx=8, pady=8, wrap=tk.WORD,
        )
        self._embed_text.pack(fill=tk.X, padx=16, pady=(0, 8))
        self._embed_text.insert("1.0", "The Bootstrap Nucleus evaluates structural and "
                                        "grammatical surfaces to score cross-hunk connections.")

        ttk.Button(p, text="Embed Text", style="Accent.TButton",
                   command=self._on_embed).pack(anchor=tk.W, padx=16, pady=(0, 8))

        # Results area (dynamically populated)
        self._embed_results_frame = ttk.Frame(p, style="Dark.TFrame")
        self._embed_results_frame.pack(fill=tk.BOTH, expand=True, padx=16)

    def _on_embed(self):
        if self._embed_provider is None:
            messagebox.showwarning("Embed", "Load trained artifacts first (Load Provider).")
            return

        text = self._embed_text.get("1.0", tk.END).strip()
        if not text:
            self._set_status("Enter some text first.")
            return

        for w in self._embed_results_frame.winfo_children():
            w.destroy()

        self._set_status("Embedding...")
        try:
            result = self._embed_provider.embed([text])
        except Exception as exc:
            self._set_status(f"Embed failed: {exc}")
            return

        if not result.vectors:
            self._set_status("Embed returned no vectors.")
            return

        vector   = result.vectors[0]
        tok_ids  = result.token_ids[0]
        tok_count = result.token_counts[0]

        sec = self._add_card(self._embed_results_frame, "Embed Result")
        self._add_kv(sec, "text (truncated)", text[:80] + ("..." if len(text) > 80 else ""))
        self._add_kv(sec, "BPE tokens",  str(tok_count))
        self._add_kv(sec, "dimensions",  str(len(vector)))
        self._add_kv(sec, "token IDs",   str(tok_ids[:16]) + ("..." if len(tok_ids) > 16 else ""))

        self._add_vector_bar(sec, vector, label="embedding")

        vals = "  ".join(f"{v:+.4f}" for v in vector[:8])
        tk.Label(sec, text=f"[{vals}{'  ...' if len(vector) > 8 else ''}]",
                 font=("Consolas", 8), fg=FG_DIM, bg=BG_CARD, anchor=tk.W,
                 ).pack(fill=tk.X, pady=(2, 0))

        self._set_status(f"Embedded {tok_count} tokens → {len(vector)}d vector.")

    # ── Nucleus tab ───────────────────────────────────────────────────────────

    def _build_nucleus_tab(self):
        p = self._tab_nucleus

        ttk.Label(p, text="Bootstrap Nucleus Demo", style="Header.TLabel").pack(
            anchor=tk.W, padx=16, pady=(12, 4))
        ttk.Label(p, text="Enter two text snippets. The Nucleus evaluates per-surface similarity\n"
                           "and returns a ConnectionStrength + RoutingProfile.",
                  style="Dim.TLabel").pack(anchor=tk.W, padx=16, pady=(0, 8))

        # Hunk A
        ttk.Label(p, text="Hunk A  (node_kind: function_def)", style="Dark.TLabel").pack(
            anchor=tk.W, padx=16)
        self._nucleus_a = tk.Text(
            p, width=80, height=5, bg=BG_PANEL, fg=FG_TEXT,
            insertbackground=ACCENT_BLUE, font=("Consolas", 10),
            relief=tk.FLAT, padx=8, pady=8, wrap=tk.WORD,
        )
        self._nucleus_a.pack(fill=tk.X, padx=16, pady=(2, 8))
        self._nucleus_a.insert("1.0", "def authenticate_user(username: str, password: str) -> bool:\n"
                                       "    \"\"\"Verify credentials against the user database.\"\"\"\n"
                                       "    return db.check_credentials(username, password)")

        # Hunk B
        ttk.Label(p, text="Hunk B  (node_kind: function_def)", style="Dark.TLabel").pack(
            anchor=tk.W, padx=16)
        self._nucleus_b = tk.Text(
            p, width=80, height=5, bg=BG_PANEL, fg=FG_TEXT,
            insertbackground=ACCENT_BLUE, font=("Consolas", 10),
            relief=tk.FLAT, padx=8, pady=8, wrap=tk.WORD,
        )
        self._nucleus_b.pack(fill=tk.X, padx=16, pady=(2, 8))
        self._nucleus_b.insert("1.0", "def verify_token(token: str) -> bool:\n"
                                       "    \"\"\"Validate an auth token from the request header.\"\"\"\n"
                                       "    return jwt.decode(token) is not None")

        # Edge threshold
        thresh_row = ttk.Frame(p, style="Dark.TFrame")
        thresh_row.pack(anchor=tk.W, padx=16, pady=(0, 8))
        ttk.Label(thresh_row, text="Edge threshold:", style="Dark.TLabel").pack(side=tk.LEFT)
        self._thresh_var = tk.DoubleVar(value=0.3)
        tk.Spinbox(thresh_row, from_=0.0, to=1.0, increment=0.05,
                   textvariable=self._thresh_var, format="%.2f", width=6,
                   bg=BG_PANEL, fg=FG_TEXT, buttonbackground=BG_CARD,
                   font=("Consolas", 9), relief=tk.FLAT,
                   ).pack(side=tk.LEFT, padx=4)

        ttk.Button(p, text="Run Nucleus", style="Accent.TButton",
                   command=self._on_nucleus).pack(anchor=tk.W, padx=16, pady=(0, 8))

        self._nucleus_results_frame = ttk.Frame(p, style="Dark.TFrame")
        self._nucleus_results_frame.pack(fill=tk.BOTH, expand=True, padx=16)

    def _on_nucleus(self):
        from ..core.nucleus.bootstrap import BootstrapNucleus
        from ..core.contract.hyperhunk import EmitterHyperHunk

        text_a = self._nucleus_a.get("1.0", tk.END).strip()
        text_b = self._nucleus_b.get("1.0", tk.END).strip()
        if not text_a or not text_b:
            self._set_status("Both hunk fields must be non-empty.")
            return

        for w in self._nucleus_results_frame.winfo_children():
            w.destroy()

        threshold = self._thresh_var.get()

        # Build minimal EmitterHyperHunks from the input text
        hunk_a = _make_demo_hunk(text_a, "function_def", "hunkA", 0)
        hunk_b = _make_demo_hunk(text_b, "function_def", "hunkB", 1)

        # Attach embeddings if provider available
        if self._embed_provider is not None:
            try:
                res_a = self._embed_provider.embed([text_a])
                res_b = self._embed_provider.embed([text_b])
                if res_a.vectors:
                    hunk_a.embedding = res_a.vectors[0]
                if res_b.vectors:
                    hunk_b.embedding = res_b.vectors[0]
            except Exception as exc:
                log.warning("Embedding for Nucleus demo failed: %s", exc)

        nucleus = BootstrapNucleus(edge_threshold=threshold)
        result  = nucleus.evaluate(hunk_a, hunk_b)

        sec = self._add_card(self._nucleus_results_frame, "Nucleus Result")
        self._add_kv(sec, "strength",      f"{result.connection_strength:.4f}")
        self._add_kv(sec, "above threshold", str(result.above_threshold))
        self._add_kv(sec, "interaction",   result.interaction_type)

        profile = result.routing_profile
        ttk.Label(sec, text="Routing Profile:", font=("Segoe UI", 9, "bold"),
                  foreground=ACCENT_BLUE, background=BG_CARD).pack(anchor=tk.W, pady=(6, 2))

        for surface, weight in sorted(profile.items(), key=lambda kv: -kv[1]):
            bar_row = tk.Frame(sec, bg=BG_CARD)
            bar_row.pack(fill=tk.X, pady=1)
            tk.Label(bar_row, text=f"{surface:<14}", font=("Consolas", 9),
                     fg=FG_DIM, bg=BG_CARD, width=14, anchor=tk.W).pack(side=tk.LEFT)
            bar_c = tk.Canvas(bar_row, height=14, bg=BG_CARD, highlightthickness=0)
            bar_c.pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(bar_row, text=f"{weight:.3f}", font=("Consolas", 9),
                     fg=FG_TEXT, bg=BG_CARD, width=6).pack(side=tk.LEFT)

            def _draw_bar(event=None, bv=weight, bc=bar_c):
                bc.delete("all")
                w = bc.winfo_width()
                bar_len = int(bv * w)
                if bar_len > 0:
                    bc.create_rectangle(0, 1, bar_len, 13,
                                        fill=ACCENT_BLUE if bv > 0.2 else ACCENT_PURPLE, outline="")

            bar_c.bind("<Configure>", _draw_bar)

        vector = result.interaction_vector
        self._add_vector_bar(sec, vector, label="interaction vec")

        self._set_status(
            f"Nucleus: strength={result.connection_strength:.4f}  "
            f"type={result.interaction_type}  "
            f"edge={'YES' if result.above_threshold else 'NO'}"
        )

    # ── Inspect tab ───────────────────────────────────────────────────────────

    def _build_inspect_tab(self):
        p = self._tab_inspect

        ttk.Label(p, text="Inspect HyperHunks", style="Header.TLabel").pack(
            anchor=tk.W, padx=16, pady=(12, 4))
        ttk.Label(p, text="Load a HyperHunk NDJSON file and inspect surface richness for each hunk.\n"
                           "Each hunk is surveyed and displayed with its richness metrics.",
                  style="Dim.TLabel").pack(anchor=tk.W, padx=16, pady=(0, 8))

        row = ttk.Frame(p, style="Dark.TFrame")
        row.pack(fill=tk.X, padx=16, pady=(0, 8))
        self._inspect_file_var = tk.StringVar()
        tk.Entry(row, textvariable=self._inspect_file_var, bg=BG_PANEL, fg=FG_TEXT,
                 insertbackground=ACCENT_BLUE, font=("Consolas", 9), relief=tk.FLAT,
                 width=56).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(row, text="Browse NDJSON", style="Toolbar.TButton",
                   command=self._browse_ndjson).pack(side=tk.LEFT)

        ttk.Button(p, text="Inspect File", style="Accent.TButton",
                   command=self._on_inspect).pack(anchor=tk.W, padx=16, pady=(0, 8))

        self._inspect_results_frame = ttk.Frame(p, style="Dark.TFrame")
        self._inspect_results_frame.pack(fill=tk.BOTH, expand=True, padx=16)

    def _browse_ndjson(self):
        path = filedialog.askopenfilename(
            title="Select NDJSON file",
            filetypes=[("NDJSON", "*.ndjson *.jsonl"), ("JSON", "*.json"), ("All", "*.*")],
        )
        if path:
            self._inspect_file_var.set(path)

    def _on_inspect(self):
        from ..core.contract.hyperhunk import HyperHunk as EmitterHyperHunk
        from ..core.surveyor.hyperhunk import HunkSurveyor

        path = self._inspect_file_var.get().strip()
        if not path:
            messagebox.showwarning("Inspect", "Select a NDJSON file first.")
            return

        for w in self._inspect_results_frame.winfo_children():
            w.destroy()

        self._set_status("Inspecting...")

        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as exc:
            self._set_status(f"Cannot open file: {exc}")
            return

        surveyor = HunkSurveyor(strict=False)
        parsed   = 0
        skipped  = 0

        for raw in lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
                hunk   = EmitterHyperHunk.from_dict(record)
                report = surveyor.observe(hunk)
                parsed += 1

                sec = self._add_card(self._inspect_results_frame,
                                     f"{hunk.node_kind}  ·  {hunk.occurrence_id[:12]}...")
                self._add_kv(sec, "origin_id",   hunk.origin_id)
                self._add_kv(sec, "v2 rich",     str(report.is_v2_rich))
                self._add_kv(sec, "token_count", str(report.token_count))
                self._add_kv(sec, "has_embedding", str(report.has_embedding))

                if report.surface_richness:
                    ttk.Label(sec, text="Surface richness:", font=("Segoe UI", 9, "bold"),
                              foreground=ACCENT_BLUE, background=BG_CARD).pack(
                                  anchor=tk.W, pady=(4, 2))
                    for surface, frac in sorted(report.surface_richness.items()):
                        self._add_kv(sec, f"  {surface}", f"{frac:.2f}")

                if report.warnings:
                    warn_str = "  |  ".join(report.warnings[:3])
                    self._add_kv(sec, "warnings", warn_str)

                self._inspect_results_frame.update_idletasks()

            except Exception as exc:
                skipped += 1
                log.warning("Skipped hunk record: %s", exc)

        stream_report = surveyor.finalize()

        # Summary card
        sum_sec = self._add_card(self._inspect_results_frame, "Stream Summary")
        for line in stream_report.summary_lines():
            tk.Label(sum_sec, text=line, font=("Consolas", 9), fg=FG_TEXT, bg=BG_CARD,
                     anchor=tk.W).pack(fill=tk.X)

        self._set_status(f"Inspected {parsed} hunks, {skipped} skipped.")

    # ── Shared UI helpers ─────────────────────────────────────────────────────

    def _add_card(self, parent: tk.Widget, title: str) -> tk.Frame:
        frame = tk.Frame(parent, bg=BG_CARD, padx=12, pady=10)
        frame.pack(fill=tk.X, pady=(0, 6))
        tk.Label(frame, text=title, font=("Segoe UI", 10, "bold"),
                 fg=ACCENT_BLUE, bg=BG_CARD, anchor=tk.W).pack(fill=tk.X, pady=(0, 6))
        return frame

    def _add_kv(self, parent: tk.Frame, key: str, value: str):
        row = tk.Frame(parent, bg=BG_CARD)
        row.pack(fill=tk.X, pady=1)
        tk.Label(row, text=key, font=("Consolas", 9), fg=FG_DIM, bg=BG_CARD,
                 width=16, anchor=tk.W).pack(side=tk.LEFT)
        tk.Label(row, text=value, font=("Consolas", 9), fg=FG_TEXT, bg=BG_CARD,
                 anchor=tk.W, wraplength=520).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _add_vector_bar(self, parent: tk.Frame, vector: List[float], label: str = ""):
        row = tk.Frame(parent, bg=BG_CARD)
        row.pack(fill=tk.X, pady=(4, 2))
        if label:
            tk.Label(row, text=label, font=("Consolas", 8), fg=FG_DIM, bg=BG_CARD,
                     width=14, anchor=tk.W).pack(side=tk.LEFT)
        bar = tk.Canvas(row, height=18, bg=BG_CARD, highlightthickness=0)
        bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def _draw(event=None, v=vector, bc=bar):
            bc.delete("all")
            w = bc.winfo_width()
            if not v or w < 10:
                return
            n = len(v)
            cell_w = max(w // n, 2)
            v_min = min(v)
            v_max = max(v) if max(v) != v_min else v_min + 1
            for i, val in enumerate(v):
                t = (val - v_min) / (v_max - v_min)
                r = int(88  + t * (188 - 88))
                g = int(166 + t * (140 - 166))
                b = 255
                colour = f"#{r:02x}{g:02x}{b:02x}"
                x0 = i * cell_w
                bc.create_rectangle(x0, 0, x0 + cell_w - 1, 18, fill=colour, outline="")

        bar.bind("<Configure>", _draw)

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self):
        self._status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self._status_var, style="Status.TLabel",
                  ).pack(side=tk.BOTTOM, fill=tk.X)

    def _set_status(self, msg: str):
        self._status_var.set(msg)
        self.update_idletasks()

    # ── Provider loading ──────────────────────────────────────────────────────

    def _on_load_provider(self):
        artifacts_dir = Path(self._artifacts_dir.get().strip() or "./artifacts")
        self._try_load_provider(artifacts_dir)

    def _try_load_provider(self, artifacts_dir: Optional[Path] = None):
        if artifacts_dir is None:
            artifacts_dir = Path(self._artifacts_dir.get().strip() or "./artifacts")
        tok_path = artifacts_dir / "tokenizer.json"
        emb_path = artifacts_dir / "embeddings.npy"
        if tok_path.is_file() and emb_path.is_file():
            try:
                from ..core.engine.inference.provider import DeterministicEmbedProvider
                self._embed_provider = DeterministicEmbedProvider(tok_path, emb_path)
                self._model_indicator.config(text="● Model ready", fg=ACCENT_GREEN)
                self._set_status(f"Provider loaded from {artifacts_dir}")
            except Exception as exc:
                self._embed_provider = None
                self._model_indicator.config(text="● Load error", fg=ACCENT_RED)
                self._set_status(f"Provider load failed: {exc}")
        else:
            self._embed_provider = None
            self._model_indicator.config(text="● No model", fg=FG_DIM)
            self._set_status(f"No trained artifacts at {artifacts_dir}")

    # ── Clear ─────────────────────────────────────────────────────────────────

    def _on_clear(self):
        for frame in (self._embed_results_frame,
                      self._nucleus_results_frame,
                      self._inspect_results_frame):
            for w in frame.winfo_children():
                w.destroy()
        self._set_status("Cleared.")


# ── Demo hunk factory ─────────────────────────────────────────────────────────

def _make_demo_hunk(content: str, node_kind: str, origin_id: str, sibling_index: int):
    """Build a minimal HyperHunk for Nucleus demo inputs."""
    from ..core.contract.hyperhunk import HyperHunk

    doc_pos = sibling_index / max(sibling_index + 1, 1)
    return HyperHunk(
        content=content,
        origin_id=origin_id,
        node_kind=node_kind,
        layer_type="demo",
        structural_path=f"/{origin_id}/{node_kind}",
        sibling_index=sibling_index,
        document_position=float(doc_pos),
        extraction_confidence=1.0,
        token_count=len(content.split()),
    )


# ── Entry point ───────────────────────────────────────────────────────────────

def main(artifacts_dir: str = "./artifacts", db_path: str = "./cold_anatomy.db"):
    """Launch the GUI. Called from app.py cmd_ui()."""
    root = MainWindow(artifacts_dir=artifacts_dir, db_path=db_path)
    root.withdraw()

    splash = SplashScreen(root)
    splash.update()

    def _finish():
        splash.destroy()
        root.deiconify()

    root.after(1800, _finish)
    root.mainloop()


if __name__ == "__main__":
    main()
