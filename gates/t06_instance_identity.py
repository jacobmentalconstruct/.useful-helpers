"""
FILE:       gates/t06_instance_identity.py
ROLE:       Gate for T6 - Instance Identity and the Installation Core.
DOMAIN:     factory
DOES:       Asserts one authoritative definition of what an installed instance IS, one
            component that resolves it, and that the product's own setup application
            creates an instance that resolves itself and its target without relying on
            its folder name, an absolute path, or an environment guess.
NOTES:      Written at declaration, BEFORE implementation (protocol 3.2 rule 1), and
            AMENDED before implementation after two audits - see journal 0025.

            WHAT THIS PROVES, IN PRODUCT TERMS. Charter 3.3 pins a fifteen-step
            prototype walk. This gate advances steps 3, 5, 13 and 14:

                3.  install into any chosen folder
                5.  the sidecar identifies itself and its target
                13. restarting destroys neither identity nor durable state
                14. moving target + sidecar together does not break the relationship

            Every assertion below answers to one of those. An assertion that answers
            to none of them is testing the substrate for its own sake.

            RULE 8: the real consumer entrance for an installed instance is the SETUP
            APPLICATION. This gate installs only through `packaging/installer/` and
            never through a runtime tool. Every install this project has verified went
            through `tools/sidecar_install`; the shipping path was never exercised and
            does not work.

            THE PAYLOAD IS A FIXTURE, NOT A PRODUCT. The installer needs something to
            install, and the canonical positive assembler is a later tranche. So the
            gate materialises a payload from today's manifest authority and hands it
            over with `--payload`. That confers NO architectural authority on the
            legacy producer, and the future pipeline remains: source factory ->
            canonical assembler -> payload -> setup application -> instance.

            NO PRODUCT SURFACE IS ADDED TO SUIT THIS GATE. An earlier draft required a
            `--folder` option so it could install under a non-default name and prove
            identity is not the basename. That would have created an unsupported
            "custom sidecar folder" contract to satisfy a test. Instead: install
            canonically, then RENAME the instance and MOVE the target, strip every
            environment hint, and require structural resolution to survive. Same
            property, proven more directly, no new contract.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OUTCOME = "one instance identity, created by the product installer, resolved structurally"

CORE = "src/core/instance.py"
INSTALLER = "packaging/installer/install.py"
DEFAULT_HOME = ".useful-helpers"

# Only this module may consult identity TRANSPORT. Passing a resolved INSTANCE_ROOT to
# a subprocess through SUITE_HOME is legitimate; a subprocess DECIDING between
# SUITE_HOME, cwd, and a folder named `.useful-helpers` is the defect. One component
# resolves; the rest consume.
IDENTITY_RESOLVER = CORE

# THE INVARIANT, NOT THE VOCABULARY:
#   does this surface CREATE or ADVERTISE another installed Useful Helpers instance?
#
# Distinct from: does this surface create or mutate ordinary TARGET-OWNED content?
# `scaffold_project` and `genesis` build project files under a governed Apply. That is
# the product working on its target, not the sidecar reproducing itself.
#
# A first draft matched the bare token `sidecar_install` anywhere and flagged nine
# sites. THREE were docstrings - `genesis`, `scaffold_project` and `payload.py` each
# merely DESCRIBE a chain that used to exist. A gate satisfiable by deleting accurate
# documentation is a gate the architecture has to grow around, so this matches
# dispatch and routing only.
INSTALL_INVOCATION = (
    r'invoke\([^)]*["\']sidecar_install["\']',     # dispatched through the seam
    r'--tool["\'],\s*["\']sidecar_install',        # dispatched through the CLI
    r'from src\.ui import installer_view',         # the runtime installer UI
    r'def run_installer\b',                        # its composition entrance
    r'mode == ["\']install["\']',                  # the CLI route
)


def _load(root: Path, dotted: str):
    sys.path.insert(0, str(root))
    try:
        return __import__(dotted, fromlist=["_"])
    except Exception:
        return None
    finally:
        if str(root) in sys.path:
            sys.path.remove(str(root))


def _ours(root: Path):
    """Our own Python, excluding foreign trees and this gate."""
    for py in sorted(root.rglob("*.py")):
        rel = py.relative_to(root).as_posix()
        if rel.startswith((".plans-and-parts", "_trash", ".useful-helpers-test-tmp",
                           "_harness/targets", "_projectmapper")):
            continue
        if rel == "gates/t06_instance_identity.py":
            continue
        yield rel, py.read_text(encoding="utf-8", errors="replace")


def _code_only(body: str) -> str:
    """Strip comments AND docstrings.

    Both are history, not entrances. Three of the first census's nine hits were
    docstrings describing a chain that used to exist - accurate documentation this
    gate would otherwise have demanded be deleted.
    """
    import io
    import tokenize

    # BLANK the comment and docstring spans in place. Re-emitting tokens joined by a
    # separator was the first attempt, and it silently destroyed every multi-token
    # pattern: `from src.ui import installer_view` became six lines, so no route could
    # ever match and the census dropped from nine hits to one by BLINDING ITSELF.
    # Blanking preserves offsets, so everything else reads exactly as written.
    triple = ('"' * 3, "'" * 3)
    lines = body.splitlines(keepends=True)
    spans = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(body).readline):
            drop = tok.type == tokenize.COMMENT or (
                tok.type == tokenize.STRING
                and tok.string.lstrip("rbfuRBFU").startswith(triple))
            if drop:
                spans.append((tok.start, tok.end))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return body                      # unparseable: keep raw text, never hide it

    for (srow, scol), (erow, ecol) in spans:
        for row in range(srow, erow + 1):
            line = lines[row - 1]
            a = scol if row == srow else 0
            b = ecol if row == erow else len(line.rstrip("\r\n"))
            keep_nl = line[len(line.rstrip("\r\n")):]
            lines[row - 1] = (line[:a] + " " * max(0, b - a)
                              + line[b:].rstrip("\r\n") + keep_nl)
    return "".join(lines)


def _installer_next(stdout: str) -> "str | None":
    """The runnable line from the installer's own `next` message.

    Deliberately parsed from what the product PRINTS rather than reconstructed here.
    A gate that builds its own launch command cannot notice the printed one is wrong -
    which is exactly how a broken entrance survived a green suite.
    """
    import json as _json
    for i, ch in enumerate(stdout):
        if ch == "{":
            try:
                doc = _json.loads(stdout[i:])
            except ValueError:
                continue
            for line in str(doc.get("next", "")).splitlines():
                line = line.strip()
                if line.startswith(("sh ", "run.bat", ".useful-helpers")) or (
                        line and not line.startswith("cd ") and "run." in line):
                    return line.split("(")[0].strip()
            return None
    return None


def _target_digest(target: Path) -> dict:
    """sha256 of every TARGET-OWNED file, keyed by relative path.

    Excludes the instance namespace, which setup is allowed to create. Everything
    else must be byte-identical across an install - measured, not sampled.
    """
    import hashlib
    out = {}
    for p in sorted(target.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(target).as_posix()
        if rel.split("/", 1)[0] in (DEFAULT_HOME, ".uh-renamed"):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _clean_env() -> dict:
    """No hints. Resolution must be structural or it is not resolution."""
    return {k: v for k, v in os.environ.items() if not k.startswith("SUITE_")}


def check(r, root: Path) -> None:
    # ---- 1. one definition -------------------------------------------------
    inst = _load(root, "src.core.instance")
    r.check("an instance definition module exists", inst is not None,
            f"expected {CORE} - what an installed instance IS must be stated once. "
            "Four surfaces answer it today: config.py by marker, _toolkit.py by env "
            "and basename, and two installers by their own constant")
    for fn in ("create", "resolve", "InstanceContext"):
        r.check(f"the instance module exposes {fn}",
                inst is not None and hasattr(inst, fn),
                f"expected src.core.instance.{fn}")

    # ---- 2. ONE RESOLVER: census of writers AND readers ---------------------
    # The earlier draft censused only sites that WRITE a marker. `suite_home()` -
    # env-or-cwd - writes nothing, is used far more widely, and is the other half of
    # the same guess. Fixing one and passing would have left the defect half-alive.
    # PRODUCTION SCOPE vs TEST SCOPE are different rules, deliberately.
    #
    #   production: no active product code outside the core may define, serialise or
    #               interpret the identity format.
    #   tests:      may INSPECT the persisted representation - that is what a
    #               serialisation contract test IS - but must not become a second
    #               PRODUCER by hand-writing an approximate manifest whenever they
    #               need an instance. They create instances through the public API.
    #
    # Scanning both identically would turn "one authority" into "nobody may test the
    # file format", which is a different and worse rule.
    # TEST SCOPE IS `tests/` ONLY.
    #
    # `_harness/` was in this set, and that is how it vanished from the census while
    # still hand-writing a `.suite_sidecar` marker. Test scope only checks for
    # producing `instance.json`; the harness produced the RETIRED marker instead, so
    # it slipped both branches and the census reported a clean [].
    #
    # It disappeared because the census excluded it, not because it stopped
    # manufacturing identity - which is the one outcome this assertion exists to
    # distinguish. The harness is a VERIFIER: it may observe an installation, and it
    # may stage fixtures, but a verifier that reimplements the thing it verifies is
    # not observing it. It is held to the production invariant.
    def _is_test_scope(rel: str) -> bool:
        return rel.startswith("tests/")

    writers, test_producers, inferrers = [], [], []
    for rel, body in _ours(root):
        if rel == IDENTITY_RESOLVER:
            continue
        code = _code_only(body)          # docstrings are history, not behaviour
        touches_format = bool(
            re.search(r'["\']\.suite_sidecar["\']', code)
            or re.search(r'instance\.json["\']', code))
        if touches_format:
            if _is_test_scope(rel):
                # Producing, not inspecting: writing the manifest by hand.
                if re.search(r'instance\.json["\'][^\n]*\)\s*\.write_text', code) \
                        or re.search(r'write_text\([^)]*schema', code):
                    test_producers.append(rel)
            else:
                writers.append(rel)
        # INFERENCE, not transport: a fallback chain for "where am I".
        if re.search(r'environ\.get\(\s*["\']SUITE_HOME["\']\s*\)\s*or\b', code) \
                or re.search(r'\{\s*["\']\.useful-helpers["\']\s*\}', code) \
                or "toolkit_home_names" in code:
            inferrers.append(rel)

    r.check("only the instance core knows the identity format",
            not writers,
            f"active product code still defines or interprets identity: {writers}")
    r.check("tests consume the identity API rather than producing identity",
            not test_producers,
            f"tests hand-writing a manifest: {test_producers} - a test may inspect "
            "the persisted representation; it may not become a second producer of it")
    r.check("no component infers its own location",
            not inferrers,
            f"sites still guessing where they are: {inferrers} - transport is fine "
            "(the seam may pass a resolved INSTANCE_ROOT through SUITE_HOME); "
            "inference is not (a fallback chain of env, cwd, and a hardcoded basename)")

    # ---- 3. the runtime installer is retired, not renamed ------------------
    # CODE references only. An accurate comment recording that a runtime installer
    # once existed is history, not an entrance - and a gate that demanded its deletion
    # would be forcing the architecture to grow around the check.
    entrances = []
    for rel, body in _ours(root):
        # The SETUP APPLICATION is the canonical installation entrance, so of course
        # it installs. Excluded by identity, not by pattern: the invariant is that no
        # INSTALLED RUNTIME surface reproduces the sidecar, and `packaging/` is not
        # installed runtime - it ships beside the payload (Charter
        # SIDECAR:SETUP-DISTRIBUTION).
        if rel.startswith(("gates/", "_docs/", "packaging/")) or rel == CORE:
            continue
        code = _code_only(body)
        for pat in INSTALL_INVOCATION:
            if re.search(pat, code, re.M):
                entrances.append(f"{rel} ({pat[:30]})")
                break
    # The registry is the ADVERTISEMENT: a tool.json is how an installed instance
    # tells a human or an agent that installing another sidecar is a capability.
    if (root / "tools" / "sidecar_install" / "tool.json").is_file():
        entrances.append("tools/sidecar_install/tool.json (registered)")
    r.check("no runtime installation entrance remains",
            not entrances,
            f"still present: {entrances} - retiring the tool manifest while a CLI "
            "route, a GUI view or a probe still offers it is cosmetic. An installed "
            "instance operates on its target; it does not reproduce itself")

    if not r.filesystem_permits_unlink(root):
        r.skip("the product installer creates a resolvable instance",
               "this filesystem denies unlink; an install cannot be performed here")
        return

    # ---- 4. RULE 8 -- install through the PRODUCT's entrance ---------------
    payload = _materialise_payload(root)
    r.check("a payload fixture can be materialised for the installer", payload is not None,
            "the gate must hand the real installer something to install; the "
            "canonical assembler is a later tranche")
    if payload is None:
        return

    target = Path(tempfile.mkdtemp(prefix="t06-target-")) / "proj"
    target.mkdir()
    (target / "README.md").write_text("HOST OWNS THIS\n", encoding="utf-8")
    (target / "src").mkdir()
    (target / "src" / "app.py").write_text("print('host')\n", encoding="utf-8")
    (target / "src" / "deep").mkdir()
    (target / "src" / "deep" / "notes.txt").write_text("keep me\n", encoding="utf-8")
    before = _target_digest(target)

    proc = _install(root, target, payload)
    home = target / DEFAULT_HOME
    r.check("the product installer completes", home.is_dir(),
            f"rc={proc.returncode} {(proc.stderr or proc.stdout)[-300:]}")
    if not home.is_dir():
        return

    # ---- WALK STEP 4: IT LAUNCHES, BY THE COMMAND IT PRINTS ---------------
    # The single most embarrassing gap T6 had. Every other assertion here proved
    # something about an instance that had never been STARTED - because the probe
    # below does `sys.path.insert(0, home)` itself, which proves resolution works when
    # the caller fixes the environment, not that the product runs.
    #
    # Meanwhile the installer's own success message named
    # `python .useful-helpers/src/app.py cli tool-list`, which died with
    # ModuleNotFoundError. A freshly installed sidecar could not be started by
    # following its own instructions, and the suite was entirely green.
    #
    # So: take the command the installer PRINTS, and run it. No path help, no cwd
    # convenience, nothing added. If the documented entrance does not work, the
    # product does not work, whatever the other assertions say.
    printed = _installer_next(proc.stdout or "")
    r.check("the installer prints a launch command", bool(printed),
            "an install that does not say how to start is not finished")
    if printed:
        launched = subprocess.run(printed, shell=True, cwd=str(target),
                                  capture_output=True, text=True, timeout=300,
                                  env=_clean_env())
        r.check("the printed launch command actually runs",
                launched.returncode == 0,
                f"`{printed}` from {target} exited {launched.returncode}: "
                f"{(launched.stderr or launched.stdout)[-300:]}")

    # Run by PATH as well, because that is what anyone will type first and it is
    # what the old message told them to do.
    by_path = subprocess.run(
        [sys.executable, str(home / "src" / "app.py"), "cli", "tool-list"],
        cwd=str(target), capture_output=True, text=True, timeout=300,
        env=_clean_env())
    r.check("the instance runs when invoked by path",
            by_path.returncode == 0,
            f"python <instance>/src/app.py exited {by_path.returncode}: "
            f"{(by_path.stderr or by_path.stdout)[-300:]} - running a file by path "
            "puts its own directory on sys.path, not the instance root")

    # WALK STEP 5 - the sidecar identifies itself and its target.
    uuid_before = _identity(root, home)
    r.check("the installed instance resolves its own target",
            _target_of(home) == target.resolve(),
            f"{INSTALLER} writes no evidence of instancehood, so resolve_paths finds "
            "no target and the sidecar has no reality to operate on")
    r.check("the instance has a durable identity", bool(uuid_before),
            "an identity that cannot be read back cannot survive an update")

    # ---- 5. WALK STEP 14 -- move target AND instance together --------------
    # Also proves identity is not the basename, WITHOUT a --folder product option:
    # the instance is renamed in place first.
    renamed = target / ".uh-renamed"
    home.rename(renamed)
    r.check("identity does not depend on the instance folder name",
            _target_of(renamed) == target.resolve(),
            "resolution must not consult the basename; a rename is not a reinstall")

    moved_parent = Path(tempfile.mkdtemp(prefix="t06-moved-"))
    shutil.move(str(target), str(moved_parent / "relocated"))
    moved = moved_parent / "relocated"
    r.check("identity survives target and instance moving together",
            _target_of(moved / ".uh-renamed") == moved.resolve(),
            "identity is where it IS plus a relative relationship - never an absolute "
            "path serialised at install time")

    # ---- 6. WALK STEP 13 -- update preserves identity ---------------------
    # `--mode update` wipes the instance root and recopies, preserving only _state.
    # With identity in a manifest INSIDE that root, update mints a NEW identity for
    # the same instance - continuity broken on the first upgrade, silently.
    (moved / ".uh-renamed").rename(moved / DEFAULT_HOME)
    upd = _install(root, moved, payload, mode="update")
    r.check("update completes", (moved / DEFAULT_HOME).is_dir(),
            f"rc={upd.returncode} {(upd.stderr or upd.stdout)[-200:]}")
    after = _identity(root, moved / DEFAULT_HOME)
    r.check("update preserves the instance identity",
            bool(uuid_before) and after == uuid_before,
            f"before={uuid_before!r} after={after!r} - an update is the same instance "
            "with newer code; a new identity would orphan every durable record keyed "
            "to the old one. Two absent identities are not a preserved identity")

    # ---- 7. malformed identity fails LOUDLY -------------------------------
    # The defect this guards is the one config.py already refuses elsewhere: a broken
    # binding that resolves to a plausible guess and reports success.
    manifest = _manifest_path(moved / DEFAULT_HOME)
    r.check("the identity manifest is findable", manifest is not None,
            "expected a small identity file inside the instance root")
    if manifest is not None:
        manifest.write_text("{ not valid json", encoding="utf-8")
        resolved = _target_of(moved / DEFAULT_HOME)
        err = _LAST_ERR[0] if _LAST_ERR else None
        r.check("malformed identity does not resolve to a target",
                resolved is None,
                f"a corrupt manifest resolved to {resolved} - it must refuse, not "
                "fall back to the parent directory and report success")
        r.check("malformed identity fails LOUDLY, not silently",
                bool(err) and "InstanceError" in str(err),
                f"resolution reported {err!r}. Absence and corruption must be "
                "distinguishable: a silent None satisfies 'did not resolve' just as "
                "well as a raised error, so the previous check proved the weaker half")

    # ---- 8. WALK STEP 15 -- target-owned content untouched ----------------
    # WHOLE-TARGET COMPARISON, not a spot check. The previous version read one file
    # and asserted another existed, which cannot see a modified third file, a deleted
    # one, or anything added outside the top level. E8's install row deserves the
    # evidence it claims.
    after = _target_digest(moved)
    r.check("installation left target-owned content byte-identical",
            before == after,
            f"target-owned content changed: only in before={sorted(set(before) - set(after))[:4]} "
            f"only in after={sorted(set(after) - set(before))[:4]} "
            f"differing={[k for k in set(before) & set(after) if before[k] != after[k]][:4]} "
            "- Charter SIDECAR:TARGET-OWNERSHIP: setup may create the reserved "
            "namespace and nothing else")
    r.check("installation created exactly one directory in the target",
            {p.name for p in moved.iterdir()} == {"README.md", "src", DEFAULT_HOME},
            f"target contains {sorted(p.name for p in moved.iterdir())}")


# --------------------------------------------------------------------------
def _materialise_payload(root: Path) -> "Path | None":
    """A payload FIXTURE from today's manifest authority. Not the canonical assembler."""
    try:
        sys.path.insert(0, str(root))
        from src.core import payload as manifest
        dst = Path(tempfile.mkdtemp(prefix="t06-payload-")) / "toolkit"
        shutil.copytree(root, dst,
                        ignore=shutil.ignore_patterns(*manifest.PAYLOAD_EXCLUDE))
        return dst if (dst / "src").is_dir() else None
    except Exception:
        return None
    finally:
        if str(root) in sys.path:
            sys.path.remove(str(root))


