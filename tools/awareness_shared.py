"""
FILE:       tools/awareness_shared.py
ROLE:       Compose existing tool output into one persisted awareness revision.
DOMAIN:     tool (shared)
DOES:       Runs the appropriate deterministic contributors THROUGH THE SEAM, captures each
            raw output as content-addressed evidence, derives a normalized evidence
            fingerprint, anchors a revision id to instance+scope+evidence, and persists the
            compact envelope under the state root.
DEPENDS ON: tools._toolkit (seam_call, roots, instance_uuid), (stdlib) hashlib, json
WIRES TO:   consumed by tools/attach; the persisted revision is what T8 will refresh
NOTES:      A SHARED MODULE, NOT AN APPLICATION, and not new orchestration inside `attach`.
            `attach` is already 1051 lines carrying privately-owned capability (journal 0032),
            and C1a.3 forbids adding to that mass. This composes; it re-implements nothing.
            Every contributor is invoked with `seam_call`, so each one is authority-checked
            and audit-logged exactly as a direct call would be.

            FOUR SEMANTICS, LOCKED BEFORE IMPLEMENTATION (operator, 2026-08-16). Each exists
            because the obvious implementation would have been subtly wrong.

            1. ONLY SEMANTICALLY SELECTED OBSERVATION DATA ENTERS EVIDENCE IDENTITY.
               Runtime and envelope metadata never enters the canonical payload in the
               first place, rather than being scrubbed out of it afterwards.
               `canonical_observation()` SELECTS; see the block below it for why the first
               version - a recursive denylist of key NAMES - was wrong in both directions.
               What is hashed is WHAT WAS SEEN, never WHEN or WHERE.

            2. REVISION IDENTITY IS CONTENT-ANCHORED, NOT SEQUENTIAL, AND NOT LOCATIONAL.
               `revision = H(instance, RELATIVE scope, evidence_fingerprint)`. A counter
               would make "revision 5" mean "the fifth run" - differing after a no-op
               re-observe and surviving a real change, exactly backwards. An ABSOLUTE
               scope was worse: it made a relocated target look changed, reintroducing
               the absolute-path identity T6 spent a tranche removing. Content anchoring
               makes restart-persistence, re-observation stability and move-survival all
               fall out instead of each needing its own defence.

            3. HANDLES ARE IDENTIFIERS OWNED BY EXISTING TOOLS.
               A handle is `{tool, id, resolve_with}` - a pointer INTO an existing tool's
               namespace, carrying the tool that owns it. No handle registry, no handle types,
               no new naming scheme. Awareness may only promote an identifier some tool will
               already accept; anything else is a pseudo-identifier, which is the failure mode
               that produced `CellBackend`.

            4. DRILL-DOWN RECOVERS THE EVIDENCE ACTUALLY USED.
               Provenance stores a content-addressed `evidence_id` captured AT OBSERVATION
               TIME, never a re-runnable invocation. Re-running a contributor observes the
               target as it is now, so it answers "what did revision X know?" with "what would
               I know today?" - a plausible answer substituted for the true one, and it would
               make a persisted revision unfalsifiable.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from tools._toolkit import instance_uuid, project_root, seam_call, state_root

SCHEMA = 1
AWARENESS_DIR = "awareness"
CURRENT = "current.json"

# ---------------------------------------------------------------------------------
# CANONICALIZATION. Only SEMANTICALLY SELECTED observation data enters evidence
# identity; runtime and envelope metadata never enters it in the first place.
#
# The first version did the opposite and was wrong twice over. It carried a
# VOLATILE_KEYS set - `generated_at`, `duration_ms`, `root`, `path`, `target`, `db`,
# `created` ... - and stripped those key NAMES recursively from arbitrary tool output.
#
#   1. IT DISCARDED REAL EVIDENCE. `path` is which file a finding is about. `created`
#      is a record's own date. `db` is which database was inspected. For a records
#      target those are the evidence, not noise - so a finding moving from a.txt to
#      b.txt, or a record's date changing, produced the SAME fingerprint. Awareness
#      would have reported "nothing changed" about a target that had.
#
#   2. IT WAS A DENYLIST, so it could only ever be wrong in one direction: every future
#      contributor field is included until someone remembers to exclude it, and every
#      legitimate field sharing a listed name is silently destroyed.
#
# A key name cannot tell you whether a value is noise. Its POSITION can. So the
# canonical observation is built by SELECTION - the same compact projection `_findings`
# already derives - and runtime metadata lives structurally outside it.
# ---------------------------------------------------------------------------------


def _module_purposes(report_body: dict) -> dict:
    """One purpose line per module, preferring the PRIMARY CLASS docstring.

    Not the module docstring first, which was the obvious choice and the wrong one.
    Measured on `_theCELL`: `src/backend.py` has NO module docstring, and the line worth
    reading - "ROLE: Orchestration / Logic Hub - pure downstream task list runner" - is
    the docstring of `class Backend`. Same for the microservices: "The Hippocampus",
    "The Spine", "The Switchboard". In a class-oriented codebase the class carries the
    purpose and the module carries nothing.

    Measured here too, in the other direction: this project's own modules open with a
    `FILE: src/core/invoke.py` header line, so taking the module docstring first yielded
    "FILE: src/core/invoke.py" as the purpose of five hub modules - technically the first
    line, and worthless.

    Falls back to the module docstring when there is no documented class. Neither source
    is guaranteed to be meaningful, which is why `limitations` says so rather than
    implying otherwise.
    """
    out = {}
    for m in (report_body.get("modules") or []):
        rel = m.get("file")
        if not rel:
            continue
        doc = next((c.get("doc") for c in (m.get("classes") or []) if c.get("doc")), "")
        purpose = doc or m.get("purpose") or ""
        if purpose:
            out[rel] = purpose
    return out


def canonical_observation(tool: str, output: dict) -> dict:
    """The part of a contributor's output that IS the evidence, selected by meaning.

    An allowlist by construction: a field participates in identity because this function
    reached for it, never because nobody remembered to exclude it. A contributor whose
    projection is not known here contributes its `summary`, which is the one field the
    tool contract already declares to be a stable digest of what it found.
    """
    body = output or {}
    if tool == "report":
        # Purposes participate in identity: a module whose docstring changes has
        # changed, and a fingerprint that ignored it would report "nothing happened".
        return {"summary": body.get("summary"),
                "purposes": _module_purposes(body)}
    if tool == "import_graph":
        return {"summary": body.get("summary"),
                "hubs": sorted(h.get("module") or h.get("name")
                               for h in (body.get("hotspots") or [])
                               if h.get("module") or h.get("name")),
                "cycles": len(body.get("cycles") or [])}
    if tool == "dead_code":
        return {"summary": body.get("summary")}
    if tool == "sqlite_inspect":
        return {"tables": sorted((t or {}).get("name", "") for t in (body.get("tables") or []))}
    return {"summary": body.get("summary")}


def _digest(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"),
                   default=str).encode("utf-8")).hexdigest()


def contributors(domain: str, probe: dict) -> list:
    """Which deterministic tools to ask, chosen from EVIDENCE - never a fixed pipeline.

    The `_theCELL` set is what a Python-rich target demonstrated; a records folder and an
    empty directory legitimately use fewer. Returning [] is a valid answer and must produce
    a truthful thin envelope rather than an error.
    """
    files = int((probe or {}).get("file_count") or 0)
    if files == 0:
        return []
    out = [("report", {"path": "."})]
    if domain == "python-app":
        out += [("import_graph", {"root": "."}), ("dead_code", {"root": "."})]
    return out


def observe(domain: str, probe: dict) -> list:
    """Run each contributor through the seam and persist its raw output as evidence.

    The evidence is attached HERE, at observation time, because that is the only moment
    the output is the output for THIS revision (semantic 4).
    """
    seen = []
    for tool, args in contributors(domain, probe):
        res = seam_call(tool, args)
        if not res.get("ok"):
            seen.append({"tool": tool, "args": args, "ok": False,
                         "error": (res.get("error") or "call failed")[:200]})
            continue
        output = res.get("output") or {}
        ev = seam_call("evidence", {
            "action": "attach", "kind": "tool_output",
            "summary": f"{tool} observation for awareness",
            "body_json": output, "apply": True})
        seen.append({
            "tool": tool, "args": args, "ok": True, "output": output,
            "evidence_id": ((ev.get("output") or {}).get("evidence_id") if ev.get("ok")
                            else None),
            "canonical": canonical_observation(tool, output),
        })
    return seen


def fingerprint(rel_scope: str, observations: list) -> str:
    """H(relative scope, [(tool, canonical observation)]).

    THE SCOPE IS RELATIVE, and that is not cosmetic. The first version hashed
    `str(project_root())` - an ABSOLUTE path - so moving a target and its instance
    together changed the fingerprint and the revision although nothing about the target
    had changed. T6 spent a whole tranche removing absolute-path identity; this had
    quietly reintroduced it one layer up. A relative scope keeps the distinction that
    matters (whole target vs one subsystem) and drops the one that does not (where the
    drive happens to be mounted).
    """
    body = {"scope": rel_scope,
            "observations": sorted(
                ({"tool": o["tool"], "seen": o.get("canonical"), "ok": o.get("ok")}
                 for o in observations),
                key=lambda o: o["tool"])}
    return _digest(body)


def revision_id(instance: str | None, rel_scope: str, evidence_fingerprint: str) -> str:
    """Content-anchored, not sequential (semantic 2). Relative scope, never absolute."""
    return _digest({"instance": instance, "scope": rel_scope,
                    "evidence": evidence_fingerprint})[:16]


def _findings(observations: list) -> dict:
    """Compact, domain-shaped, small. The SUMMARY projection only.

    HUB PURPOSES ARE PROMOTED, and only the hubs'. The dogfood run on `_theCELL` is why:
    the envelope said "41 files, and `src.backend` is the hub" while the evidence it had
    just captured said `src.backend` is the "Orchestration / Logic Hub - pure downstream
    task list runner" wiring sixteen microservices. Naming the hub without saying what it
    does is a map that stops one word short of useful, and the word was already in hand.

    Only the hubs, because purpose for all 41 modules would be prose bulk in the default
    projection - the thing C2 exists to prevent. Everything else stays one drill-down
    away in the evidence.
    """
    out = {}
    purposes = {}
    hubs = []
    for o in observations:
        if not o.get("ok"):
            continue
        body = o.get("output") or {}
        if o["tool"] == "report":
            out["code_shape"] = body.get("summary")
            # THE SAME helper the canonical observation uses. Two selections of "the
            # purpose of a module" would be two authorities on one fact, and they would
            # disagree the first time either changed - which they already did: this line
            # read the module docstring while the canonical observation read the class,
            # so findings came back empty on exactly the codebases the class-preference
            # was written for.
            purposes = _module_purposes(body)
        elif o["tool"] == "import_graph":
            s_ = body.get("summary") or {}
            hubs = [h.get("module") or h.get("name")
                    for h in (body.get("hotspots") or [])[:5]]
            hubs = [h for h in hubs if h]
            out["dependencies"] = {"summary": s_, "hubs": hubs}
        elif o["tool"] == "dead_code":
            out["unused"] = body.get("summary")
    # Cross-reference two contributors this composition already holds: `import_graph`
    # says WHERE the gravity is, `report` says WHAT sits there. Neither tool changes.
    if hubs and purposes:
        named = {}
        for hub in hubs:
            rel = hub.replace(".", "/") + ".py"
            doc = purposes.get(rel) or purposes.get(hub)
            if doc:
                named[hub] = doc[:200]
        if named:
            out["hub_purposes"] = named
    return out


def _handles(observations: list) -> list:
    """Identifiers ALREADY OWNED by a tool, carrying their owner (semantic 3)."""
    handles = []
    for o in observations:
        if not o.get("ok") or o["tool"] != "import_graph":
            continue
        for hot in (o.get("output") or {}).get("hotspots", [])[:5]:
            mod = hot.get("module") or hot.get("name")
            if mod:
                handles.append({"tool": "symbol_graph", "id": mod, "kind": "module",
                                "resolve_with": {"action": "refs", "symbol": mod}})
    return handles


def _limitations(observations: list, probe: dict, pmap: dict) -> list:
    lim = list((pmap or {}).get("limits") or [])
    asked = {o["tool"] for o in observations}
    failed = [o["tool"] for o in observations if not o.get("ok")]
    if not observations:
        lim.append("No deterministic contributor applied to this target: there is nothing "
                   "here to observe yet. That is an honest map, not a failed one.")
    if failed:
        lim.append(f"These contributors did not complete, so their findings are absent: "
                   f"{sorted(failed)}")
    lim.append(f"Findings are composed from {sorted(asked) or 'no contributors'}; anything "
               "outside what those tools report is unknown, not absent.")
    return lim


def build(pmap: dict, probe: dict, stale: bool, *, scope_rel: str = "") -> dict:
    """Compose one awareness revision and persist it. Returns the compact envelope."""
    instance = instance_uuid()
    obs = observe((pmap or {}).get("domain") or "generic", probe)
    fp = fingerprint(scope_rel, obs)
    rev = revision_id(instance, scope_rel, fp)
    envelope = {
        "schema": SCHEMA,
        "revision": rev,
        "evidence_fingerprint": fp,
        "instance": instance,
        # DISPLAY vs IDENTITY, kept apart deliberately. `scope` is the absolute path a
        # reader wants to see; `scope_rel` is what participates in the revision. Folding
        # the absolute one into identity is what made a relocated target look changed.
        "scope": str(project_root()),
        "scope_rel": scope_rel,
        "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "findings": _findings(obs),
        "handles": _handles(obs),
        "provenance": {o["tool"]: {"evidence_id": o.get("evidence_id"),
                                   "ok": o.get("ok", False)} for o in obs},
        "limitations": _limitations(obs, probe, pmap),
        "freshness": {"stale": bool(stale), "contributors": len(obs)},
    }
    _persist(envelope)
    return envelope


def _persist(envelope: dict) -> None:
    """Durable, under the instance's state root, keyed by revision.

    `current.json` is a POINTER, not a second copy: a copy would be a second authority on
    what the current revision is, and the two would disagree the first time a write was
    interrupted.
    """
    d = state_root() / AWARENESS_DIR
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{envelope['revision']}.json").write_text(
        json.dumps(envelope, indent=2, default=str) + "\n", encoding="utf-8")
    (d / CURRENT).write_text(
        json.dumps({"revision": envelope["revision"]}, indent=2) + "\n", encoding="utf-8")


def load_current() -> dict:
    """The persisted current revision, or {}. This is what makes a restart cheap."""
    d = state_root() / AWARENESS_DIR
    try:
        rev = json.loads((d / CURRENT).read_text(encoding="utf-8")).get("revision")
        return json.loads((d / f"{rev}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
