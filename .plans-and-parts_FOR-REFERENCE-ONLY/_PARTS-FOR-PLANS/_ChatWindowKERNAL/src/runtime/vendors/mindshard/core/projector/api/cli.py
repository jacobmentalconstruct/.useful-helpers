"""
manifold_kernel.api.cli — Command-line interface.

Subcommands:

    manifold-kernel ingest <path>
    manifold-kernel project --query "..." [--profile balanced]
    manifold-kernel evidence --query "..." [--json] [--profile balanced]
    manifold-kernel inspect <artifact_id>
    manifold-kernel neighbors <artifact_id> [--depth 2]
    manifold-kernel stats
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from ..config import KernelConfig, SemanticConfig, StorageConfig
from ..evidence.serializer import evidence_to_json, evidence_to_summary
from ..lens.profiles import list_profiles
from .kernel import ManifoldKernel


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manifold-kernel",
        description="Graph Manifold Kernel Tool — multi-representational retrieval substrate.",
    )
    parser.add_argument(
        "--db", default="manifold_kernel.db",
        help="Path to SQLite database (default: manifold_kernel.db)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose logging.",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # ── ingest ────────────────────────────────────────────────────
    p_ingest = sub.add_parser("ingest", help="Ingest a source file or directory.")
    p_ingest.add_argument("path", help="File or directory to ingest.")

    # ── project ───────────────────────────────────────────────────
    p_project = sub.add_parser("project", help="Build a projection graph for a query.")
    p_project.add_argument("--query", "-q", required=True, help="Query text.")
    p_project.add_argument("--profile", default="balanced", help=f"Lens profile ({', '.join(list_profiles())}).")
    p_project.add_argument("--max-seeds", type=int, default=None)
    p_project.add_argument("--max-nodes", type=int, default=None)
    p_project.add_argument("--radius", type=int, default=None)

    # ── evidence ──────────────────────────────────────────────────
    p_evidence = sub.add_parser("evidence", help="Extract a bounded evidence bag.")
    p_evidence.add_argument("--query", "-q", required=True, help="Query text.")
    p_evidence.add_argument("--profile", default="balanced", help=f"Lens profile ({', '.join(list_profiles())}).")
    p_evidence.add_argument("--json", action="store_true", dest="output_json", help="Output raw JSON.")
    p_evidence.add_argument("--max-seeds", type=int, default=None)
    p_evidence.add_argument("--max-nodes", type=int, default=None)
    p_evidence.add_argument("--radius", type=int, default=None)
    p_evidence.add_argument("--max-items", type=int, default=None)

    # ── inspect ───────────────────────────────────────────────────
    p_inspect = sub.add_parser("inspect", help="Inspect a single artifact.")
    p_inspect.add_argument("artifact_id", help="The artifact ID to inspect.")

    # ── neighbors ─────────────────────────────────────────────────
    p_neighbors = sub.add_parser("neighbors", help="List neighbors of an artifact.")
    p_neighbors.add_argument("artifact_id", help="The artifact ID.")
    p_neighbors.add_argument("--depth", type=int, default=2, help="Neighborhood depth (default: 2).")

    # ── stats ─────────────────────────────────────────────────────
    sub.add_parser("stats", help="Show aggregate store statistics.")

    return parser


def main(argv: list | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    if not args.command:
        parser.print_help()
        return 0

    # Build config
    config = KernelConfig.with_defaults(db_path=args.db)

    # Auto-discover BDVec artifacts
    src_root = Path(__file__).resolve().parent.parent.parent
    bundle = src_root / "mechanical_tokenizer_bundle" / "bdvec"
    tok_path = bundle / "artifacts" / "tokenizer.json"
    emb_path = bundle / "artifacts" / "embeddings.npy"
    if tok_path.is_file() and emb_path.is_file():
        config.semantic.bdvec_tokenizer_path = str(tok_path)
        config.semantic.bdvec_embeddings_path = str(emb_path)
        config.semantic.backend = "bdvec"

    kernel = ManifoldKernel(config)

    try:
        return _dispatch(args, kernel)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        kernel.close()


def _dispatch(args, kernel: ManifoldKernel) -> int:
    cmd = args.command

    if cmd == "ingest":
        stats = kernel.ingest_source(args.path)
        print(json.dumps(stats, indent=2))
        return 0

    if cmd == "project":
        graph = kernel.project(
            query=args.query,
            max_seeds=args.max_seeds,
            max_nodes=args.max_nodes,
            radius=args.radius,
        )
        print(f"Projection: {graph.node_count} nodes, {graph.edge_count} edges")
        for nid, node in sorted(graph.nodes.items(), key=lambda x: x[1].depth):
            print(f"  [{node.depth}] {nid}: {node.text_preview[:80]}")
        return 0

    if cmd == "evidence":
        bag = kernel.extract_evidence(
            query=args.query,
            lens_profile=args.profile,
            max_seeds=args.max_seeds,
            max_nodes=args.max_nodes,
            radius=args.radius,
            max_items=args.max_items,
        )
        if args.output_json:
            print(evidence_to_json(bag))
        else:
            print(evidence_to_summary(bag))
        return 0

    if cmd == "inspect":
        info = kernel.inspect_artifact(args.artifact_id)
        print(json.dumps(info, indent=2))
        return 0

    if cmd == "neighbors":
        neighbors = kernel.list_neighbors(args.artifact_id, depth=args.depth)
        print(json.dumps(neighbors, indent=2))
        return 0

    if cmd == "stats":
        stats = kernel.stats()
        print(json.dumps(stats, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
