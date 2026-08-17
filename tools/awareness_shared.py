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

            1. THE FINGERPRINT EXCLUDES VOLATILE OBSERVATION METADATA.
               Hashing raw contributor output would fold in timestamps, durations and
               absolute host paths, so observing an unchanged target twice would produce two
               fingerprints and the whole idea would collapse on its first use. `_normalize`
               strips a declared volatile key set and tokenizes the target path, then
               serializes with sorted keys. What is hashed is WHAT WAS SEEN, never WHEN.

            2. REVISION IDENTITY IS CONTENT-ANCHORED, NOT SEQUENTIAL.
               `revision = H(instance, scope, evidence_fingerprint)`. A counter would make
               "revision 5" mean "the fifth run" - it would differ after a no-op re-observe
               and survive a real change, which is exactly backwards. Content anchoring makes
               restart-persistence and re-observation stability fall out rather than needing
               to be defended separately.

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

# Keys whose values describe the OBSERVATION rather than the TARGET. Excluded from the
# fingerprint by name, declared here so the exclusion is auditable rather than ad hoc.
VOLATILE_KEYS = frozenset({
    "generated_at", "observed_at", "timestamp", "duration_ms", "elapsed", "elapsed_ms",
    "root", "path", "cwd", "target", "db", "evidence_id", "op_id", "started", "created",
})


def _normalize(value, target: str):
    """Strip volatile metadata and tokenize host paths. Deterministic by construction.

    Recursive because contributor payloads nest, and a volatile key three levels down
    poisons the hash exactly as surely as one at the top.
    """
    if isinstance(value, dict):
        return {k: _normalize(v, target) for k, v in sorted(value.items())
                if k not in VOLATILE_KEYS}
    if isinstance(value, list):
        return [_normalize(v, target) for v in value]
    if isinstance(value, str) and target and target in value:
        # An absolute host path makes the same target fingerprint differently after a
        # move - which T6 went to some trouble to make survivable.
        return value.replace(target, "<target>")
    return value


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
    target = str(project_root())
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
            "normalized": _normalize(output, target),
        })
    return seen


def fingerprint(scope: str, observations: list) -> str:
    """H(scope, [(tool, normalized output)]) - what was seen, never when (semantic 1)."""
    body = {"scope": scope,
            "observations": sorted(
                ({"tool": o["tool"], "seen": o.get("normalized"), "ok": o.get("ok")}
                 for o in observations),
                key=lambda o: o["tool"])}
    return _digest(body)


def revision_id(instance: str | None, scope: str, evidence_fingerprint: str) -> str:
    """Content-anchored, not sequential (semantic 2)."""
    return _digest({"instance": instance, "scope": scope, "evidence": evidence_fingerprint})[:16]


def _findings(observations: list) -> dict:
    """Compact, domain-shaped, small. The SUMMARY projection only."""
    out = {}
    for o in observations:
        if not o.get("ok"):
            continue
        body = o.get("output") or {}
        if o["tool"] == "report":
            out["code_shape"] = body.get("summary")
        elif o["tool"] == "import_graph":
            s = body.get("summary") or {}
            hot = [h.get("module") or h.get("name") for h in (body.get("hotspots") or [])[:5]]
            out["dependencies"] = {"summary": s, "hubs": [h for h in hot if h]}
        elif o["tool"] == "dead_code":
            out["unused"] = body.get("summary")
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


def build(pmap: dict, probe: dict, stale: bool) -> dict:
    """Compose one awareness revision and persist it. Returns the compact envelope."""
    scope = str(project_root())
    instance = instance_uuid()
    obs = observe((pmap or {}).get("domain") or "generic", probe)
    fp = fingerprint(scope, obs)
    rev = revision_id(instance, scope, fp)
    envelope = {
        "schema": SCHEMA,
        "revision": rev,
        "evidence_fingerprint": fp,
        "instance": instance,
        "scope": scope,
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
