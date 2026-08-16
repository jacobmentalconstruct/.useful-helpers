"""
FILE:       gates/t07_shared_awareness.py
ROLE:       Gate for T7 - Shared Project Awareness Prototype.
DOMAIN:     factory
DOES:       Builds three representative targets, installs a real instance into each, and
            asserts the awareness acceptance walk THROUGH THE PRODUCT'S OWN ENTRANCES.
NOTES:      Written at declaration, BEFORE implementation (protocol 3.2 rule 1), and
            deliberately BLACK-BOX.

            WHY BLACK-BOX MATTERS MORE HERE THAN ANYWHERE PREVIOUS. T7's nouns are
            seductive. "Awareness" invites an AwarenessManager, an AwarenessStore, an
            AwarenessEngine and a schema framework, none of which any requirement asks
            for. So this gate names NO module, NO class and NO file. It calls the
            product's entrances and inspects what comes back. Let the failing gate say
            what machinery is actually absent; do not decide in advance.

            WHAT THIS PROVES, IN PRODUCT TERMS. Charter 3.3 walk steps 6, 7, 8, and
            the awareness half of 13:

                6.  it maps the target
                7.  the user can inspect that map
                8.  an agent receives the SAME project awareness
                13. restarting destroys neither identity nor durable awareness

            FOUR PROPERTIES ARE STATED MECHANICALLY, NOT ADJECTIVALLY, because each has
            a history of degrading into a green assertion whose meaning drifted:

            1. CONTEXT REDUCTION IS A MEASURED RATIO, NOT "compact". The gate sums the
               serialized bytes of the contributors, measures the default projection,
               and holds it to a declared threshold. If dogfooding proves the threshold
               wrong it is changed DELIBERATELY, in one place, with a reason.

            2. A REVISION DESCRIBES OBSERVATIONS, NOT A COUNTER. "Revision 5" must mean
               "produced from this observed state", so the record carries a
               deterministic fingerprint of the evidence and scope beside the id. Same
               target unchanged -> same fingerprint. Target changed -> different one.
               Three distinct questions, three distinct fields:
                   instance uuid       who am I
                   revision id         what did I know
                   evidence fingerprint what observed reality produced that knowledge

            3. A CANONICAL HANDLE MUST ROUND-TRIP. Every handle awareness promotes has
               to be ACCEPTED BY THE TOOL THAT OWNS IT and resolve back to the entity it
               names. This is the anti-hallucination property, and it exists because a
               model in this project once invented `CellBackend` from a module name plus
               a project name and reported the resulting refusal as a capability gap.
               Awareness that emits a convenient pseudo-identifier is worse than
               awareness that emits none.

            4. DRILL-DOWN CROSSES BACK INTO EVIDENCE, NOT INTO MORE NARRATIVE. The gate
               does NOT require awareness to persist duplicate copies of every raw
               contributor response. It requires enough PROVENANCE to retrieve the
               canonical evidence. Storing the raw observation satisfies this; storing
               the invocation needed to re-obtain it satisfies this. What fails is a
               drill-down that returns prose - a model reconstructing what the evidence
               probably said.

            THREE TARGETS, AND THE POINT IS DEGRADATION. Software, records, empty. Equal
            richness is NOT required; truthful thinness is. Together they stop T7 from
            quietly becoming "Python Project Awareness": the empty target proves less
            evidence is not failure, and the records target proves software concepts are
            not imposed just because the richest contributor set came from software.

            RULE 8: the consumer entrances for shared awareness are the CLI (human) and
            MCP (agent). Both are exercised. A gate that reached inside instead would be
            asserting that the implementation exists, not that the product works.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OUTCOME = ("one compact evidence-backed awareness revision, persisted against the "
           "instance, identical for human and agent")

INSTALLER = "packaging/installer/install.py"
DEFAULT_HOME = ".useful-helpers"

# ---- the declared threshold, in ONE place ---------------------------------------
# Local compute is cheap; model context is expensive. Measured on `_theCELL`: `report`
# plus `dead_code` returned ~49 KB of envelope to supply seven summary integers. The
# ratio is what makes "rich evidence stays local" mechanical rather than aspirational.
MAX_PROJECTION_RATIO = 0.25      # default projection / summed contributor payload
MAX_PROJECTION_BYTES = 8192      # and an absolute ceiling, so a thin target cannot pass
                                 # by having no contributors to be a fraction of

# The envelope. Named here so a missing field is a NAMED failure, not a KeyError.
REQUIRED_FIELDS = (
    "revision",             # what did I know
    "evidence_fingerprint",  # what observed reality produced it
    "instance",             # who am I (the T6 uuid)
    "scope",                # what was looked at
    "observed_at",
    "findings",             # heterogeneous, domain-shaped, small
    "handles",              # canonical machine identifiers
    "provenance",           # which contributor produced which finding
    "limitations",          # what this map does NOT know
    "freshness",
)

# What a Python-rich target demonstrated on `_theCELL`. NOT a universal pipeline:
# contributor selection is evidence-driven, and the records/empty targets are expected
# to use fewer. This tuple is the gate's yardstick for the reduction ratio, not a
# requirement that awareness call exactly these.
SOFTWARE_CONTRIBUTORS = (
    ("report", {"path": "."}),
    ("import_graph", {"root": "."}),
    ("dead_code", {"root": "."}),
)


# Every assertion that cannot be evaluated until an awareness envelope exists. Listed
# so a declaration run shows the full requirement surface instead of stopping at the
# first missing prerequisite.
_DEPENDENT_ASSERTIONS = tuple(
    [f"awareness carries `{f}`" for f in REQUIRED_FIELDS] + [
        "re-observing an unchanged target yields the same evidence fingerprint",
        "changing the target changes the evidence fingerprint",
        "the revision is bound to the instance identity",
        "awareness survives a restart and reports the current revision",
        "the agent entrance reports the same awareness revision as the human one",
        "awareness promotes at least one canonical handle for a software target",
        "every canonical handle resolves through the tool that owns it",
        "the default projection is a measured fraction of the raw evidence",
        "provenance names the contributor behind a finding",
        "drill-down recovers canonical evidence, not re-synthesised prose",
        "awareness is produced with no `apps/` member in the path",
        "producing awareness left target-owned content byte-identical",
    ])


def _blocked(r, names, why: str) -> None:
    """Fail a set of assertions by name, with one shared reason.

    NOT `skip`. A skip says "this could not be measured here"; these can be measured
    and the answer is no. Calling them skipped would hide the tranche's real size
    behind an honest-looking word.
    """
    for n in names:
        r.check(n, False, why)


def check(r, root: Path) -> None:
    if not r.filesystem_permits_unlink(root):
        r.skip("awareness is produced through the product's entrances",
               "this filesystem denies unlink; an install cannot be performed here")
        return

    payload = _materialise_payload(root)
    r.check("a payload fixture can be materialised", payload is not None,
            "the gate installs real instances; the canonical assembler is a later tranche")
    if payload is None:
        return

    # ---- 0. the .git* prune regression (backlog, 0032) --------------------
    # NARROW ON PURPOSE. `_probe` prunes with `not d.startswith(".git")`, written for
    # `.git` and silently swallowing `.github`, `.gitlab` and anything else sharing the
    # prefix - so CI configuration is invisible to the map and `command_profile` cannot
    # find workflow files. One failing regression, one correction. This does NOT
    # generalise the exclusion subsystem; it asserts exactly one distinction.
    soft = _software_target()
    inst = _install(root, soft, payload)
    r.check("an instance installs into the software target", inst.returncode == 0,
            f"rc={inst.returncode} {(inst.stderr or inst.stdout)[-200:]}")
    if inst.returncode != 0:
        return
    home = soft / DEFAULT_HOME

    seen = _mapped_paths(home)
    r.check("`.git` metadata is excluded from the map",
            not any(p == ".git" or p.startswith(".git/") for p in seen),
            "git internals are not target content")
    r.check("`.github` is NOT excluded merely for sharing a prefix",
            any(p.startswith(".github/") for p in seen),
            "`.github` is absent from PRUNE; it disappears only because the prune test "
            "is `startswith('.git')`. CI configuration is exactly what a map of a "
            "target should see, and `command_profile` cannot find workflow files "
            "either. Assert the distinction, not a general exclusion redesign")

    # ---- 1. awareness exists, through the human entrance ------------------
    aw = _awareness(home)
    have = isinstance(aw, dict) and bool(aw)
    r.check("the product produces an awareness envelope", have,
            f"no awareness returned from the human entrance: {_LAST_ERR[:1]}")
    if not have:
        # DO NOT RETURN. Returning here would report two failures where twenty-five
        # requirements exist, and a reader would see "3 passing, 2 failing" and infer
        # the tranche was nearly done. Every dependent assertion is named and failed
        # explicitly, so the gate shows its WHOLE surface at declaration.
        #
        # This is the project's recurring defect stated as gate design: absence is
        # invisible in a column of green, and an assertion that never ran is absent,
        # not passing.
        _blocked(r, _DEPENDENT_ASSERTIONS,
                 "no awareness envelope exists yet, so this cannot be evaluated")
        _degradation_targets(r, root, payload)
        return

    for field in REQUIRED_FIELDS:
        r.check(f"awareness carries `{field}`", field in aw,
                f"present: {sorted(aw)}")

    # ---- 2. a revision describes observations, not a counter --------------
    fp1 = aw.get("evidence_fingerprint")
    again = _awareness(home)
    r.check("re-observing an unchanged target yields the same evidence fingerprint",
            bool(fp1) and again.get("evidence_fingerprint") == fp1,
            f"{fp1!r} then {again.get('evidence_fingerprint')!r} - a fingerprint that "
            "moves without the target moving cannot identify an observed state")

    (soft / "src" / "added_later.py").write_text("def later(): pass\n", encoding="utf-8")
    moved = _awareness(home, refresh=True)
    r.check("changing the target changes the evidence fingerprint",
            moved.get("evidence_fingerprint") not in (None, fp1),
            f"still {fp1!r} after a file was added - the fingerprint must describe the "
            "evidence, or 'revision X' means only 'the Nth time this ran'")
    r.check("the revision is bound to the instance identity",
            aw.get("instance") == _identity(home),
            f"awareness says {aw.get('instance')!r}, instance.json says "
            f"{_identity(home)!r} - awareness belongs to an instance, never to an "
            "absolute target path")

    # ---- 3. WALK STEP 13 -- it survives a restart -------------------------
    # Fresh process, no warm state. A revision held only in memory is not persisted.
    after_restart = _awareness(home)
    r.check("awareness survives a restart and reports the current revision",
            bool(after_restart.get("revision"))
            and after_restart.get("revision") == moved.get("revision"),
            f"{moved.get('revision')!r} before, {after_restart.get('revision')!r} after "
            "- each call is a separate process already; this asserts the revision is "
            "read from durable state rather than recomputed into a new identity")

    # ---- 4. WALK STEP 8 -- human and agent see the SAME revision ----------
    # Not "look similar". The same identifier, resolved mechanically.
    mcp_rev = _awareness_over_mcp(home)
    r.check("the agent entrance reports the same awareness revision as the human one",
            mcp_rev is not None and mcp_rev == after_restart.get("revision"),
            f"human={after_restart.get('revision')!r} agent={mcp_rev!r} - two "
            "projections of one revision, or two competing project models")

    # ---- 5. the anti-hallucination property -------------------------------
    handles = aw.get("handles") or []
    r.check("awareness promotes at least one canonical handle for a software target",
            bool(handles),
            "a target with modules and symbols must offer machine identifiers beside "
            "readable labels, or the next call reconstructs names from prose")
    unresolved = _unresolved_handles(home, handles)
    r.check("every canonical handle resolves through the tool that owns it",
            not unresolved,
            f"unresolved: {unresolved[:4]} - a handle awareness emits must be ACCEPTED "
            "by its owning tool and resolve back to the entity it names. This is the "
            "assertion that stops awareness inventing convenient pseudo-identifiers")

    # ---- 6. context reduction, measured ------------------------------------
    raw = _contributor_bytes(home)
    proj = len(json.dumps(aw, sort_keys=True).encode("utf-8"))
    ratio = (proj / raw) if raw else 1.0
    r.check("the default projection is a measured fraction of the raw evidence",
            raw > 0 and ratio <= MAX_PROJECTION_RATIO and proj <= MAX_PROJECTION_BYTES,
            f"contributors={raw}B projection={proj}B ratio={ratio:.3f} "
            f"(max {MAX_PROJECTION_RATIO}, ceiling {MAX_PROJECTION_BYTES}B) - rich "
            "evidence stays local; ordinary orientation must not shovel it into model "
            "context")

    # ---- 7. drill-down crosses back into EVIDENCE --------------------------
    # Deliberately NOT "returns a byte-identical copy": requiring that would force
    # awareness to persist duplicates of every contributor response. Provenance
    # sufficient to RETRIEVE the canonical evidence is equally legitimate. What must
    # not happen is a drill-down answered with narrative.
    prov = aw.get("provenance") or {}
    r.check("provenance names the contributor behind a finding",
            bool(prov),
            "without it, drill-down has nothing to cross back into")
    recovered, why = _drill_down(home, aw)
    r.check("drill-down recovers canonical evidence, not re-synthesised prose",
            recovered, why)

    # ---- 8. no application-layer dependency --------------------------------
    used = _tools_used(home)
    apps_used = sorted(t for t in used if _entry_of(root, t).startswith("apps/"))
    r.check("awareness is produced with no `apps/` member in the path",
            not apps_used,
            f"used {apps_used} - the acceptance walk must not require a specialised "
            "application layer (Charter SIDECAR:PRODUCT-SHAPE)")

    # ---- 9. THE TARGET IS NOT TOUCHED --------------------------------------
    r.check("producing awareness left target-owned content byte-identical",
            _target_digest(soft) == _digest_snapshot,
            "awareness is an Observe operation")

    # ---- 10. truthful degradation on the other two targets -----------------
    _degradation_targets(r, root, payload)


def _degradation_targets(r, root: Path, payload: Path) -> None:
    """Records and empty. Run independently of the software target's outcome.

    Independently on purpose: these prove *thin is legitimate*, and that property is
    exactly as interesting when the rich case is failing.
    """
    for name, builder in (("records", _records_target), ("empty", _empty_target)):
        tgt = builder()
        rc = _install(root, tgt, payload)
        if rc.returncode != 0:
            r.check(f"an instance installs into the {name} target", False,
                    f"rc={rc.returncode} {(rc.stderr or rc.stdout)[-200:]}")
            continue
        h = tgt / DEFAULT_HOME
        a = _awareness(h)
        r.check(f"the {name} target produces a truthful awareness envelope",
                isinstance(a, dict) and all(f in a for f in REQUIRED_FIELDS),
                f"got {sorted(a) if isinstance(a, dict) else a!r} - thin is a legitimate "
                "map, not an error and not a software ontology forced onto it")
        r.check(f"the {name} target declares what it does not know",
                bool((a or {}).get("limitations")),
                "honesty about absent evidence is the deliverable for a thin target")
        # GUARDED. `_has_software_ontology({})` is False, so an unguarded version of
        # this PASSES whenever awareness does not exist - an assertion satisfied for a
        # reason unrelated to the product, which is the defect family this project has
        # recorded seven times. It can only mean something once there are findings.
        if a.get("findings"):
            r.check(f"the {name} target does not invent software findings",
                    not _has_software_ontology(a),
                    f"findings={json.dumps(a.get('findings'))[:200]} - a folder of "
                    "documents has no modules, hotspots or dead code, and saying it "
                    "does is the failure this target exists to catch")
        else:
            r.check(f"the {name} target does not invent software findings", False,
                    "no findings to inspect; this cannot be evaluated yet. Recorded as "
                    "a failure rather than a pass, because an empty envelope satisfies "
                    "'contains no software concepts' trivially")


# --------------------------------------------------------------------------
# Fixtures. Three representative targets, built here so the gate owns its own inputs.
# --------------------------------------------------------------------------
def _software_target() -> Path:
    t = Path(tempfile.mkdtemp(prefix="t07-soft-")) / "proj"
    (t / "src").mkdir(parents=True)
    (t / ".github" / "workflows").mkdir(parents=True)
    (t / ".git").mkdir()
    (t / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (t / ".github" / "workflows" / "ci.yml").write_text(
        "name: ci\non: [push]\njobs:\n  t:\n    runs-on: ubuntu-latest\n", encoding="utf-8")
    (t / "README.md").write_text("# Demo\nA small application.\n", encoding="utf-8")
    (t / "requirements.txt").write_text("requests\n", encoding="utf-8")
    (t / "src" / "__init__.py").write_text("", encoding="utf-8")
    (t / "src" / "backend.py").write_text(
        '"""The hub."""\n\n\nclass Backend:\n    def start(self):\n        return 1\n',
        encoding="utf-8")
    (t / "src" / "app.py").write_text(
        "from src.backend import Backend\n\n\ndef main():\n    return Backend().start()\n",
        encoding="utf-8")
    (t / "src" / "orphan.py").write_text("def never_called():\n    return 0\n", encoding="utf-8")
    global _digest_snapshot
    _digest_snapshot = _target_digest(t)
    return t


def _records_target() -> Path:
    t = Path(tempfile.mkdtemp(prefix="t07-rec-")) / "records"
    (t / "2024").mkdir(parents=True)
    (t / "2025").mkdir(parents=True)
    (t / "index.csv").write_text("id,name,date\n1,Deed,2024-01-02\n", encoding="utf-8")
    for year in ("2024", "2025"):
        for i in range(4):
            (t / year / f"filing_{i}.txt").write_text(
                f"Record {i} for {year}. Filed under statute.\n", encoding="utf-8")
    (t / "NOTES.md").write_text("Scanned filings, one folder per year.\n", encoding="utf-8")
    return t


def _empty_target() -> Path:
    t = Path(tempfile.mkdtemp(prefix="t07-empty-")) / "blank"
    t.mkdir(parents=True)
    return t


_digest_snapshot: dict = {}


# --------------------------------------------------------------------------
# Entrances. Everything below drives the PRODUCT, never its internals.
# --------------------------------------------------------------------------
_LAST_ERR: list = []


def _cli(home: Path, tool: str, args: dict, timeout: int = 300):
    """One governed call through the human entrance, from the installed instance."""
    return subprocess.run(
        [sys.executable, "-m", "src.app", "cli", "tool-call",
         "--tool", tool, "--args-json", json.dumps(args)],
        cwd=home, capture_output=True, text=True, timeout=timeout, env=_clean_env())


def _output(proc) -> dict:
    """The tool's own payload out of the CLI envelope, or {} with the reason kept."""
    for line in reversed((proc.stdout or "").splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            doc = json.loads(line)
        except ValueError:
            continue
        return doc.get("output") or doc
    _LAST_ERR.insert(0, (proc.stderr or proc.stdout or "")[-300:])
    return {}


def _awareness(home: Path, *, refresh: bool = False) -> dict:
    """The compact current understanding, as the human entrance returns it.

    Asks the FRONT DOOR. The gate does not care whether awareness is composed inside
    `attach`, by a playbook, or by something not yet written - only that the product's
    documented entrance hands back the envelope.
    """
    args = {"refresh": True} if refresh else {}
    out = _output(_cli(home, "attach", args))
    aw = out.get("awareness")
    return aw if isinstance(aw, dict) else {}


def _awareness_over_mcp(home: Path) -> "str | None":
    """The revision id as an AGENT receives it, over the real MCP entrance."""
    req = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "t07-gate", "version": "1"}}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "attach", "arguments": {}}},
    ]
    stdin = "\n".join(json.dumps(m) for m in req) + "\n"
    try:
        proc = subprocess.run([sys.executable, "-m", "src.app", "mcp"], cwd=home,
                              input=stdin, capture_output=True, text=True,
                              timeout=300, env=_clean_env())
    except subprocess.TimeoutExpired:
        _LAST_ERR.insert(0, "mcp entrance timed out")
        return None
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            doc = json.loads(line)
        except ValueError:
            continue
        if doc.get("id") != 2:
            continue
        blob = json.dumps(doc)
        try:
            payload = json.loads(doc["result"]["content"][0]["text"])
        except (KeyError, IndexError, TypeError, ValueError):
            _LAST_ERR.insert(0, blob[:300])
            return None
        aw = (payload.get("output") or payload).get("awareness") or {}
        return aw.get("revision")
    _LAST_ERR.insert(0, (proc.stderr or "")[-300:])
    return None


