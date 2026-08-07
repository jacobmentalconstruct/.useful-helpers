"""
FILE:       src/core/payload.py
ROLE:       The ship manifest - the ONE declaration of what the sidecar ships.
DOMAIN:     core
DOES:       Names every exclusion BY CATEGORY, so each states its reason, and derives
            the payload boundary from those categories.
DEPENDS ON: nothing (deliberately: the harness, the gates, the tests and the vend
            tools all import it, so it must stay dependency-free)
WIRES TO:   tools/vendor_export, tools/sidecar_install, _harness/harness.py,
            tests/test_smoke.py, gates/t01_ship_manifest.py
NOTES:      This exists because the boundary used to be implicit in the folder layout.
            While the sidecar was nested inside toolkit/, "what ships" was "what is in
            that folder" - a rule nothing had to state and four mechanisms silently
            relied on. Collapsing the sidecar to the repository root erased it, and
            each mechanism widened from ~136 files to thousands. One vend shipped
            4,009 files - the operator's whole reference library - into a target.

            The categories are the point. A flat exclusion list cannot distinguish
            "regenerable junk" from "must never reach a target" from "belongs to the
            other deliverable", and under a flat list `packaging/` sat beside
            `_trash`, inviting exactly the wrong cleanup.
"""
from __future__ import annotations

# ---------------------------------------------------------------- universal
# Excluded from ANY export, including an export of the USER'S project. These are
# not sidecar concerns; they are things nobody wants copied anywhere.

REGENERABLE = frozenset({
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".venv", "venv", "env", "build", "dist", "node_modules",
    "_artifacts",           # disposable generated output
    "_exports",             # previous exports
    "_state",               # durable memory: belongs to whoever is attached, never shipped
    "_tmp_sqlite_probe",
    "logs",
})

VCS = frozenset({".git", ".hg", ".svn"})

EXCLUDE_SUFFIXES = frozenset({
    ".sqlite", ".sqlite3", ".db", ".pyc", ".pyo", ".log",
})

# ------------------------------------------------------------ sidecar-only
# Excluded when exporting THE SIDECAR ITSELF. These must NOT be applied to an
# export of a user's project - a target may legitimately have its own `_docs/`
# or `gates/`, and stripping them would be the sidecar editing the target's shape.

NEVER_SHIP = frozenset({
    ".bcc",                                  # builder contract, charter, plan, evidence
    "_docs",                                 # the sidecar's own journal; a target's record starts empty
    "gates",                                 # tranche gates
    "_trash",                                # removal staging
    "_harness",                              # proving ground; ALSO a recursion guard - its
                                             # targets live inside it, so vending the root
                                             # without excluding it copies a target into itself
    ".plans-and-parts_FOR-REFERENCE-ONLY",   # parts bin: predecessor apps and their plans
    ".useful-helpers-test-tmp",              # suite scratch
    "requirements-dev.txt",                  # dev-only dependency declaration
})

# Ships as DELIVERABLE #1, beside the payload, never inside it. Excluded for a
# different reason than everything above: not unwanted, just not part of this half.
# `packaging/installer/install.py` states it directly - "ships NEXT TO the product
# zip, not inside it" - resolving a sibling folder or zip, stdlib-only so it runs on
# a bare machine. A payload carrying its own installer is circular and dead weight.
INSTALLER_ONLY = frozenset({
    "packaging",
})

# Replaced at export time by tool-focused versions, so the shipped copy never links
# to stripped build docs. Excluded verbatim, then substituted back.
EXPORT_SUBSTITUTED = frozenset({
    "tools/vendor_export/clean_app_docs",
})

# ------------------------------------------------------------- not ours
# Code this project did not write and will not maintain. This is a DIFFERENT axis
# from shipping: `gates/` and `_harness/` do not ship, but they are ours and should
# meet our bar; the parts bin is neither shipped nor ours.
#
# Lint scope is therefore not ship scope, and conflating them was about to exclude
# our own gates from linting. Anything here must be excluded from lint; excluding
# more is a judgement call, not a correctness one.
FOREIGN = frozenset({
    ".plans-and-parts_FOR-REFERENCE-ONLY",   # twelve predecessor applications
    "_trash",                                # staged for deletion
    ".useful-helpers-test-tmp",              # suite scratch
})

# ---------------------------------------------------------------- derived
# Everything stripped when exporting the sidecar itself. Relative-path matched.
SIDECAR_STRIP = NEVER_SHIP | INSTALLER_ONLY | EXPORT_SUBSTITUTED

# Every name that must never appear in a vended payload. Basename matched, for
# shutil.ignore_patterns and equivalent name-based filters.
PAYLOAD_EXCLUDE = SIDECAR_STRIP | REGENERABLE | VCS

# Regression signal. The payload is ~275 files; a leak once shipped 4,009. This is
# the cheapest possible check that the boundary has not quietly widened again.
MAX_PAYLOAD_FILES = 500
