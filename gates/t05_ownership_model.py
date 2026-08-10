"""
FILE:       gates/t05_ownership_model.py
ROLE:       Gate for T5 - Ownership and Distribution Model.
DOMAIN:     factory
DOES:       Asserts the project has ONE authoritative statement of its deployment
            topology and ownership semantics, that no second live surface claims the
            same facts, and that the end-state conditions and audit findings have been
            restated against it.
NOTES:      Written during tranche declaration, BEFORE implementation, per
            .bcc/TRANCHE_PROTOCOL.md sec 3.2 rule 1.

            T5 is DEFINITIONAL. It moves no product module, builds no payload, splits
            no harness. So this gate asserts the MODEL and its consequences for the
            project's own authority surfaces - never implementation T5 deliberately
            does not build. A gate that reached for the implementation would make the
            tranche unclosable by design.

            Rule 8 is satisfied differently here than in T2-T4. There is no runtime
            entrance to a definition. The equivalent of a real entrance for a
            governance tranche is the ENTERING AGENT'S read path: the anchors an
            agent is told to resolve must actually resolve, and the facts must be
            reachable from the documented entry point rather than merely present
            somewhere in the tree. That is asserted, not assumed.

            The operator's amendment to the original gate language is load-bearing
            and encoded at check 4: NOT "no document states a boundary rule the model
            does not own" - the BCC legitimately owns generic builder boundaries
            while the Charter owns this product's topology - but "no two live
            normative surfaces claim ownership of the same fact."
"""
from __future__ import annotations

import re
from pathlib import Path

OUTCOME = "one authority per normative fact, and a stated deployment topology"

BCC = ".bcc/BUILDER-CONSTRAINT-CONTRACT.md"
CHARTER = ".bcc/CHARTER.md"
PLAN = ".bcc/TRANCHE_PLAN.md"
PROTOCOL = ".bcc/TRANCHE_PROTOCOL.md"
AUDIT = "_docs/AppJOURNAL/0018-project-audit.md"

# Product semantics, owned by the Charter. Not BCC-prefixed: these are this
# product's topology, not generic builder governance.
REQUIRED_ANCHORS = (
    "SIDECAR:SOURCE-FACTORY",
    "SIDECAR:SETUP-DISTRIBUTION",
    "SIDECAR:INSTALLABLE-PAYLOAD",
    "SIDECAR:INSTANCE-OWNERSHIP",
    "SIDECAR:TARGET-OWNERSHIP",
    "SIDECAR:EXTERNAL-CORPUS",
)

# The four roots that must stop sharing one word. `SIDECAR_ROOT` means the BCC's
# governance root in the contract and the product's instance root in architecture
# prose, and those are different abstractions.
REQUIRED_TERMS = ("TARGET_ROOT", "INSTANCE_ROOT", "GOVERNANCE_ROOT", "STATE_ROOT")

# The six domains, and the disposition axis. Classification is MULTIDIMENSIONAL by
# operator instruction: ownership and defect type are different questions, and
# collapsing them into one enum loses the distinction between ".github in the source
# repo" (valid) and ".github in the payload" (a leak).
DOMAINS = ("source/factory", "setup-distribution", "installable-payload",
           "installed-instance", "target-owned", "external-corpus")
DISPOSITIONS = ("valid", "stale", "development-lineage residue", "distribution leak",
                "target-boundary violation", "nonconformity", "superseded")


def _read(root: Path, rel: str) -> str:
    p = root / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