def _unresolved_handles(home: Path, handles) -> list:
    """Feed each handle back to the tool that owns it. Anything refused is a defect.

    A handle carries its own owner - awareness that emits an identifier without saying
    which tool resolves it has not made it canonical, only decorative.
    """
    bad = []
    for h in list(handles)[:12]:
        if not isinstance(h, dict):
            bad.append(f"{h!r} (not an object with an owning tool)")
            continue
        tool, ident = h.get("tool"), h.get("id")
        if not tool or not ident:
            bad.append(f"{h!r} (missing tool/id)")
            continue
        out = _output(_cli(home, tool, dict(h.get("resolve_with") or {"symbol": ident})))
        if not out or out.get("ok") is False:
            bad.append(f"{tool}:{ident}")
    return bad


def _drill_down(home: Path, aw: dict) -> "tuple[bool, str]":
    """Can the caller cross from a finding back to canonical evidence?

    Satisfied EITHER by a stored raw observation OR by provenance sufficient to
    re-obtain it. Not satisfied by prose.
    """
    prov = aw.get("provenance") or {}
    if not isinstance(prov, dict) or not prov:
        return False, "no provenance to follow"
    for key, entry in list(prov.items())[:4]:
        if isinstance(entry, dict) and entry.get("evidence_id"):
            out = _output(_cli(home, "evidence",
                               {"action": "get", "evidence_id": entry["evidence_id"]}))
            if out.get("ok") is not False and out:
                return True, ""
        if isinstance(entry, dict) and entry.get("tool"):
            out = _output(_cli(home, entry["tool"], dict(entry.get("args") or {})))
            if out and out.get("ok") is not False:
                return True, ""
        return False, (f"provenance entry {key!r} = {entry!r} names neither a "
                       "retrievable evidence id nor a re-runnable invocation, so "
                       "drill-down can only return narrative")
    return False, "provenance carried no followable entry"


