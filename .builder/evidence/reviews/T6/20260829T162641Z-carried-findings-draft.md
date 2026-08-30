# Companion Draft: T6 Ruling and Carried-Findings Placement

Date: 2026-08-29T16:26:41Z
Author: The Reviewer
Companion to: `.builder/evidence/reviews/T6/20260829T123032Z-external-review.md`

## What this file is and is not

This is **review evidence only**. It is a drafting aid prepared at operator request so
that the disposition of every T6 review finding can be recorded with a reason rather than
left silent. It is not a ruling, not authority, not a journal entry, and not a Plan
amendment. Nothing here takes effect until the Operator rules and the Builder places the
text under its proper owner.

Every disposition below is marked **RECOMMENDED** and is the Reviewer's proposal. The
Operator confirms, changes, or rejects each one. Where an entry says
`OPERATOR DECISION:` the field must be resolved by the Operator before the Builder writes
it into history.

Placement follows the chain in the Reviewer manifest: external review evidence -> operator
ruling -> builder journal entry -> plan/current-state update.

---

## Part 1 - Entry `0042` is not drafted here, deliberately

The missing `0042-t6-awaiting-approval.md` is the **Builder's** record of what it
believed, attempted, changed, and why during T6 implementation. Under the BCC, journal
entries record first-hand construction history. I did not perform that work and cannot
supply that content; ghostwriting it would put invented belief into an immutable record
and would defeat the purpose of the entry existing at all.

What I can supply is the checklist of what `0042` must contain for the submission record
to be complete. The Builder writes it.

**Required contents of `0042`:**

1. Entry type (`review submission`), tranche (`T6 Removable MCP Entrance`), status
   (`AWAITING_APPROVAL`), and the date the work was actually submitted.
2. What was implemented: the MCP stdio adapter (`product/core/mcp.py`), the shared host
   status owner (`product/core/host.py`), the lazy CLI `mcp` subcommand, the focused
   fixtures (`tests/test_t6_mcp_entrance.py`), and the T6 gate
   (`.builder/gates/t6_mcp_entrance.py`).
3. The decision to narrow `.builder/gates/t3_epistemic_substrate.py` and
   `.builder/gates/t5_governed_mutation.py`: what was exempted, on which exact surfaces,
   why the exemption does not weaken the parked T3 and T5 outcomes, and the bound the
   Builder intended it to have. This is the single most important omission in the current
   record.
4. The authoritative T6 gate receipt and the cumulative T5/T4/T3/T2/T1/T0 receipts relied
   on, stated with the fact that they were produced against a working tree in which the
   two narrowed gates were still uncommitted.
5. Which declared completion-evidence items from `0040` the Builder considered met, and
   any it considered partially met or unmet.
6. An explicit statement that the entry does not park T6, credit P6, or begin T7.

Note for the Builder: `0042` should record the submission as it stood. It should not be
back-dated, and it should not be written as though it anticipated this review. Findings
raised after submission belong in `0043`.

---

## Part 2 - Draft `0043` verification return

Placement: `.builder/journal/0043-t6-verification-return.md`
Model precedent: `0013-t1-verification-return.md`, `0030-t4-verification-return.md`,
and `0032-t4-acceptance-review-return.md`.

Authorship note: under the Protocol the Builder writes the journal entry that records the
Operator's ruling. The text below is a draft of that entry with the Operator's decisions
marked. It must not be committed until the Operator has resolved every
`OPERATOR DECISION:` field.

