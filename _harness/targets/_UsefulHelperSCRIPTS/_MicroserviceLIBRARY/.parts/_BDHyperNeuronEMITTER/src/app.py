"""_BDHyperNeuronEMITTER v2 — composition root and CLI entry.

Commands
--------
train   Build BPE tokenizer + cooccurrence NPMI embeddings from a plain-text
        corpus directory.  Writes tokenizer.json, embeddings.npy, and
        inhibit_edges.json to the artifacts directory.

emit    Read HyperHunk NDJSON from stdin (or --input file), build a Cold
        Artifact SQLite graph, and optionally export training pairs and
        a surface richness report.

bag     Query the Cold Artifact and shape the results into a user-facing
        Bag of Evidence with item, group, and pullback views.

ui      Launch the Tkinter training/inspection GUI.

Usage:
    python -m src train --corpus <path> [--artifacts-dir <dir>] [--vocab-size N] [--embed-dims K]
    python -m src emit [--db <path>] [--artifacts-dir <dir>] [--input <file>]
                       [--report-richness] [--training-pairs <file>]
    python -m src bag --query <text> [--db <path>] [--top-k N] [--group-by origin_id]
    python -m src ui [--artifacts-dir <dir>] [--db <path>]

See _docs/ARCHITECTURE.md for the full design.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

log = logging.getLogger(__name__)

# ── Defaults ──────────────────────────────────────────────────────────────────

_DEFAULT_ARTIFACTS = "./artifacts"
_DEFAULT_DB        = "./cold_anatomy.db"
_DEFAULT_VOCAB     = 8192
_DEFAULT_DIMS      = 300
_DEFAULT_WINDOW    = 5    # cooccurrence sliding window (tokens)
_DEFAULT_SENTENCE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ── BPE helper (re-encode corpus for cooccurrence without re-loading npy) ─────

def _bpe_encode_word(word: str, merges: List[Tuple[str, str]], eow: str) -> List[str]:
    """Apply BPE merge rules to a single word and return a list of subword symbols."""
    symbols: List[str] = list(word) + [eow]
    for a, b in merges:
        merged = a + b
        i, new = 0, []
        while i < len(symbols):
            if i < len(symbols) - 1 and symbols[i] == a and symbols[i + 1] == b:
                new.append(merged)
                i += 2
            else:
                new.append(symbols[i])
                i += 1
        symbols = new
    return symbols


def _bpe_encode_text(
    text: str,
    vocab: Dict[str, int],
    merges: List[Tuple[str, str]],
    eow: str,
) -> List[int]:
    """Tokenise a whitespace-split text into BPE token IDs (unknown → skipped)."""
    ids: List[int] = []
    for word in text.strip().split():
        for sym in _bpe_encode_word(word, merges, eow):
            tid = vocab.get(sym)
            if tid is not None:
                ids.append(tid)
    return ids


def _encode_corpus_to_token_ids(
    corpus_dir: Path,
    vocab: Dict[str, int],
    merges: List[Tuple[str, str]],
    eow: str,
) -> List[List[int]]:
    """Walk corpus_dir for .txt files and encode each line as BPE token IDs."""
    sequences: List[List[int]] = []
    for root, _, files in os.walk(str(corpus_dir)):
        for fname in sorted(files):
            if not fname.lower().endswith(".txt"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        ids = _bpe_encode_text(line, vocab, merges, eow)
                        if ids:
                            sequences.append(ids)
            except OSError as exc:
                log.warning("Could not read corpus file %s: %s", fpath, exc)
    log.info("Encoded %d lines from %s", len(sequences), corpus_dir)
    return sequences


# ── NDJSON reader ──────────────────────────────────────────────────────────────

def _iter_ndjson(source) -> Iterator[dict]:
    """Yield parsed JSON objects from a line-delimited stream, skipping blanks."""
    for raw in source:
        line = raw.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError as exc:
            log.warning("Skipping malformed NDJSON line: %s", exc)


# ── train command ─────────────────────────────────────────────────────────────

def cmd_train(args: argparse.Namespace) -> int:
    """Full training pipeline: BPE → cooccurrence → NPMI → SVD → artifacts."""
    try:
        from .core.engine.training.bpe_trainer import BPETrainer
        from .core.engine.training.cooccurrence import compute_counts
        from .core.engine.training.npmi_matrix import build_npmi_matrix_with_inhibits
        from .core.engine.training.spectral import compute_embeddings
    except ImportError:
        from core.engine.training.bpe_trainer import BPETrainer
        from core.engine.training.cooccurrence import compute_counts
        from core.engine.training.npmi_matrix import build_npmi_matrix_with_inhibits
        from core.engine.training.spectral import compute_embeddings
    import numpy as np

    corpus_dir   = Path(args.corpus)
    artifacts_dir = Path(args.artifacts_dir)
    vocab_size   = args.vocab_size
    embed_dims   = args.embed_dims

    if not corpus_dir.exists():
        log.error("Corpus directory not found: %s", corpus_dir)
        return 1

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    tokenizer_path   = artifacts_dir / "tokenizer.json"
    embeddings_path  = artifacts_dir / "embeddings.npy"
    inhibit_path     = artifacts_dir / "inhibit_edges.json"

    # ── Step 1: BPE training ────────────────────────────────────────────
    log.info("Step 1/4 — BPE training on %s (vocab_size=%d)", corpus_dir, vocab_size)
    trainer = BPETrainer(vocab_size=vocab_size)
    trainer.train(corpus_dir)
    trainer.save(tokenizer_path)
    log.info("  tokenizer.json written: %d tokens, %d merges",
             len(trainer.vocab), len(trainer.merges))

    # ── Step 2: Encode corpus → token ID sequences ─────────────────────
    log.info("Step 2/4 — re-encoding corpus with learned BPE vocabulary")
    corpus_token_ids = _encode_corpus_to_token_ids(
        corpus_dir, trainer.vocab, trainer.merges, trainer.end_of_word,
    )
    if not corpus_token_ids:
        log.error("No token sequences produced — is the corpus non-empty .txt files?")
        return 1

    # ── Step 3: Co-occurrence → NPMI matrix ────────────────────────────
    log.info("Step 3/4 — co-occurrence counting + NPMI matrix (window=%d)", _DEFAULT_WINDOW)
    matrix_result = compute_counts(corpus_token_ids, window_size=_DEFAULT_WINDOW)
    if hasattr(matrix_result, "pair_counts") and hasattr(matrix_result, "token_counts"):
        pair_counts = matrix_result.pair_counts
        token_counts = matrix_result.token_counts
    else:
        pair_counts, token_counts = matrix_result
    npmi_result = build_npmi_matrix_with_inhibits(
        pair_counts=pair_counts,
        token_counts=token_counts,
        vocab_size=len(trainer.vocab),
    )
    log.info("  association matrix: %s, inhibit_edges: %d",
             npmi_result.matrix.shape, len(npmi_result.inhibit_edges))

    # ── Step 4: SVD → dense embeddings ─────────────────────────────────
    log.info("Step 4/4 — truncated SVD (k=%d)", embed_dims)
    k = min(embed_dims, npmi_result.matrix.shape[0] - 1)
    if k < 1:
        log.error("Vocabulary too small for SVD (vocab_size=%d)", len(trainer.vocab))
        return 1
    embeddings = compute_embeddings(npmi_result.matrix, k=k)
    np.save(str(embeddings_path), embeddings)
    log.info("  embeddings.npy written: shape=%s", embeddings.shape)

    # ── Save inhibit edges ──────────────────────────────────────────────
    inhibit_data = [
        {"token_a": e.token_a, "token_b": e.token_b, "weight": e.weight}
        for e in npmi_result.inhibit_edges
    ]
    with open(inhibit_path, "w", encoding="utf-8") as f:
        json.dump(inhibit_data, f, indent=2)
    log.info("  inhibit_edges.json written: %d edges", len(inhibit_data))

    print(f"Training complete. Artifacts written to: {artifacts_dir}", file=sys.stderr)
    print(f"  tokenizer.json  — {len(trainer.vocab)} tokens", file=sys.stderr)
    print(f"  embeddings.npy  — shape {embeddings.shape}", file=sys.stderr)
    print(f"  inhibit_edges.json — {len(inhibit_data)} edges", file=sys.stderr)
    return 0


# ── emit command ──────────────────────────────────────────────────────────────

def cmd_emit(args: argparse.Namespace) -> int:
    """Ingest HyperHunk NDJSON, build the Cold Artifact graph."""
    try:
        from .core.contract.hyperhunk import HyperHunk as EmitterHyperHunk
        from .core.nucleus.bootstrap import BootstrapConfig, BootstrapNucleus
        from .core.assembler.core import GraphAssembler
        from .core.surveyor.hyperhunk import HunkSurveyor
        from .core.engine.inference.provider import (
            EmbeddingProviderSpec,
            create_embed_provider,
            save_embedding_provider_spec,
        )
        provider_mode = "relative"
    except ImportError:
        from core.contract.hyperhunk import HyperHunk as EmitterHyperHunk
        from core.nucleus.bootstrap import BootstrapConfig, BootstrapNucleus
        from core.assembler.core import GraphAssembler
        from core.surveyor.hyperhunk import HunkSurveyor
        from core.engine.inference.provider import (
            EmbeddingProviderSpec,
            create_embed_provider,
            save_embedding_provider_spec,
        )
        provider_mode = "absolute"

    db_path       = Path(args.db)
    artifacts_dir = Path(args.artifacts_dir)
    tokenizer_path  = artifacts_dir / "tokenizer.json"
    embeddings_path = artifacts_dir / "embeddings.npy"

    # ── Optional embed provider ────────────────────────────────────────
    embed_provider: Optional[object] = None
    provider_spec = EmbeddingProviderSpec(provider="none")
    embedder_mode = str(args.embedder).strip().lower()
    sentence_model = str(args.sentence_model or _DEFAULT_SENTENCE_MODEL)

    if embedder_mode == "auto":
        if tokenizer_path.is_file() and embeddings_path.is_file():
            provider_spec = EmbeddingProviderSpec(
                provider="deterministic",
                artifacts_dir=str(artifacts_dir.resolve()),
            )
        else:
            provider_spec = EmbeddingProviderSpec(provider="none")
    elif embedder_mode == "deterministic":
        if not tokenizer_path.is_file() or not embeddings_path.is_file():
            log.error(
                "Deterministic embedder requested but tokenizer.json/embeddings.npy were not found in %s",
                artifacts_dir,
            )
            return 1
        provider_spec = EmbeddingProviderSpec(
            provider="deterministic",
            artifacts_dir=str(artifacts_dir.resolve()),
        )
    elif embedder_mode == "sentence-transformers":
        provider_spec = EmbeddingProviderSpec(
            provider="sentence-transformers",
            model_name=sentence_model,
        )
    elif embedder_mode == "none":
        provider_spec = EmbeddingProviderSpec(provider="none")
    else:
        log.error("Unsupported embedder mode: %s", args.embedder)
        return 1

    try:
        embed_provider = create_embed_provider(provider_spec)
        if embed_provider is None:
            log.info("Embeddings disabled (provider=%s)", provider_spec.provider)
        elif provider_spec.provider == "deterministic":
            log.info("Deterministic embedding provider loaded from %s", artifacts_dir)
        else:
            log.info(
                "Traditional embedding provider loaded: %s (%s)",
                provider_spec.provider,
                provider_spec.model_name,
            )
    except Exception as exc:
        log.error("Could not load embedding provider %s: %s", provider_spec.provider, exc)
        return 1

    # ── Input source ───────────────────────────────────────────────────
    if args.input:
        try:
            source = open(args.input, "r", encoding="utf-8")
        except OSError as exc:
            log.error("Cannot open input file: %s", exc)
            return 1
    else:
        source = sys.stdin

    # ── Build Nucleus + Assembler ──────────────────────────────────────
    try:
        bootstrap_config = BootstrapConfig.default()
        if args.bootstrap_profile:
            profile_path = Path(args.bootstrap_profile)
            payload = json.loads(profile_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("bootstrap profile must be a JSON object")
            bootstrap_config = bootstrap_config.with_overrides(payload)

        cli_overrides: Dict[str, float] = {}
        if args.edge_threshold is not None:
            cli_overrides["edge_threshold"] = args.edge_threshold
        if args.dominance_threshold is not None:
            cli_overrides["dominance_threshold"] = args.dominance_threshold
        if cli_overrides:
            bootstrap_config = bootstrap_config.with_overrides(cli_overrides)
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        log.error("Invalid bootstrap profile configuration: %s", exc)
        if args.input and source is not sys.stdin:
            source.close()
        return 1

    nucleus  = BootstrapNucleus(config=bootstrap_config)
    surveyor = HunkSurveyor(strict=False) if args.report_richness else None

    hunk_count = 0
    error_count = 0

    db_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path = db_path.parent / "bootstrap_profile_effective.json"
    bootstrap_config.save_json(profile_path)
    log.info("Effective bootstrap profile written: %s", profile_path)
    embed_profile_path = save_embedding_provider_spec(db_path.parent, provider_spec)
    log.info("Effective embedding provider written: %s", embed_profile_path)
    with GraphAssembler(
        db_path,
        nucleus,
        embed_provider=embed_provider,
        window_size=args.window_size,
        reference_candidate_limit=args.reference_candidate_limit,
    ) as assembler:
        for record in _iter_ndjson(source):
            try:
                hunk = EmitterHyperHunk.from_dict(record)
            except Exception as exc:
                log.warning("Skipping malformed hunk record: %s", exc)
                error_count += 1
                continue

            assembler.ingest_one(hunk)
            if surveyor is not None:
                surveyor.observe(hunk)
            hunk_count += 1

        # ── Training pairs export ──────────────────────────────────────
        if args.training_pairs:
            pairs = assembler.export_training_pairs()
            tp_path = Path(args.training_pairs)
            tp_path.parent.mkdir(parents=True, exist_ok=True)
            with open(tp_path, "w", encoding="utf-8") as f:
                json.dump(pairs, f, indent=2)
            log.info("Training pairs written: %d pairs → %s", len(pairs), tp_path)

        stats = assembler.stats()

    if args.input and source is not sys.stdin:
        source.close()

    # ── Output ─────────────────────────────────────────────────────────
    print(f"Emit complete: {hunk_count} hunks ingested, {error_count} skipped", file=sys.stderr)
    print(f"Cold Artifact: {db_path}", file=sys.stderr)
    for k, v in stats.items():
        print(f"  {k}: {v}", file=sys.stderr)

    if surveyor is not None:
        report = surveyor.finalize()
        print("\n--- Surface Richness Report ---", file=sys.stderr)
        for line in report.summary_lines():
            print(line, file=sys.stderr)

    return 0


# ── ui command ────────────────────────────────────────────────────────────────

def cmd_ui(args: argparse.Namespace) -> int:
    """Launch the Tkinter training/inspection GUI."""
    try:
        try:
            from .ui.gui_main import main as gui_main
        except ImportError:
            from ui.gui_main import main as gui_main
        gui_main(
            artifacts_dir=args.artifacts_dir,
            db_path=args.db,
        )
        return 0
    except ImportError as exc:
        log.error("GUI dependencies not available: %s", exc)
        return 1


def cmd_bag(args: argparse.Namespace) -> int:
    """Query the Cold Artifact and return a rudimentary Bag of Evidence."""
    try:
        try:
            from .core.engine.inference.bag_view import build_bag
        except ImportError:
            from core.engine.inference.bag_view import build_bag

        bag = build_bag(
            query_text=args.query,
            db_path=args.db,
            top_k=args.top_k,
            hop_limit=args.hop_limit,
            decay=args.decay,
            group_by=args.group_by,
            include_full_text=args.include_full_text,
            pull_occurrence_ids=args.pull_occurrence_id,
            embedder_override=args.embedder_override,
            sentence_model=args.sentence_model,
        )
        json.dump(bag, sys.stdout, indent=2)
        print()
        return 0
    except Exception as exc:
        log.error("Bag query failed: %s", exc)
        return 1
    except Exception as exc:
        log.error("GUI crashed: %s", exc)
        return 1


# ── Argument parser ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="_BDHyperNeuronEMITTER",
        description="Build and query the HyperNeuron Cold Artifact graph.",
    )
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # ── train ──────────────────────────────────────────────────────────
    t = sub.add_parser("train", help="Train BPE tokenizer and compute embeddings.")
    t.add_argument("--corpus", required=True, metavar="DIR",
                   help="Path to corpus directory containing .txt files.")
    t.add_argument("--artifacts-dir", default=_DEFAULT_ARTIFACTS, metavar="DIR",
                   help=f"Where to write training artifacts (default: {_DEFAULT_ARTIFACTS}).")
    t.add_argument("--vocab-size", type=int, default=_DEFAULT_VOCAB, metavar="N",
                   help=f"Target BPE vocabulary size (default: {_DEFAULT_VOCAB}).")
    t.add_argument("--embed-dims", type=int, default=_DEFAULT_DIMS, metavar="K",
                   help=f"SVD embedding dimensions (default: {_DEFAULT_DIMS}).")

    # ── emit ───────────────────────────────────────────────────────────
    e = sub.add_parser("emit", help="Ingest HyperHunk NDJSON into the Cold Artifact.")
    e.add_argument("--db", default=_DEFAULT_DB, metavar="PATH",
                   help=f"Cold Artifact SQLite path (default: {_DEFAULT_DB}).")
    e.add_argument("--artifacts-dir", default=_DEFAULT_ARTIFACTS, metavar="DIR",
                   help=f"Artifacts directory with tokenizer.json + embeddings.npy (default: {_DEFAULT_ARTIFACTS}).")
    e.add_argument("--input", default=None, metavar="FILE",
                   help="Input NDJSON file (default: stdin).")
    e.add_argument("--bootstrap-profile", default=None, metavar="FILE",
                   help="Optional JSON bootstrap tuning profile; applied before CLI overrides.")
    e.add_argument("--edge-threshold", type=float, default=None, metavar="T",
                   help="Override bootstrap edge strength threshold.")
    e.add_argument("--dominance-threshold", type=float, default=None, metavar="D",
                   help="Override bootstrap routing dominance threshold.")
    e.add_argument("--report-richness", action="store_true",
                   help="Print surface richness report to stderr after ingestion.")
    e.add_argument("--training-pairs", default=None, metavar="FILE",
                   help="Export all Nucleus evaluations (training data) to this JSON file.")
    e.add_argument("--window-size", type=int, default=50, metavar="N",
                   help="Sliding comparison window for Nucleus pair evaluation (default: 50).")
    e.add_argument("--reference-candidate-limit", type=int, default=0, metavar="N",
                   help="Additional long-range reference-targeted candidates per hunk (default: 0 = disabled).")
    e.add_argument("--embedder", default="auto", choices=["auto", "deterministic", "sentence-transformers", "none"],
                   help="Embedding provider for occurrence vectors (default: auto).")
    e.add_argument("--sentence-model", default=_DEFAULT_SENTENCE_MODEL, metavar="MODEL",
                   help=f"Sentence-transformers model name when --embedder=sentence-transformers (default: {_DEFAULT_SENTENCE_MODEL}).")

    # ── bag ────────────────────────────────────────────────────────────
    b = sub.add_parser("bag", help="Query the Cold Artifact and emit a rudimentary Bag of Evidence.")
    b.add_argument("--query", required=True, metavar="TEXT",
                   help="Query text used to anchor retrieval.")
    b.add_argument("--db", default=_DEFAULT_DB, metavar="PATH",
                   help=f"Cold Artifact SQLite path (default: {_DEFAULT_DB}).")
    b.add_argument("--top-k", type=int, default=12, metavar="N",
                   help="Maximum number of evidence items to return (default: 12).")
    b.add_argument("--hop-limit", type=int, default=2, metavar="N",
                   help="Neighborhood expansion depth for the reactor query (default: 2).")
    b.add_argument("--decay", type=float, default=0.9, metavar="A",
                   help="Activation decay factor for the reactor query (default: 0.9).")
    b.add_argument("--group-by", default="origin_id", choices=["origin_id", "node_kind", "structural_root"],
                   help="Grouping lens for the bag output (default: origin_id).")
    b.add_argument("--include-full-text", action="store_true",
                   help="Include full evidence text for each bag item.")
    b.add_argument("--pull-occurrence-id", action="append", default=[], metavar="OCC_ID",
                   help="Occurrence id to include in the pullback section; repeatable.")
    b.add_argument("--embedder-override", default=None, choices=["deterministic", "sentence-transformers", "none"],
                   help="Optional query-time embedder override. By default the bag infers the provider from DB-side metadata.")
    b.add_argument("--sentence-model", default=None, metavar="MODEL",
                   help="Sentence-transformers model name for bag/query override mode.")

    # ── ui ─────────────────────────────────────────────────────────────
    u = sub.add_parser("ui", help="Launch the training/inspection GUI.")
    u.add_argument("--artifacts-dir", default=_DEFAULT_ARTIFACTS, metavar="DIR",
                   help=f"Artifacts directory to load on startup (default: {_DEFAULT_ARTIFACTS}).")
    u.add_argument("--db", default=_DEFAULT_DB, metavar="PATH",
                   help=f"Cold Artifact to inspect on startup (default: {_DEFAULT_DB}).")

    return p


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level, logging.INFO),
        format="%(levelname)s  %(name)s  %(message)s",
        stream=sys.stderr,
    )

    if args.command == "train":
        return cmd_train(args)
    if args.command == "emit":
        return cmd_emit(args)
    if args.command == "bag":
        return cmd_bag(args)
    if args.command == "ui":
        return cmd_ui(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