def _contributor_bytes(home: Path) -> int:
    """Summed serialized size of the raw contributor payloads - the denominator."""
    total = 0
    for tool, args in SOFTWARE_CONTRIBUTORS:
        out = _output(_cli(home, tool, args))
        total += len(json.dumps(out, sort_keys=True).encode("utf-8"))
    return total


def _tools_used(home: Path) -> set:
    """Which tools the ledger says were invoked. The seam already records this."""
    proc = subprocess.run(
        [sys.executable, "-c",
         "import sys,json;sys.path.insert(0,'.');"
         "from src.core.config import resolve_paths;from src.core import event_log;"
         "from pathlib import Path;p=resolve_paths(Path('.'));"
         "print(json.dumps([e.get('tool_id') for e in event_log.read(p, limit=500)]))"],
        cwd=home, capture_output=True, text=True, timeout=180, env=_clean_env())
    for line in reversed((proc.stdout or "").splitlines()):
        if line.strip().startswith("["):
            return {t for t in json.loads(line) if t}
    return set()


def _entry_of(root: Path, tool_id: str) -> str:
    reg = json.loads((root / "config" / "registry.json").read_text(encoding="utf-8"))
    for t in reg.get("tools", []):
        if t.get("id") == tool_id:
            return (t.get("invocation") or {}).get("entry", "")
    return ""