```markdown
# 0043 - T6 Verification Return and Carried Construction Findings

Entry type: verification return
Tranche: T6 Removable MCP Entrance
Status: VERIFYING
Date: OPERATOR DECISION: <ruling date>

## Operator ruling

The Operator reviewed external Reviewer evidence at
`.builder/evidence/reviews/T6/20260829T123032Z-external-review.md`, disposition
RETURN TO VERIFYING, and its companion placement draft at
`.builder/evidence/reviews/T6/20260829T162641Z-carried-findings-draft.md`.

T6 returns from AWAITING_APPROVAL to VERIFYING for a bounded repair. This entry does not
park T6, credit P6, begin T7, widen T6 scope, or reopen T0-T5. Repair is confined to the
active T6 lifecycle and to the surfaces T6 already owns or already modified.

## Repair items - required before T6 may return to AWAITING_APPROVAL

R1. Create `0042-t6-awaiting-approval.md`, the missing submission record, including the
    T3/T5 gate-narrowing decision and its justification. Until it exists, the Plan,
    Current State, and Architecture cite an entry that does not exist, and the T6 gate's
    own `journal_continuity` check contradicts them by reporting the journal contiguous
    through `0041`.

R2. Repair the MCP tool-contract mismatch. `mcp._tool_descriptors` publishes each
    manifest `input_schema` with `additionalProperties: false` while
    `mcp._call_manifest_tool` accepts `_authority` and `_timeout` inside the same
    arguments object. Carry authority and timeout in the MCP call envelope, or declare
    them in the projected schema, so the advertised contract matches the accepted one.

R3. Add product fixtures for MCP above `observe` authority: an apply-authority write that
    succeeds and is receipted, the refusal path, and the resulting receipt/artifact. The
    declared completion evidence in `0040` covers only an observe tool, so the entrance's
    only mutating path currently ships unwitnessed.

R4. Emit the standard JSON error envelope from `sidecar mcp` when the adapter is absent,
    instead of an unhandled `ModuleNotFoundError` traceback with empty stdout, and assert
    it in `test_cli_survives_when_mcp_adapter_is_removed`.

R5. Stop replying to id-less JSON-RPC requests and accept `notifications/initialized`,
    with one fixture completing an `initialize` -> `notifications/initialized` ->
    `tools/list` handshake.
    OPERATOR DECISION: accept R5 as a T6 repair, or decline it and carry MCP client
    conformance to T8 under C3 below. If declined, the T6 park entry must state plainly
    that the entrance is JSON-RPC-shaped and not yet verified against any MCP client.

R6. Repair the two T6-gate assertions that do not discriminate. `_t6_surfaces` and
    `_mcp_import_violations` judge `product/core/cli.py` by the text above `def _parser`,
    so a module-level MCP import placed below that point passes both while genuinely
    breaking removability. Detect module-level imports in `cli.py` by AST, as the gate
    already does for every other module. Add at least one discrimination witness that
    runs the mutated system rather than grepping its own keywords.

R7. Re-run the authoritative T6 gate and the cumulative T5/T4/T3/T2/T1/T0 gates from a
    clean working tree at the repaired commit, and cite those receipts in the returning
    submission. The current authoritative receipts record
    `M .builder/gates/t3_epistemic_substrate.py` and
    `M .builder/gates/t5_governed_mutation.py` in `working_tree`, so their `head_commit`
    does not describe the measured state.

OPERATOR DECISION: confirm or amend R1-R7. Any item the Operator declines must be
restated below as a carried or declined finding so that no finding leaves this entry
without a disposition.

## Carried construction findings

These findings do not block T6 approval and are not absorbed into T6. They are recorded
here and referenced by the Plan so they cannot be silently lost. They are construction
machinery, not product features, and they are not candidates for the Plan's deferred
product ideas.

C1. Gate exemption idiom is coupled to editable Plan prose.
    `t3_epistemic_substrate.py` and `t5_governed_mutation.py` derive their `mcp`
    exemption from `"T6 Removable MCP Entrance | PROVISIONAL" not in plan`, read from
    `.builder/TRANCHE_PLAN.md`. With product source unchanged, editing that Plan cell
    flips both gates between PASS and FAIL, and the negative form fails open under any
    table reformat or tranche rename. The idiom predates T6 (`t4_has_started`) and was
    accepted through T4 and T5 review; T6 extended it to two parked tranches whose
    credit is already granted.
    RECOMMENDED disposition: carry to T7 as a named precondition. Replace the Plan
    substring test with an explicit allowlist constant in each gate, commented with the
    tranche that introduced each exemption. T7 and T8 will both add surfaces that trip
    these forbidden-term lists, so the cost of the idiom compounds with each further
    tranche.
    OPERATOR DECISION: carry to T7 / repair inside the T6 return / decline.

C2. MCP exposes the ungoverned immediate-write route and no route into the T5 governed
    mutation loop. After a successful MCP `tool.write_file` apply, all five mutation
    tables remain at zero. The MCP catalog carries `mutation.status`, `mutation.history`,
    and `mutation.links` but no `preview-write`, `approve`, or `apply`. This is within
    the scope `0040` declared and does not affect P6.
    RECOMMENDED disposition: carry to T8. The Charter acceptance walk already requires
    proposing, previewing, approving, applying, and measuring one exact change and
    inspecting the same world through CLI and MCP; T8 is where those two requirements
    meet. Record now whether the prototype accepts an agent entrance that can reach only
    the path around the governed loop.
    OPERATOR DECISION: carry to T8 / accept permanently as prototype scope / other.

C3. MCP client conformance is unverified. No evidence in T6 shows any MCP client
    completing a handshake; the fixtures drive the loop with this repository's own
    request shapes.
    RECOMMENDED disposition: carry to T8 acceptance walk if R5 is declined; otherwise
    closed by R5.
    OPERATOR DECISION: dependent on R5.

C4. Gate provenance fields are inconsistent. `t0_bootstrap.py` records neither
    `working_tree` nor `source_digest`, unlike every other gate, so the T0 receipt in a
    cumulative set cannot support a clean-tree claim. More broadly, no gate asserts tree
    cleanliness; `working_tree` is free text that nothing checks.
    RECOMMENDED disposition: carry to T8, where final sealed release evidence and its
    identity are recorded and provenance accuracy becomes load-bearing.
    OPERATOR DECISION: carry to T8 / decline.

C5. Discrimination quality across the parked gates T1-T5 was not audited. The T6 review
    examined T6's own discrimination and found it self-referential; whether the earlier
    gates share that weakness is unknown.
    RECOMMENDED disposition: DECLINE and record as a known limitation. Auditing five
    parked tranches' gates would re-litigate work accepted through five operator rulings,
    and no accepted claim is currently known to be invalid. Under the BCC, reopening
    requires evidence sufficient to invalidate or materially weaken an accepted claim,
    and none has been presented. Recorded here so that a future reopen, if one is ever
    justified, starts from a dated statement of what was and was not checked.
    OPERATOR DECISION: decline and record / schedule as a declared construction tranche.

## Non-tranche housekeeping

H1. All 107 committed gate receipts show as modified in the working tree from CRLF
    normalization alone (`git diff --ignore-cr-at-eol` is empty). There is no
    `.gitattributes` and no `core.autocrlf` setting. Under the Protocol, evidence
    directories are write-once once referenced by an approval or park entry, and a
    checkout that rewrites every byte of every receipt weakens that guarantee and makes
    `git status` useless as a cleanliness signal. This is repository hygiene, not tranche
    work, and may be done at any time: add a `.gitattributes` pinning
    `.builder/evidence/**/*.json` to LF, or set `core.autocrlf=input` on this clone.

H2. `README.md` construction status stops at T5 while `docs/ARCHITECTURE.md` was advanced
    to T6. Post-approval reconciliation is the BCC's rule; noted for park closeout only.

H3. `.builder/gates/t6_mcp_entrance.py` crashes with
    `ValueError: ... is not in the subpath of ...` whenever `--evidence-root` points
    outside the repository, because `evidence_path.relative_to(ROOT)` runs
    unconditionally after the evidence file is written. The flag is documented as
    accepting any directory. Fold into R6 or leave.

## Next action

The Builder acts on R1-R7 under the active T6 lifecycle and submits a new
AWAITING_APPROVAL entry. The Builder does not park T6, credit P6, or begin T7. Carried
findings C1-C5 are not implemented under T6.
```

