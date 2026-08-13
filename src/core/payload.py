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
    "_projectmapper",                        # projectmapper's own output. Regenerable by
                                             # `projectmapper` at any time; three copies were
                                             # tracked and 8.4 MB of them shipped, carrying
                                             # build-machine paths and filedumped predecessor
                                             # content into the payload. Generated residue in
                                             # the tree this toolkit exists to keep clean.
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
#
# DEFAULT-OFF, NOT FORBIDDEN. `.bcc` and `gates` are excluded by default but are
# NOT unshippable: three files inside them form the OPTIONAL GOVERNANCE CARTRIDGE
# below, which the installer may add back at the operator's request. Everything
# else here is unshippable outright.
#
# This distinction was missing when the manifest was first written, and the whole
# of `.bcc` was swept in as one directory. That silently dropped a requirement the
# operator had already given - that the contract be installable via a checkbox in
# the installer - because a name in this set is invisible everywhere else.

NEVER_SHIP = frozenset({
    ".bcc",                                  # DEFAULT-OFF: charter, plan and evidence are
                                             # never shippable; the contract and protocol are
                                             # opt-in - see GOVERNANCE_CARTRIDGE
    "_docs",                                 # the sidecar's own journal; a target's record starts empty
    "gates",                                 # DEFAULT-OFF: tranche gates are this build's;
                                             # `gates/run.py` alone is opt-in
    "_trash",                                # removal staging
    "_harness",                              # proving ground; ALSO a recursion guard - its
                                             # targets live inside it, so vending the root
                                             # without excluding it copies a target into itself
    ".plans-and-parts_FOR-REFERENCE-ONLY",   # parts bin: predecessor apps and their plans
    ".useful-helpers-test-tmp",              # suite scratch
    "requirements-dev.txt",                  # dev-only dependency declaration
})

# ------------------------------------------------- optional governance cartridge
# The contract is not merely this build's governance - it is a TOOL the sidecar
# carries. A target that wants tranche discipline can have it; a target that does
# not is never colonised by it. Hence opt-in rather than always or never.
#
# Off by default, added back only when the operator enables it at install. Named as
# RELATIVE PATHS, unlike the name-matched sets above, because the point is to carve
# individual files out of directories that are otherwise excluded.
#
# BLANK ON ARRIVAL. The shipped contract must carry UNRESOLVED placeholders, or
# values resolved for the NEW target - never this project's. A vended contract
# still reading TARGET_PROJECT_ROOT="." and JOURNAL_PATH="_docs/AppJOURNAL" would
# be exactly the unpurged history E11 forbids. The installer collects these, with
# defaults shown and editable.
#
# WIRING BELONGS TO T9 (Install and Packaging). This declaration exists now so the
# requirement lives in the one file that governs shipping, where it cannot be
# dropped a second time.
GOVERNANCE_CARTRIDGE = frozenset({
    ".bcc/BUILDER-CONSTRAINT-CONTRACT.md",   # the contract itself, placeholders unresolved
    ".bcc/TRANCHE_PROTOCOL.md",              # gate mechanism and the discovery pass
    "gates/run.py",                          # the runner, so the discipline arrives
                                             # executable rather than aspirational
})

# Never shippable, not even opt-in: this product's own definition and this build's
# own record. Enumerated so the cartridge cannot be widened to include them by a
# later hand that reads `.bcc` as one undifferentiated thing.
CARTRIDGE_FORBIDDEN = frozenset({
    ".bcc/CHARTER.md",                       # what THIS product is
    ".bcc/TRANCHE_PLAN.md",                  # what THIS build is doing
    ".bcc/evidence",                         # what THIS build measured
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

# WHAT replaces WHAT. The set above says "excluded verbatim"; this says where each
# substitute lands. Two consumers previously carried their own copy of this mapping -
# `vendor_export` and the deleted `sidecar_install` - which is why a payload produced
# by a third route shipped the development ignore file. One authority, one mapping.
EXPORT_SUBSTITUTIONS = {
    "tools/vendor_export/clean_app_docs/README.md": "README.md",
    "tools/vendor_export/clean_app_docs/ONBOARDING.md": "docs/ONBOARDING.md",
    "tools/vendor_export/clean_app_docs/gitignore": ".gitignore",
}

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

# The cartridge adds three files when enabled, so the ceiling does not move.
# Stated rather than assumed: an opt-in category is exactly the kind of thing that
# grows quietly, and the point of the ceiling is to notice.
MAX_CARTRIDGE_FILES = 8


def materialise(source: "object", dest: "object") -> "object":
    """Copy exactly the payload from `source` to `dest`. Returns `dest`.

    THE ONE PAYLOAD PRODUCER, so gates and tests do not each grow their own copy of
    "what a payload is" - which is this module's whole reason to exist.

    It is NOT the canonical positive assembler. That is a later tranche, and it will
    build from a declared inclusion manifest rather than by subtracting exclusions
    from a source tree. Until then this is how a real payload is produced for the
    standalone setup application to install, and it inherits exactly the boundary
    declared above.

    Deliberately not a tool and not registered: producing a payload is a
    source-factory activity (Charter SIDECAR:SOURCE-FACTORY), not something an
    installed instance does.
    """
    import shutil
    from pathlib import Path

    src, dst = Path(source), Path(dest)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*PAYLOAD_EXCLUDE))

    # SUBSTITUTION IS PART OF THE BOUNDARY, not a courtesy.
    #
    # The development `.gitignore` names the parts bin, the harness, gates and trash -
    # zones that do not exist in an installed instance, and whose names would tell a
    # target about the build process. So the payload gets its own.
    #
    # This lived in `tools/sidecar_install` until T6 deleted it, and the first version
    # of `materialise()` was a plain copytree that silently dropped the behaviour: the
    # payload started shipping the development ignore file again. Which is the point -
    # "what the payload contains" is this module's question, and answering half of it
    # elsewhere is how it got lost.
    for rel, target in EXPORT_SUBSTITUTIONS.items():
        source_file = src / rel
        if source_file.is_file():
            out = dst / target
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, out)
    return dst


def cartridge_conflicts() -> set[str]:
    """Paths claimed by both the cartridge and the forbidden set.

    Always empty. It exists so the contradiction is detectable rather than
    arguable: the two sets are written by hand, in the same file, by people who
    will read `.bcc` as one thing unless something stops them.
    """
    return set(GOVERNANCE_CARTRIDGE) & set(CARTRIDGE_FORBIDDEN)
