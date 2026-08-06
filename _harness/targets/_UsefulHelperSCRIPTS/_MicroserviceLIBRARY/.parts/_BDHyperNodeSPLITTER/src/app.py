"""_BDHyperNodeSPLITTER v2 — composition root and CLI entry.

Modes
-----
  stream <path>       Split a file or directory. Emit HyperHunk NDJSON to stdout.
  info   <path>       Print hunk count estimate and engine routing info. No stream.

Usage
-----
  python -m src stream ./docs/ --max-tokens 256
  python -m src stream ./src/main.py --max-tokens 128 --overlap 0.3
  python -m src info ./docs/
  python src/app.py stream ./docs/ | python ../emitter/src/app.py emit

All structured output goes to stdout (NDJSON).
All diagnostic / progress output goes to stderr.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

log = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="_BDHyperNodeSPLITTER",
        description="Split documents into richly-contextual HyperHunks (NDJSON to stdout).",
    )
    p.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: WARNING).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # ── stream ──────────────────────────────────────────────────────────
    stream = sub.add_parser(
        "stream",
        help="Stream HyperHunks from a file or directory as NDJSON.",
    )
    stream.add_argument("path", help="File or directory to split.")
    stream.add_argument(
        "--max-tokens", type=int, default=256,
        help="Token budget per hunk (default: 256).",
    )
    stream.add_argument(
        "--overlap", type=float, default=0.25,
        help="Context window overlap ratio (default: 0.25).",
    )
    stream.add_argument(
        "--chars-per-token", type=float, default=4.0,
        help="Chars-per-token calibration for budget estimate (default: 4.0).",
    )
    stream.add_argument(
        "--signal-profile",
        help="Path to a builder-side Splitter signal profile JSON.",
    )

    # ── info ─────────────────────────────────────────────────────────────
    info = sub.add_parser(
        "info",
        help="Show engine routing and estimated hunk count for a file/dir.",
    )
    info.add_argument("path", help="File or directory to inspect.")
    info.add_argument("--max-tokens", type=int, default=256)
    info.add_argument(
        "--signal-profile",
        help="Path to a builder-side Splitter signal profile JSON.",
    )

    return p


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    args = build_parser().parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s  %(name)s  %(message)s",
        stream=sys.stderr,
    )

    # Import core here so import errors surface clearly
    try:
        from core import splitter
    except ImportError as exc:
        log.error("Failed to import core.splitter: %s", exc)
        return 1

    if args.command == "stream":
        return _cmd_stream(args, splitter)

    if args.command == "info":
        return _cmd_info(args, splitter)

    return 1


def _cmd_stream(args, splitter) -> int:
    """Stream HyperHunk NDJSON to stdout."""
    count = 0
    errors = 0
    signal_profile = _load_signal_profile(args.signal_profile)
    try:
        for hunk in splitter.process_file(
            args.path,
            max_tokens=args.max_tokens,
            overlap_ratio=args.overlap,
            chars_per_token=args.chars_per_token,
            signal_profile=signal_profile,
        ):
            try:
                line = json.dumps(hunk.to_dict(), ensure_ascii=False)
                sys.stdout.write(line + "\n")
                sys.stdout.flush()
                count += 1
            except (TypeError, ValueError) as exc:
                log.warning("Skipping non-serializable hunk: %s", exc)
                errors += 1
    except OSError as exc:
        log.error("I/O error: %s", exc)
        return 1

    log.info("Streamed %d hunks (%d skipped) from %s", count, errors, args.path)
    return 0


def _cmd_info(args, splitter) -> int:
    """Print routing and estimate info to stdout as JSON."""
    from pathlib import Path
    skip_dirs = {"__pycache__", ".git", ".venv", "venv", "node_modules"}
    p = Path(args.path)
    signal_profile = _load_signal_profile(args.signal_profile)

    if p.is_file():
        targets = [str(p)]
    elif p.is_dir():
        targets = sorted(
            str(f)
            for f in p.rglob("*")
            if f.is_file()
            and not any(part in skip_dirs for part in f.parts)
            and f.suffix.lower() != ".pyc"
        )[:20]  # sample first 20
    else:
        log.error("Path not found: %s", args.path)
        return 1

    rows = []
    for t in targets:
        text = None
        try:
            text = Path(t).read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = None
        rows.append({
            "path": t,
            "engines": splitter.which_engines(t, text=text, signal_profile=signal_profile),
            "estimated_hunks": splitter.estimate_hunk_count(t, args.max_tokens),
        })

    info = {
        "path": args.path,
        "max_tokens": args.max_tokens,
        "files_sampled": len(rows),
        "routing": rows,
    }
    sys.stdout.write(json.dumps(info, indent=2) + "\n")
    return 0


def _load_signal_profile(path: str | None):
    if not path:
        return None
    profile_path = Path(path)
    if not profile_path.exists():
        raise FileNotFoundError(f"Signal profile not found: {profile_path}")
    from core.signal_profile import SplitterSignalProfile
    return SplitterSignalProfile.load_json(profile_path)


if __name__ == "__main__":
    sys.exit(main())