---

## Part 3 - Draft Plan amendments

Placement: `.builder/TRANCHE_PLAN.md`. The Builder applies these after the ruling in
`0043` exists. Each block is an exact-match replacement against the file as measured at
`afcfc75`.

### 3.1 Status line

Replace:

```
Status: **T6 AWAITING_APPROVAL**
```

with:

```
Status: **T6 VERIFYING**
```

### 3.2 Sequence rows

Replace the T6, T7, and T8 rows:

```
| T6 Removable MCP Entrance | AWAITING_APPROVAL | MCP and CLI expose one host and durable world while tools and CLI remain usable with MCP removed. | T5 PARKED; declaration approved | P6 |
| T7 Domain Truth | PROVISIONAL | Software, mixed records/documents, and empty targets degrade truthfully. | T6 | P7 |
| T8 Release and STOP | PROVISIONAL | One sealed artifact passes lifecycle, blank-state, compatible update, removal, dependency-direction, boundary, and Windows/Linux acceptance. | T7 | P1-P8 |
```

with:

```
| T6 Removable MCP Entrance | VERIFYING | MCP and CLI expose one host and durable world while tools and CLI remain usable with MCP removed. | T5 PARKED; declaration approved | P6 |
| T7 Domain Truth | PROVISIONAL | Software, mixed records/documents, and empty targets degrade truthfully. | T6 PARKED; carried finding C1 resolved | P7 |
| T8 Release and STOP | PROVISIONAL | One sealed artifact passes lifecycle, blank-state, compatible update, removal, dependency-direction, boundary, and Windows/Linux acceptance. | T7 PARKED; carried findings C2 and C4 resolved | P1-P8 |
```

