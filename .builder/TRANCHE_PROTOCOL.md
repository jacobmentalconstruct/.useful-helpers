# Tranche Protocol

Status: **APPROVED REPOSITORY PROTOCOL**

This protocol realizes the BCC workflow in this repository without reproducing its
general rules.

## Locations

- Declarations, amendments, approval submissions, parks, reopens, and supersessions:
  `.builder/journal/NNNN-<subject>.md`
- Tranche/closure gates: `.builder/gates/`
- Immutable run evidence: `.builder/evidence/<tranche>/<run-id>/`
- Product tests and target fixtures: `tests/`
- Sequence and status: `.builder/TRANCHE_PLAN.md`
- Resumability projection: `.builder/CURRENT_STATE.md`

Journal numbers increase monotonically. A correcting entry cites the entry it corrects.
Evidence directories are write-once once referenced by an approval or park entry.

## States and transitions

```text
PROVISIONAL -> DECLARED -> IMPLEMENTING -> VERIFYING -> AWAITING_APPROVAL
                                                           |
                                                    operator only
                                                           v
                                                        PARKED
```

The operator may return AWAITING_APPROVAL to IMPLEMENTING, or grant PARKED,
SUPERSEDED, WITHDRAWN, or another explicit terminal disposition. BLOCKED may interrupt
active work. A builder discovering a failed parked premise submits a bounded REOPEN
record and stops for operator ruling; historical entries and evidence remain unchanged.

## BCC workflow repository mapping

The BCC owns the required construction workflow and review discipline. This table only
maps its stages to repository mechanisms; it does not redefine the required activities.

| BCC-owned stage | Repository mechanism |
|---|---|
| ORIENT | Read current authorities/history/evidence and measure the live repository |
| DECLARE | A new numbered declaration in `.builder/journal/`; status in the Plan and Current State |
| EXECUTE | Changes on the declared surfaces; amendments receive later journal numbers |
| CONSOLIDATE | Hardening/discovery findings recorded in the active tranche history |
| VERIFY | The tranche entry in `.builder/gates/`; immutable output under `.builder/evidence/<tranche>/` |
| REVIEW | A numbered awaiting-approval entry and later operator ruling; Plan and Current State carry status |
| PARK | Operator-granted terminal disposition recorded in journal, Plan, and Current State |

STOP/outcome dependencies are owned by the Plan and Charter; discovery, reopen, and
supersession use later immutable journal entries. These mappings do not make Sidecar
Workbench the owner or required runtime of Coherent Development.

When this mapping and the BCC disagree, the BCC governs builder behavior. This protocol
governs only the repository locations and transitions shown here.

## Gate contract

Each declared tranche names exactly one authoritative gate entry under `.builder/gates/`.
The gate may invoke product tests and fixtures but owns the closure interpretation. It
must report PASS, FAIL, or UNSCORED per assertion and emit durable machine-readable
evidence. A gate cannot park a tranche.

T0 uses `.builder/gates/t0_bootstrap.py`. Later gates do not inherit T0 assertions by
copy; they may call shared gate components only after repetition demonstrates a genuine
shared owner.
