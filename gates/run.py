#!/usr/bin/env python3
"""
FILE:       gates/run.py
ROLE:       Gate runner - the mechanism that makes a tranche closable.
DOMAIN:     factory
DOES:       Discovers gates/t*.py, runs each one's check() in order, prints a
            per-assertion result, and exits non-zero if any gate fails or if a
            check is SKIPPED without a registered acceptance.
DEPENDS ON: (stdlib) argparse, importlib, pathlib, sys
NOTES:      A gate proves a TRANCHE OUTCOME holds. It is not a unit test suite,
            though it may invoke one. See .bcc/TRANCHE_PROTOCOL.md sec 3.
            Binary only: exit 0 or non-zero. No partial credit.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

GATES = Path(__file__).resolve().parent
ROOT = GATES.parent

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


class Result:
    """Collects assertions for one gate."""

    def __init__(self, tranche: str):
        self.tranche = tranche
        self.rows: list[tuple[str, str, str]] = []

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.rows.append((PASS if ok else FAIL, name, detail))

    def skip(self, name: str, reason: str) -> None:
        self.rows.append((SKIP, name, reason))

    @property
    def failed(self) -> bool:
        return any(s == FAIL for s, _, _ in self.rows)

    @property
    def skipped(self) -> bool:
        return any(s == SKIP for s, _, _ in self.rows)


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description="Run tranche gates.")
    ap.add_argument("tranche", nargs="?", help="e.g. t00; omit to run all")
    args = ap.parse_args()

    files = sorted(GATES.glob("t[0-9][0-9]_*.py"))
    if args.tranche:
        files = [f for f in files if f.stem.startswith(args.tranche.lower())]
        if not files:
            print(f"no gate matching {args.tranche!r}")
            return 2

    overall_fail = False
    for f in files:
        mod = _load(f)
        res = Result(f.stem)
        mod.check(res, ROOT)
        header = f"{res.tranche}  {getattr(mod, 'OUTCOME', '')}"
        print(f"\n{header}\n{'-' * len(header)}")
        for status, name, detail in res.rows:
            line = f"  [{status}] {name}"
            if detail:
                line += f"\n         {detail}"
            print(line)
        if res.failed:
            overall_fail = True
            print(f"  => {res.tranche} BLOCKED")
        elif res.skipped:
            overall_fail = True
            print(f"  => {res.tranche} INCOMPLETE (skipped checks are not passes)")
        else:
            print(f"  => {res.tranche} PASS")

    print()
    if overall_fail:
        print("SUITE: FAIL - tranche is not parkable")
        return 1
    print("SUITE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
