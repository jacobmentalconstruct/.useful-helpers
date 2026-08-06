"""
FILE:       smoke_test.py
ROLE:       Convenience runner for the tests/ smoke suite.
DOMAIN:     testing
DOES:       Discovers and runs tests/ from the project root; exits non-zero on failure so it
            can gate a tranche or CI step.
DEPENDS ON: (stdlib) unittest, sys
WIRES TO:   runs tests/test_smoke.py
NOTES:      Equivalent to `python -m unittest discover -s tests -t .`.
"""
from __future__ import annotations

import sys
import unittest


def run() -> int:
    suite = unittest.TestLoader().discover("tests", top_level_dir=".")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run())