def check(r, root: Path) -> None:
    bcc = _read(root, BCC)
    charter = _read(root, CHARTER)
    plan = _read(root, PLAN)
    audit = _read(root, AUDIT)

    # ---- 0. RULE 8: the real consumer entrance ----------------------------
    # A governance model has no runtime capability to invoke. Its real consumer is
    # an ENTERING AGENT, and its entrance is the documented context-entry read path.
    # So walk it, exactly as an arriving agent is instructed to: start at the
    # documented entry anchor, follow what it gives, and require that the product
    # authority is reachable WITHOUT already knowing where it lives.
    #
    # Asserting the anchors exist somewhere in the tree would be the internal-seam
    # equivalent that rule 8 exists to forbid.
    entry = ""
    if "[ANCHOR: BCC-CONTEXT-ENTRY]" in bcc:
        entry = bcc.split("[ANCHOR: BCC-CONTEXT-ENTRY]", 1)[1].split("[ANCHOR:", 1)[0]
    r.check("the documented context entry exists", bool(entry.strip()),
            "BCC-CONTEXT-ENTRY is the read path an entering agent is told to follow")

    named = re.findall(r"`(BCC-[A-Z-]+)`", entry)
    r.check("the entry path names the one-authority rule",
            "BCC-ONE-AUTHORITY" in named,
            f"entry path offers {sorted(set(named))} - an agent following the "
            "documented path would never learn that facts have single owners")

    # Every anchor the entry path promises must actually resolve in the contract.
    unresolved = [a for a in set(named) if f"[ANCHOR: {a}]" not in bcc]
    r.check("every anchor the entry path names resolves",
            not unresolved, f"dangling: {sorted(unresolved)}")

    # And the path must lead to the product authority by name, not by luck.
    reachable = ("CHARTER" in bcc or "CHARTER" in entry)
    r.check("the entry path reaches the product authority",
            reachable and "SIDECAR:" in charter,
            "an agent must arrive at the Charter's ownership model by following the "
            "documented path, not by knowing an undocumented location")

    # ---- 1. the general rule, in the general document ----------------------
    # Scoped deliberately: "for each normative fact". An unscoped version would make
    # one document authority over everything, which is a different defect.
    r.check("the BCC carries the one-authority-per-normative-fact rule",
            "normative fact" in bcc and "hand-maintained" in bcc,
            "expected a rule in the BCC stating that exactly one surface owns each "
            "normative fact, and that a second hand-maintained representation is a "
            "defect even when the copies agree - five instances of that defect are "
            "recorded in journal 0018")

    # Scoped to the rule's own section rather than the whole document. The first
    # revision searched the file for "generated" and "verif" and PASSED at
    # declaration time, matching the word "verification" 300 lines away in an
    # unrelated rule. A check that passes before the work exists cannot detect the
    # work being done.
    # Split on the ANCHOR form, not the bare name: the first bare occurrence is the
    # entry in the anchor map, so slicing there measured the wrong section entirely.
    rule_section = ""
    if "[ANCHOR: BCC-ONE-AUTHORITY]" in bcc:
        rule_section = bcc.split("[ANCHOR: BCC-ONE-AUTHORITY]", 1)[1].split("[ANCHOR:", 1)[0]
    r.check("the rule has its own anchor",
            "BCC-ONE-AUTHORITY" in bcc,
            "the rule must be addressable, or nothing can point at it instead of "
            "restating it - which is the defect the rule exists to prevent")
    r.check("the rule permits consumers, generators and verifiers",
            all(w in rule_section for w in ("consume", "generated", "verif")),
            "a verifier that observes conformance is not a second authority; if the "
            "rule does not say so it forbids the gates, the harness and the tests")

    # ---- 2. the Charter owns product topology, and no new document does ----
    for a in REQUIRED_ANCHORS:
        r.check(f"anchor {a} exists in the Charter", a in charter,
                f"{a} must be defined in {CHARTER}")

    live = {p.name for p in (root / ".bcc").iterdir()} if (root / ".bcc").is_dir() else set()
    expected = {"BUILDER-CONSTRAINT-CONTRACT.md", "CHARTER.md",
                "TRANCHE_PROTOCOL.md", "TRANCHE_PLAN.md", "evidence"}
    r.check("no fifth authority document was created",
            live == expected,
            f"`.bcc` holds {sorted(live)}; the ownership model belongs in the "
            "Charter, which already owns product-specific architecture")

    # ---- 3. the topology is stated, and the runtime is not an installer ----
    r.check("the deployment topology is stated end to end",
            all(w in charter for w in ("setup", "payload", "instance", "target")),
            "source factory -> setup application -> canonical payload -> installed "
            "instance -> target must be explicit, not inferable")

    r.check("the installed runtime is not defined as an installer of sidecars",
            "does not vend" in charter or "not vend" in charter
            or "no additional instance" in charter,
            "an installed instance belongs to one target and does not reproduce "
            "itself; today `tools/sidecar_install` is registered runtime capability")

    r.check("the standalone packaging installer is named as the product entrance",
            "packaging/installer" in charter,
            "there are three installation implementations today; the Charter must "
            "say which one is the product's")

    # ---- 4. UNIQUE DECLARED NORMATIVE OWNERSHIP ---------------------------
    # What this proves, stated precisely: each ENUMERATED fact has exactly one
    # DECLARED owner. It does NOT prove the absence of semantic duplication -
    # natural-language paraphrase is not mechanically decidable, and a gate that
    # claimed otherwise would be lying about its own reach. An accidental prose
    # restatement that does not announce itself with the same identifier remains the
    # discovery pass's job (protocol 3.4) and critical review's.
    #
    # Not "one document owns all boundaries": the BCC owns generic builder
    # boundaries and the Charter owns product topology, legitimately and at once.
    # The defect is two live normative surfaces declaring the SAME fact.
    live_files = sorted((root / ".bcc").glob("*.md")) if (root / ".bcc").is_dir() else []
    for fact in REQUIRED_ANCHORS:
        owners = [f.name for f in live_files
                  if f"[OWNS: {fact}]" in f.read_text(encoding="utf-8", errors="replace")]
        r.check(f"{fact} has exactly one declared owner",
                owners == ["CHARTER.md"],
                f"declared by {owners or 'nobody'} - expected exactly ['CHARTER.md']")

    stray = []
    for f in live_files:
        body = f.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"\[OWNS: (SIDECAR:[A-Z-]+)\]", body):
            if m.group(1) not in REQUIRED_ANCHORS:
                stray.append(f"{f.name}:{m.group(1)}")
    r.check("no surface declares ownership of an unenumerated product fact",
            not stray,
            f"undeclared facts claimed: {stray} - a fact worth owning is worth "
            "enumerating, or the registry stops being a registry")

    r.check("the Plan cites the model rather than restating it",
            "SIDECAR:" in plan and "[OWNS:" not in plan,
            "TRANCHE_PLAN owns sequencing only; it must reference the Charter's "
            "identifiers and never declare ownership of them")

    # ---- 5. the four roots stop sharing one word --------------------------
    for term in REQUIRED_TERMS:
        r.check(f"{term} is a distinct named concept", term in charter,
                f"{term} must be defined; `SIDECAR_ROOT` currently means the BCC's "
                "governance root in the contract and the product's instance root in "
                "architecture prose")

    # ---- 6. the end-state conditions are restated -------------------------
    # E8 on a phase x authority matrix, because "the target is never modified" is
    # not the product invariant - an Apply tool exists precisely to modify it.
    r.check("E8 states lifecycle AND governed-runtime mutation semantics",
            all(w in charter for w in ("uninstall", "self-maint"))
            and ("declared write scope" in charter or "write scope" in charter),
            "E8 must cover install/update/uninstall/startup/self-maintenance as "
            "never silently mutating target-owned content, AND runtime mutation as "
            "permitted under an explicit governed operation")

    r.check("E11 states development blankness without banning self-knowledge",
            "self-knowledge" in charter and "lineage" in charter,
            "E11 must permit the instance manifest, reserved namespace, tool "
            "manifests and generic seed, while forbidding this build's journal, "
            "evidence, tranche history, builder identity and predecessor identity")

    # ---- 7. supersession, without rewriting history -----------------------
    # Also scoped. `supersede` already appears in the protocol's staleness criterion
    # and in the plan's T0 entry, so the loose forms of both of these PASSED at
    # declaration. The mechanism needs its own numbered section, and the
    # supersession needs its own record, or neither is findable by an entering agent.
    protocol = _read(root, PROTOCOL)
    r.check("the protocol defines supersession as its own mechanism",
            "Supersession" in protocol and "SUPERSEDED" in protocol,
            "a later operator-approved architecture decision must be able to retire "
            "an invariant proven by a parked tranche - naming the old invariant, "
            "why, its replacement, and atomically replacing its proof - without "
            "reopening the tranche or rewriting its journal. Expected a numbered "
            "section, not the word appearing in a staleness criterion")

    r.check("supersession requires the four elements, not just a note",
            all(w in protocol for w in ("names the exact", "replacement", "evidence")),
            "identify the old invariant, why it is no longer desired, its "
            "replacement, and preserve the historical evidence - a mechanism that "
            "requires less than that is silent disabling with extra steps")

    r.check("T1's self-hosting proof is explicitly marked superseded",
            "Superseded active proof" in plan and "self-host" in plan.lower(),
            "`payload.py` justifies shipping itself on the premise that a vended "
            "sidecar must vend itself; that premise is retired, and the assertion "
            "must not keep claiming current authority. Expected an explicit "
            "supersession record, not the word `superseded` in unrelated prose")

    # ---- 7b. THE SUPERSESSION ACTUALLY TOOK EFFECT ------------------------
    # The operator's requirement, and the one that makes the mechanism real: prose
    # saying "superseded" while the active suite still requires the retired premise
    # would leave two normative surfaces claiming opposite things - inside the very
    # tranche that wrote the one-authority rule.
    t01 = _read(root, "gates/t01_ship_manifest.py")
    still_active = [phrase for phrase in
                    ("the manifest itself ships",
                     "the payload can reproduce itself exactly")
                    if f'r.check("{phrase}' in t01]
    r.check("no superseded assertion remains in the active proof set",
            not still_active,
            f"still asserted in t01: {still_active}")

    r.check("the retired assertions are preserved with provenance",
            (root / "gates" / "_superseded" / "t01_self_hosting.py.superseded").is_file(),
            "removed from the active suite is not the same as deleted from project "
            "memory; §5.1 requires the code and its five provenance elements")

    r.check("the active suite no longer drives a second-generation vend",
            "gen2" not in t01,
            "the generation-2 install called `sidecar_install` from inside an "
            "installed sidecar - the exact `instance -> instance` behaviour the "
            "Charter now says is not a product requirement")

    # ---- 7c. PARTIAL COVERAGE IS DECLARED, NOT IMPLIED --------------------
    # A retained assertion whose coverage is known-incomplete is still worth having:
    # a tripwire that fires is information, and a deleted tripwire is nothing. What
    # is not acceptable is a partial sentinel wearing the epistemic label of a
    # comprehensive proof - a green column reads as completeness whatever the
    # assertion's own text says.
    #
    # So the limitation is DECLARED in the gate and PRINTED by the runner. Asserted
    # here rather than trusted, because an undeclared weakness is exactly a false
    # green, and this project has now produced four of those.
    r.check("gates with known-partial coverage declare it machine-visibly",
            "KNOWN_LIMITATIONS" in t01,
            "t01 retains two assertions of known-partial coverage - an incomplete "
            "predecessor sentinel set, and a payload fixture produced by legacy "
            "runtime machinery. Both must be declared, not left in the reader's head")

    runner = _read(root, "gates/run.py")
    r.check("the runner surfaces declared limitations beside the verdict",
            "KNOWN_LIMITATIONS" in runner and "PARTIAL" in runner,
            "a limitation recorded where only the gate's author reads it does not "
            "stop a green suite being misread as a complete proof")

    for phrase in ("no product authority", "TEST FIXTURE PRODUCER"):
        r.check(f"the legacy vend path is disclaimed ({phrase!r})",
                phrase in t01,
                "`sidecar_install` materialises the payload fixture because nothing "
                "else does yet. Its use must confer no product authority and prove "
                "nothing about canonical installation or setup lifecycle")

    # ---- 8. the audit is reclassified, on BOTH axes -----------------------
    r.check("audit findings carry an ownership domain",
            sum(1 for d in DOMAINS if d in audit) >= 4,
            f"expected the six domains in {AUDIT}; found "
            f"{[d for d in DOMAINS if d in audit]}")
    r.check("audit findings carry a disposition",
            sum(1 for d in DISPOSITIONS if d in audit) >= 4,
            "ownership and defect type are different axes; one enum cannot "
            "distinguish `.github` in the source repo from `.github` in the payload")

    # ---- 9. withdrawal left no competing state ----------------------------
    # A plan that says withdrawn while the runner still executes the gate is exactly
    # the competing project state this project was reset to remove.
    active = sorted(p.name for p in (root / "gates").glob("t[0-9][0-9]*_*.py"))
    r.check("the withdrawn T5a gate is out of active discovery",
            not any("t05a" in n for n in active),
            f"active gates: {active}")
    r.check("the withdrawn T5a gate is preserved with provenance",
            (root / "gates" / "_deferred" / "t05a_observe_select.py.deferred").is_file()
            and (root / "gates" / "_deferred" / "README.md").is_file(),
            "withdrawn is not deleted; its assertions are salvage for One Surface")
    r.check("the plan records T5a as withdrawn",
            "withdrawn" in plan.lower(),
            "TRANCHE_PLAN must not still present T5a as the next tranche")

    # ---- 10. authority surfaces stop lying about their own status ---------
    # Small lines, large semantic weight: these are the first thing an entering
    # agent reads to decide how much to trust the document.
    for name, body in (("Charter", charter), ("Plan", plan)):
        m = re.search(r"^Status:\s*\*\*(.+?)\*\*", body, re.M)
        status = m.group(1) if m else ""
        r.check(f"the {name}'s status header describes the project as it is",
                bool(status) and "DRAFT" not in status.upper()
                and "Nothing is built" not in body,
                f"{name} status reads {status!r} while T1-T4 are implemented and "
                "the scoreboard marks conditions met")