def _install(root: Path, target: Path, payload: Path, mode: str = "install"):
    return subprocess.run(
        [sys.executable, str(root / INSTALLER), "--target", str(target),
         "--payload", str(payload), "--mode", mode],
        cwd=root, capture_output=True, text=True, timeout=600, env=_clean_env())


def _target_of(home: Path) -> "Path | None":
    """Ask the INSTALLED copy what its target is, in its own process, with no hints."""
    # Written to a FILE, not passed with -c. An earlier revision built a one-liner
    # in which `try:` followed a semicolon - not valid Python - so the probe always
    # died and every resolution assertion failed for a reason that had nothing to do
    # with the product. A check that cannot execute is absent, not failing.
    probe = "\n".join((
        "import json, sys",
        "sys.path.insert(0, sys.argv[1])",
        "from pathlib import Path",
        "err = None",
        "try:",
        "    from src.core.config import resolve_paths",
        "    p = resolve_paths(Path(sys.argv[1]))",
        "    t = str(p.project_root) if p.project_root else None",
        "except Exception as e:",
        "    t, err = None, f'{type(e).__name__}: {e}'",
        "print(json.dumps({'t': t, 'err': err}))",
    ))
    script = Path(tempfile.mkdtemp(prefix="t06-probe-")) / "probe.py"
    script.write_text(probe, encoding="utf-8")
    out = subprocess.run([sys.executable, str(script), str(home)],
                         capture_output=True, text=True, timeout=180, env=_clean_env())
    for line in reversed((out.stdout or "").splitlines()):
        if line.strip().startswith("{"):
            doc = json.loads(line)
            got = doc.get("t")
            _LAST_ERR.clear()
            _LAST_ERR.append(doc.get("err"))
            return Path(got).resolve() if got else None
    _LAST_ERR.clear()
    _LAST_ERR.append("probe produced no verdict")
    return None


# The probe's error text, kept because discarding it made an assertion prove less
# than its name. "fails loudly" was checked as `_target_of(...) is None`, and a SILENT
# None satisfies that exactly as well as a raised InstanceError does. Given this
# project's record of assertions passing for the wrong reason, the distinction is now
# carried out of the subprocess rather than thrown away at the boundary.
_LAST_ERR: list = []


def _manifest_path(home: Path) -> "Path | None":
    for name in ("instance.json", ".instance.json"):
        if (home / name).is_file():
            return home / name
    return None


def _identity(root: Path, home: Path) -> "str | None":
    m = _manifest_path(home)
    if m is None:
        return None
    try:
        return json.loads(m.read_text(encoding="utf-8")).get("uuid")
    except Exception:
        return None
