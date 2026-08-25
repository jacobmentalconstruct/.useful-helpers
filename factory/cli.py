from __future__ import annotations

import argparse
import json
import sys

from .installer import AttachError, attach


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sidecar-builder")
    commands = parser.add_subparsers(dest="command", required=True)
    attach_parser = commands.add_parser("attach", help="attach a new .sidecar to a target")
    attach_parser.add_argument("target")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "attach":
            result = attach(args.target)
        else:  # argparse keeps this unreachable, but the adapter still fails closed.
            raise AttachError(f"unsupported command: {args.command}")
    except AttachError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"ok": True, **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