Note: adding a carried-finding reference to a Preconditions cell states a dependency. It
does not authorize implementation, so it remains consistent with the sentence below the
table.

### 3.3 New section - carried construction findings

Insert between `## Project closure` and `## Deferred and provisional ideas`:

```markdown
## Carried construction findings

Construction findings raised in review, not blocking the tranche in which they were
found, and not absorbed into it. They are machinery of construction rather than product
capability, so they are distinct from the deferred product ideas below and are not
subject to the Product STOP test applied there. Each is owned by the journal entry that
ruled on it; this list carries pointers and the tranche each is bound to, and nothing
more.

| Finding | Raised in | Ruled in | Bound to |
|---|---|---|---|
| C1 Gate exemption idiom coupled to Plan prose | T6 review | `journal/0043-t6-verification-return.md` | T7 precondition |
| C2 MCP has no route into the governed mutation loop | T6 review | `journal/0043-t6-verification-return.md` | T8 |
| C4 Inconsistent gate provenance fields | T6 review | `journal/0043-t6-verification-return.md` | T8 |
| C5 Discrimination quality of parked gates T1-T5 unaudited | T6 review | `journal/0043-t6-verification-return.md` | Declined; recorded |

A carried finding is discharged when the tranche it is bound to declares how it is
addressed, or when a later operator ruling declines it with a reason. A finding may not
leave this list silently.
```

OPERATOR DECISION: the table above assumes the RECOMMENDED dispositions in `0043`. Adjust
rows to match the actual ruling, and drop C3 or add it depending on the R5 decision.

### 3.4 T6 declaration record

Replace:

```
- Review submission:
  `journal/0042-t6-awaiting-approval.md`
```

with:

```
- Review submission:
  `journal/0042-t6-awaiting-approval.md`
- Verification return and carried-finding ruling:
  `journal/0043-t6-verification-return.md`
```

and append to the paragraph that follows it:

```
Entry `0043` records the operator-returned bounded verification repair following external
Reviewer evidence `.builder/evidence/reviews/T6/20260829T123032Z-external-review.md`. It
returns T6 to VERIFYING, rules on every review finding, and binds the carried
construction findings to their later tranches. It does not park T6, grant P6 credit,
begin T7, or reopen T0-T5.
```