def _mapped_paths(home: Path) -> set:
    """Every target-relative path the map reports having seen."""
    out = _output(_cli(home, "attach", {"refresh": True}))
    pmap = out.get("project_map") or {}
    seen = set()
    for sub in (pmap.get("subsystems") or []) + (pmap.get("minor") or []):
        if sub.get("name"):
            seen.add(sub["name"] + "/")
    for ep in pmap.get("entry_points") or []:
        seen.add(ep)
    cp = _output(_cli(home, "command_profile", {"root": "."}))
    for c in cp.get("commands") or []:
        if c.get("source"):
            seen.add(c["source"])
    ft = _output(_cli(home, "file_tree", {"root": ".", "limit": 5000}))
    for row in ft.get("rows") or []:
        seen.add(row.get("path", ""))
    return {s for s in seen if s}


def _has_software_ontology(aw: dict) -> bool:
    """Did a non-software target get software concepts anyway?"""
    blob = json.dumps((aw or {}).get("findings") or {}).lower()
    return any(k in blob for k in ("hotspot", "dead_code", "import_graph", "symbol"))


# --------------------------------------------------------------------------
def _materialise_payload(root: Path) -> "Path | None":
    try:
        sys.path.insert(0, str(root))
        from src.core import payload as manifest
        dst = Path(tempfile.mkdtemp(prefix="t07-payload-")) / "toolkit"
        shutil.copytree(root, dst, ignore=shutil.ignore_patterns(*manifest.PAYLOAD_EXCLUDE))
        return dst if (dst / "src").is_dir() else None
    except Exception:
        return None
    finally:
        if str(root) in sys.path:
            sys.path.remove(str(root))


def _install(root: Path, target: Path, payload: Path):
    return subprocess.run(
        [sys.executable, str(root / INSTALLER), "--target", str(target),
         "--payload", str(payload), "--mode", "install"],
        cwd=root, capture_output=True, text=True, timeout=600, env=_clean_env())


def _identity(home: Path) -> "str | None":
    m = home / "instance.json"
    if not m.is_file():
        return None
    try:
        return json.loads(m.read_text(encoding="utf-8")).get("uuid")
    except Exception:
        return None


def _target_digest(target: Path) -> dict:
    """sha256 per target-owned file, excluding the instance root."""
    import hashlib
    out = {}
    for p in sorted(target.rglob("*")):
        if not p.is_file() or DEFAULT_HOME in p.parts:
            continue
        try:
            out[p.relative_to(target).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            continue
    return out


def _clean_env() -> dict:
    env = dict(os.environ)
    for k in ("SUITE_HOME", "SUITE_PROJECT_ROOT", "SUITE_STATE_ROOT"):
        env.pop(k, None)
    return env