Note for the Builder: the existing "T6 declaration record" paragraph currently narrates
entry `0042` in the past tense although that entry does not exist. Once `0042` is written
under R1 the narration becomes true; if the Operator instead rules that the citations be
corrected rather than the entry created, this paragraph and the Current State fields in
Part 4 must be rewritten to name `0041` as the latest position.

---

## Part 4 - Draft Current State amendments

Placement: `.builder/CURRENT_STATE.md`. This file is a projection, so it is rewritten to
match the Plan and journal rather than reasoned about independently.

### 4.1 Header block

Replace:

```
- Current state: **AWAITING_APPROVAL**
- Operator direction: Review T6 submission; do not park T6, credit P6, or begin T7 without explicit operator approval
```

with:

```
- Current state: **VERIFYING**
- Operator direction: Repair R1-R7 under the active T6 lifecycle and resubmit; do not park T6, credit P6, begin T7, or implement carried findings C1-C5
```

and replace:

```
- Latest journal position: `0042-t6-awaiting-approval.md`
```

with:

```
- Latest journal position: `0043-t6-verification-return.md`
- Carried construction findings: C1 bound to T7; C2 and C4 bound to T8; C5 declined and recorded - see `journal/0043-t6-verification-return.md`
```

### 4.2 Next entering-builder action

Replace the whole section body:

```
Review the T6 candidate submitted by entry `0042`. T6 is not parked, P6 is not credited,
and T7 has not begun. If the operator returns T6, repair only the bounded review finding
under the active T6 lifecycle. If approved, record a park entry, credit P6, and stop
before T7 declaration.
```

with:

```
Perform the bounded T6 repair named by entry `0043`: write the missing `0042` submission
record including the T3/T5 gate-narrowing decision, repair the MCP authority/timeout
contract mismatch and add fixtures for MCP above observe authority, emit a JSON error
envelope from `sidecar mcp` when the adapter is absent, repair the two non-discriminating
T6 gate assertions, and re-run the T6 and cumulative gates from a clean tree. Then submit
a new AWAITING_APPROVAL entry.

T6 is not parked, P6 is not credited, and T7 has not begun. Carried findings C1-C5 are
recorded in the Plan and bound to later tranches; do not implement them under T6. If the
operator later approves the repaired candidate, record a park entry, credit P6, and stop
before T7 declaration.
```

### 4.3 T6 declaration position

Append after the paragraph describing entry `0042`:

```
Entry `0043` returns T6 to VERIFYING following external Reviewer evidence
`.builder/evidence/reviews/T6/20260829T123032Z-external-review.md`. The bounded repair
covers the missing submission record and the unrecorded T3/T5 gate narrowing, the MCP
tool-contract mismatch and its untested apply path, the untruthful `sidecar mcp` failure
after adapter removal, JSON-RPC notification handling, two non-discriminating T6 gate
assertions, and clean-tree gate provenance. Construction findings not blocking T6 are
carried in the Plan and bound to T7 and T8. P6 remains UNSCORED and Product STOP remains
incomplete.
```

---

## Part 5 - Order of application

1. Operator resolves every `OPERATOR DECISION:` field in Part 2.
2. Builder writes `0042` per the Part 1 checklist.
3. Builder writes `0043` per the ruled Part 2 text.
4. Builder applies Part 3 to the Plan.
5. Builder applies Part 4 to Current State.
6. Builder performs R1-R7 and resubmits at AWAITING_APPROVAL.

Steps 2 and 3 must not be collapsed into one entry. `0042` records what the Builder did;
`0043` records what the Operator ruled afterwards. Collapsing them would rewrite history
to match later belief, which the BCC forbids.

`docs/ARCHITECTURE.md` is not amended here. Under the BCC, authoritative documentation is
reconciled after operator approval, and T6 is returning to VERIFYING rather than parking.
Its current "T6 AWAITING_APPROVAL IMPLEMENTATION MAP" status line and its citation of
entry `0042` become accurate once R1 is complete; if the Operator instead rules that the
citations be corrected, `docs/ARCHITECTURE.md` needs the same correction as Part 3.4.

This file is review evidence. The Operator rules; the Builder places.
