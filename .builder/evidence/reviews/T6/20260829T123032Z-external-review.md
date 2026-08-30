# External Review: T6 Removable MCP Entrance

Date: 2026-08-29T12:30:32Z
Reviewer: The Reviewer
Reviewed commit: `afcfc75c9d19c1a4bd8e7f0516e61aaca751710d` (branch `codex/t1-mechanical-host`)
Reviewed evidence: `.builder/journal/0040-t6-removable-mcp-entrance-declaration.md`;
`.builder/journal/0041-t6-execution-start.md`;
`.builder/evidence/T6/20260829T112223Z-d213f103/t6-gate.json` and the five cumulative
T5/T4/T3/T2/T1/T0 receipts named by the Plan; `product/core/mcp.py`,
`product/core/host.py`, `product/core/cli.py`, `product/core/control.py`;
`tests/test_t6_mcp_entrance.py`; `.builder/gates/t6_mcp_entrance.py` and the T3/T5 gate
changes in `afcfc75`; independent re-run of all seven gates and canonical pytest on a
clean off-repository copy; live adversarial probes against an installed instance.

## Disposition

RETURN TO VERIFYING

## Executive Finding

The T6 implementation is substantively sound and reproduces independently. `product/core/mcp.py`
is a genuine adapter: it owns no tables, launches no tools, and routes every operation
through `registry`, `ControlPlane`, and the existing state owners. `product/core/host.py`
is a real shared owner consumed by both entrances rather than an MCP-private duplicate.
Removability is implemented correctly (lazy import, behavioral fixture), the host boundary
holds through MCP (containment refusal, authority refusal, receipted denials), and the
catalog is projected live from manifests rather than hard-coded. I reproduced all seven
gates at PASS on a second platform.

I nevertheless recommend RETURN TO VERIFYING for two record-keeping blockers and three
bounded implementation repairs. The blockers are that the submission's own journal entry
does not exist, and that two parked tranches' gates were narrowed with no construction
record. The repairs concern the one MCP behavior the tranche never witnessed — mutating
the target through the entrance — plus a crash and a protocol defect on paths adjacent to
the declared outcome. None of these reopens T0-T5 or contradicts the declared T6 scope.

## Findings

- [BLOCKER] The T6 awaiting-approval journal entry does not exist.
  `.builder/journal/0042-t6-awaiting-approval.md` is absent from the working tree and
  from all of git history (`git log --all --diff-filter=A -- '.builder/journal/0042*'`
  returns nothing). The last entry is `0041-t6-execution-start.md`. Three documents cite
  the missing entry as the authority for the submission: `TRANCHE_PLAN.md`
  ("Review submission: `journal/0042-t6-awaiting-approval.md`"; "Entry `0042` records the
  implemented review candidate, including the T6 gate receipt ..."), `CURRENT_STATE.md`
  ("Latest journal position: `0042-t6-awaiting-approval.md`"; "Review the T6 candidate
  submitted by entry `0042`"), and `docs/ARCHITECTURE.md` ("Authoritative T6 review
  evidence is recorded by journal entry `0042`"). The submitted gate receipt contradicts
  them on its face: check `journal_continuity` in
  `.builder/evidence/T6/20260829T112223Z-d213f103/t6-gate.json` reads "journal is
  contiguous through 0041-t6-execution-start.md". Under `TRANCHE_PROTOCOL.md`, REVIEW is
  realized by "a numbered awaiting-approval entry"; T6 therefore has no submission record,
  and the Plan's status ledger rests on a citation to nothing.
  Evidence: `.builder/journal/` listing; `git log --all --diff-filter=A`; commit
  `afcfc75` file list (Plan, Current State, Architecture, evidence, gates — no journal
  entry); T6 receipt `20260829T112223Z-d213f103` check `journal_continuity`.
  Required action: the builder creates the `0042` awaiting-approval entry recording what
  was believed, attempted, and changed, the gate receipts relied on, the T3/T5 gate
  narrowing decision and its bound, and the open risks; or the operator rules that the
  Plan, Current State, and Architecture citations be corrected instead. T6 should not be
  parked and P6 should not be credited while the submission record is missing.

- [BLOCKER] Two parked tranches' gates were narrowed with no construction record.
  Commit `afcfc75` modified `.builder/gates/t3_epistemic_substrate.py` and
  `.builder/gates/t5_governed_mutation.py` to exempt the term `mcp` in
  `product/core/cli.py` (T3) and in `product/core/cli.py` plus `product/core/mcp.py`
  (T5). T3 and T5 are PARKED with P3 and P5 credited. Under the BCC, `.builder/gates/` is
  the only gate authority and construction history is owned by `.builder/journal/`;
  relaxing a parked tranche's closure gate touches an accepted claim and belongs in an
  immutable entry with its justification and bound. The only trace is one sentence in
  `docs/ARCHITECTURE.md`, which is an implementation map, not construction history. This
  finding is inseparable from the first: the entry that should have recorded the decision
  is the entry that is missing.
  Evidence: `git show afcfc75 -- .builder/gates/t3_epistemic_substrate.py
  .builder/gates/t5_governed_mutation.py`; `.builder/journal/` listing;
  `docs/ARCHITECTURE.md` "T6 review evidence" section.
  Required action: record the narrowing in the `0042` entry (or a companion amendment)
  with the reasoning, the exact surfaces exempted, and why the exemption does not weaken
  the parked T3/T5 outcomes. The change itself appears correctly bounded; the objection is
  to its absence from history, not to its content.

- [RETURN] MCP advertises a tool contract it does not accept, and its only mutating path
  is untested.
  `mcp._tool_descriptors` projects each manifest's `input_schema` verbatim as
  `inputSchema`; for `write_file` that schema carries `"additionalProperties": false` and
  declares no `_authority` or `_timeout`. `mcp._call_manifest_tool` then pops `_authority`
  (defaulting to `observe`) and `_timeout` out of the same arguments object. Measured
  against an installed instance: a schema-conforming `tool.write_file` call is refused
  `authority_denied`; the identical call carrying `"_authority": "apply"` — an argument the
  advertised schema forbids — succeeds, creates the target file, and records
  `client: "mcp"`, `authority: "apply"`, `durably_governed: true` with receipt and
  artifact identifiers. So a conformant client can never reach apply authority, and a
  client that does reach it must violate the catalog the server published. No product
  fixture and no gate assertion exercises MCP above `observe`; declared completion
  evidence item 3 covers only "an observe tool". The most consequential behavior of this
  entrance — an agent mutating the operator's target through MCP — ships unwitnessed. The
  `0040` declaration named this exact risk ("making MCP names a second tool contract").
  Evidence: `product/core/mcp.py:104-107` (schema projection), `:146-156`
  (`_call_manifest_tool`); live probe results recorded in this review; absence of any
  `_authority` or `apply` term in `tests/test_t6_mcp_entrance.py`.
  Required action: carry authority and timeout in the MCP call envelope (or declare them
  in the projected schema) so the advertised contract matches the accepted one, and add a
  fixture covering MCP apply-authority write, its refusal path, and its receipt.

- [RETURN] `sidecar mcp` crashes with an unhandled traceback once the adapter is removed.
  Measured: after deleting `.sidecar/core/mcp.py` from an installed instance,
  `sidecar status`, `sidecar tools`, and `sidecar receipts list` all succeed with normal
  JSON (requirement 6 holds), but `sidecar mcp` exits 1 with empty stdout and a
  `ModuleNotFoundError` traceback on stderr. Every other CLI path emits a JSON envelope;
  declared completion evidence item 8 requires truthful failure. The removability story is
  otherwise clean, and this is a few lines.
  Evidence: live probe (`A1_mcp_subcommand_after_removal`); `product/core/cli.py:161`.
  Required action: catch the import failure and emit the standard JSON error envelope
  stating that the MCP adapter is not installed; add the assertion to
  `test_cli_survives_when_mcp_adapter_is_removed`.

- [RETURN] The JSON-RPC loop answers notifications and rejects MCP's own initialization
  notification.
  Measured: sending `{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}`
  — a notification, no `id` — returns
  `{"jsonrpc":"2.0","id":null,"error":{"code":-32601,"message":"unknown method:
  notifications/initialized"}}`. JSON-RPC 2.0 forbids replying to a notification, and
  `notifications/initialized` is a required step of the MCP lifecycle, so the first
  message a conformant MCP client sends after `initialize` draws a protocol violation. No
  evidence in this tranche shows any MCP client completing a handshake; the fixtures drive
  the loop with the project's own request shapes only. Entry `0040` does permit "the small
  JSON-RPC-over-stdio subset needed for these tests", and this satisfies that sentence
  literally — but the tranche name, the Plan's outcome column, and P6 all say MCP, and
  what is proven is that the loop answers this repository's fixture.
  Evidence: `product/core/mcp.py:40-52` (`_handle_line` always writes a response),
  `:66-74` (`_dispatch` method table); live probe (`A2_notification_reply`).
  Required action: suppress the response for id-less requests and accept (ignore)
  `notifications/initialized`, then add one fixture that completes an
  `initialize` -> `notifications/initialized` -> `tools/list` handshake. If the operator
  prefers to defer client conformance to T8's acceptance walk, the park record should say
  plainly that the entrance is JSON-RPC-shaped and not yet MCP-client-verified.

- [ADVISORY] The gate's two removability assertions do not discriminate; only the fixture
  does.
  `_t6_surfaces` and `_mcp_import_violations` both judge `cli.py` by
  `cli.split("def _parser", 1)[0]` — the text above the parser function. Measured: appending
  `from . import mcp as _eager_mcp` to the bottom of `cli.py` (module scope, therefore
  eager) leaves both checks reporting PASS, including the detail string "CLI is the only
  non-MCP product module allowed to mention the MCP adapter". The mutation genuinely
  breaks removability — with `mcp.py` deleted, `status`, `tools`, and `receipts list` all
  die with `ImportError`. The gate as a whole still FAILs, because
  `test_cli_survives_when_mcp_adapter_is_removed` catches it. Closure is therefore not
  breached; the objection is that the two checks named for removability report a property
  they do not verify, against the BCC's requirement that assertions discriminate against
  plausible wrong implementations.
  Evidence: `.builder/gates/t6_mcp_entrance.py:63-78`, `:124-142`; adversarial mutation
  run recorded in this review.
  Required action: none for closure. Recommend detecting module-level imports in `cli.py`
  by AST (the gate already parses imports for every other module) rather than by text
  slice.

- [ADVISORY] `_discrimination_witness` is largely self-referential.
  Five of its seven mutations rewrite the *text* of `tests/test_t6_mcp_entrance.py` or
  `product/core/mcp.py` in memory and then assert that a substring predicate over that
  text complains. "missing removability witness" replaces `mcp_source.unlink()` with
  `pass` and asserts a grep for `"mcp_source.unlink()"` fails; "missing malformed request
  witness" greps for `-32700`; "missing no automatic memory witness" greps for
  `'journal["entries"], []'`. Nothing is executed and no behavior is measured. Under the
  BCC, "a tool's report of its own mutation is not measurement." This is the weakest
  discrimination pass in the series: T1 injected real module mutations and re-ran, T2 used
  SQLite trigger failure injection, T4 carried a behavioral basis/freshness witness.
  Evidence: `.builder/gates/t6_mcp_entrance.py:220-314`.
  Required action: none for closure. Recommend at least one discrimination that runs the
  mutated system — for example remove `mcp.py` and assert the removability fixture fails,
  or stub `ControlPlane.invoke` and assert the routing fixture fails.

- [ADVISORY] Parked-gate strictness is coupled to editable Plan prose.
  Both narrowed gates derive their exemption from
  `"T6 Removable MCP Entrance | PROVISIONAL" not in plan`, read out of
  `.builder/TRANCHE_PLAN.md`. Measured: with product source untouched, editing that one
  Plan cell back to `PROVISIONAL` flips `t3._no_t4_or_out_of_scope_surfaces` and
  `t5._no_out_of_scope_surfaces` from PASS to FAIL. Because the test is negative, it also
  fails open under any table reformat or tranche rename. A builder can thus relax two
  parked tranches' boundaries by editing a status document. The idiom pre-dates T6
  (`t4_has_started` in the same T3 gate) and was accepted through T4 and T5, so this is an
  inherited pattern that T6 extended rather than introduced.
  Evidence: `.builder/gates/t3_epistemic_substrate.py:210-227`;
  `.builder/gates/t5_governed_mutation.py:227-250`; Plan-mutation run recorded in this
  review.
  Required action: none for closure. Recommend expressing the exemption as an explicit
  allowlist constant in the gate, commented with the tranche that introduced it, rather
  than deriving it from a mutable authority document.

- [ADVISORY] The authoritative T6 receipt and five of six cumulative receipts record a
  dirty working tree.
  All six carry `head_commit 3c3e394` with `working_tree` listing
  `M .builder/gates/t3_epistemic_substrate.py` and `M .builder/gates/t5_governed_mutation.py`
  plus untracked evidence directories. The T3 and T5 PASS results supporting this
  submission were therefore produced by gate code that was in no commit at the time, and
  the receipts' `head_commit` does not describe the measured state. The receipts disclose
  this honestly in their own `working_tree` field, and I confirmed the results are
  faithful by re-running every gate from a clean copy at `afcfc75` (see Independent
  Measurement). Prior tranches' narratives claimed clean-commit runs; no gate actually
  asserts tree cleanliness, so this is a systemic evidence weakness that T6 is the first
  to exercise in tranche-relevant files.
  Evidence: `working_tree` fields of `20260829T112223Z-d213f103`, `20260829T112333Z-7a06a488`,
  `20260829T112500Z-731d6bb1`, `20260829T112612Z-c40cb33e`, `20260829T112721Z-c9a3a230`,
  `20260829T112842Z-bf459e22`.
  Required action: none, given independent reproduction. Recommend re-running the
  authoritative T6 and cumulative gates from clean `afcfc75` and citing those receipts in
  the `0042` entry, and consider a gate check that records tree cleanliness as an
  explicit PASS/UNSCORED assertion rather than a free-text field.

- [INFORMATIONAL] MCP exposes the ungoverned immediate-write route and no route into the
  T5 governed mutation loop.
  Measured: after a successful MCP `tool.write_file` apply, `mutation_previews`,
  `mutation_approvals`, `mutation_records`, `mutation_verifications`, and `mutation_links`
  all remain 0. The MCP catalog carries `mutation.status`, `mutation.history`, and
  `mutation.links` (read-only) but no `preview-write`, `approve`, or `apply`, and no
  `journal.add`. This is within the scope `0040` declared. It is still worth an explicit
  operator decision: P5 credit rests on preview -> approval -> stale refusal -> measured
  mutation -> honest verification, and the entrance built for agents can reach only the
  path around that loop.
  Evidence: live probe (`mutation_counts` after MCP apply; `mcp_catalog_names`).
  Required action: none for T6. Recommend the operator record whether this is accepted for
  the prototype or scheduled for T7/T8, rather than leaving it implied.

- [INFORMATIONAL] `_timeout` is unvalidated and internal exception text reaches the client.
  `int(tool_arguments.pop("_timeout", 30))` raises `ValueError` for a non-numeric value,
  which the generic handler formats as
  `-32000 "ValueError: invalid literal for int() with base 10: 'abc'"`. Invalid params
  should be `-32602`, and the catch-all formats arbitrary exception text — which can carry
  host filesystem paths — into the response.
  Evidence: `product/core/mcp.py:50-51`, `:149`; live probe (`bad_timeout`).
  Required action: none for T6 closure; fold into a later hardening pass.

- [INFORMATIONAL] `t0_bootstrap.py` records no `working_tree` or `source_digest`.
  Every other gate records both. The T0 receipt in the cumulative set therefore cannot
  support a clean-tree claim; a scan that shows T0 as "clean" is reading an absent field,
  not evidence.
  Evidence: `.builder/gates/t0_bootstrap.py:479` versus the equivalent block in
  `t1`-`t6`; keys of `.builder/evidence/T0/20260829T112820Z-1afe077d/bootstrap-gate.json`.
  Required action: none for T6.

- [INFORMATIONAL] Committed evidence receipts are being rewritten in place by the working
  environment.
  All 107 committed gate receipts show as modified in the working tree
  (`107 files changed, 7865 insertions(+), 7865 deletions(-)`). The difference is entirely
  line endings: `git diff --ignore-cr-at-eol` is empty, the working copies carry CR and
  the committed blobs do not, and there is no `.gitattributes` and no `core.autocrlf`
  setting. Under the Protocol, evidence directories are write-once once referenced by an
  approval or park entry; a checkout that rewrites every byte of every receipt weakens
  that guarantee and makes `git status` useless as a cleanliness signal — which is part of
  how the dirty-tree receipts above went unnoticed.
  Evidence: `git diff --shortstat`; `git diff --ignore-cr-at-eol --shortstat`;
  CR counts of working file versus `git show HEAD:` blob.
  Required action: none for T6 closure. Recommend a `.gitattributes` pinning
  `.builder/evidence/**/*.json` to LF, or `core.autocrlf=input` on this clone.

- [INFORMATIONAL] `README.md` still stops at T5 while `docs/ARCHITECTURE.md` was advanced
  to "T6 AWAITING_APPROVAL IMPLEMENTATION MAP" in `afcfc75`. Post-approval reconciliation
  is the BCC's rule, so a stale README at AWAITING_APPROVAL is expected; noted only for
  the park closeout checklist.
  Required action: none now.

## Boundary Checks

- Confirmed: `product/core/mcp.py` imports no `sqlite3`, no `subprocess`, and no tool
  module; every operation routes through `registry.discover`, `ControlPlane(context).invoke`,
  or an owning module (`runtime_records`, `app_journal`, `substrate`, `awareness`,
  `mutation`, `host`).
- Confirmed: `product/core/host.py` is a genuine shared owner. `cli.py` deleted its private
  `_status` and now calls `host.status`, and MCP calls the same function. This is the right
  shape and not an MCP-private duplicate.
- Confirmed: no product module imports MCP. `cli.py` imports it lazily inside the `mcp`
  subcommand branch, verified by AST across `product/**` and by the removal fixture.
- Confirmed: MCP does not own capabilities. Catalog entries `tool.<id>` are projected from
  live manifests — the fixture mutates a manifest description and MCP reports the mutated
  text.
- Confirmed: the host boundary holds through MCP. `../../../../etc/passwd` is refused with
  `containment_refusal`; `_authority: "root"` is refused with `invalid_authority`; an
  authority denial still records a governed receipt with `durably_governed: true`.
- Confirmed: attribution reaches durable state. An MCP-originated receipt is visible from
  the CLI with `client: "mcp"`. Caveat: CLI `--client` is caller-settable (pre-existing
  from T2), so `client` is an asserted field, not a host-derived one; MCP hard-codes it.
- Confirmed: no automatic memory. `initialize` and `tools/list` create no App Journal
  entries, no substrate resources, no mutation records, and no `.sidecar/state/mcp.sqlite3`.
- Confirmed behaviorally, beyond the gate's text checks: malformed `{not json` and
  `unknown/method` wrote no durable state (2 receipts before, 2 after).
- Confirmed: `product/**` imports nothing from `factory`, `tests`, or `.builder`
  (31 modules scanned).
- Confirmed: T6 introduces no GUI, AI/vector, cartridge, rollback, planner, or
  workflow-engine surface; no new mechanical tools; no widening of the T5 mutation surface;
  no release/update/removal lifecycle.
- Confirmed: `_projectmapper/` remains covered by the root-scoped ignore rule and is
  excluded from the T6 hygiene check, consistent with the operator's transient-output
  ruling. Its SQLite snapshot is still present.
- Confirmed: T0-T5 remain PARKED, P1-P5 remain credited, P6-P8 remain UNSCORED, Product
  STOP remains incomplete, and T7 has not begun.

## Independent Measurement

I copied the repository to an off-repository working root, restored the committed byte
content of `.builder/evidence` (removing the CRLF churn), and re-ran everything at
`afcfc75` on Linux with Python 3.13.15, pytest 8.4.2, and Ruff 0.15.22 — a second platform
and toolchain, since every receipt in the repository was produced on
Windows-10 / CPython 3.13.6.

- `python -m pytest -q`: 54 passed.
- T6 gate: PASS 11/11, clean tree, at `afcfc75`.
- T5 gate: PASS 13/13. T4: PASS 14/14. T3: PASS 12/12. T2: PASS 13/13. T1: PASS 9/9.
  T0: PASS 13/13.

All seven gates reproduce. The narrowed T3 and T5 gates pass with the committed narrowing,
so the dirty-tree receipts above record a real result recorded against a misleading commit
reference, not a falsified one.

Adversarial probes run against a freshly attached instance are cited inline in the Findings
above: notification handling, projected-schema versus accepted-argument mismatch,
apply-authority write through MCP, malformed-request durability, path escape, bogus
authority, unknown manifest tool, `sidecar mcp` after adapter removal, eager-import
mutation of `cli.py`, and the Plan-prose coupling of the T3/T5 exemptions.

One incidental defect found while doing this: `t6_mcp_entrance.py --evidence-root` crashes
with `ValueError: ... is not in the subpath of ...` at line 411 whenever the evidence root
is outside the repository, because `evidence_path.relative_to(ROOT)` runs unconditionally
after the evidence file is written. The flag is documented as accepting any directory.

## Requirement Matrix

Against the ten completion-evidence items declared in `0040`:

1. Fresh attach has no inherited MCP state; CLI works before MCP is used — PASS.
   `test_no_mcp_state_or_automatic_memory_is_created_by_listing`;
   `test_cli_survives_when_mcp_adapter_is_removed`.
2. `initialize`/tool discovery returns a projected catalog, not a hard-coded one — PASS.
   `test_mcp_initializes_and_projects_live_manifest_catalog` mutates a live manifest
   description and asserts MCP reports it. Genuine discriminator.
3. MCP tool call routes through `ControlPlane` and creates the same receipt/artifact as
   CLI — PASS for observe authority; UNSCORED for `sandbox` and `apply`. See the
   contract-mismatch finding: the apply path works but is unwitnessed and is unreachable
   for a schema-conforming client.
4. MCP read/list operations go through owning APIs — PASS.
   `test_mcp_reads_existing_world_through_owner_surfaces` plus source inspection of
   `_call_projection`.
5. MCP and CLI inspect the same durable world across restart/re-entry — PASS. Each
   `sidecar` invocation and each MCP session is a separate process against the same
   instance; the receipt written through MCP is read back through CLI.
6. Removing the adapter leaves CLI, host, registry, and mechanical tools usable — PASS for
   `status`, `call`, and `receipts list`. Partial: the `mcp` subcommand itself then
   crashes untruthfully.
7. Lower layers do not import MCP; product does not import construction/tests/factory —
   PASS on substance (AST scan across `product/**`, plus the removal fixture). The
   `cli.py`-specific check does not discriminate; see the advisory.
8. Malformed or unknown requests fail truthfully without misleading durable state — PASS,
   and I confirmed the durability half behaviorally rather than by grep. Adjacent gap:
   id-less notifications are answered.
9. No out-of-scope surfaces — PASS.
10. Canonical pytest, Ruff, `git diff --check`, T6 gate, and cumulative T5-T0 gates pass —
    PASS, reproduced independently. Provenance qualified by the dirty-tree advisory.

Against the seven wrong implementations named in the `0040` discrimination plan: the
hard-coded catalog, control-plane bypass, MCP-private state ownership, CLI-import, and
automatic-memory cases are genuinely rejected by the product fixtures. The gate's own
discrimination witnesses do not independently establish any of them (see advisory). The
"CLI importing MCP" case is rejected only by the fixture, not by the check named for it.

Against Charter P6: the "same host catalog, authority, substrate, awareness, receipts, and
App Journal rather than parallel implementations" half is well supported. The "removing MCP
leaves CLI, host, and mechanical capabilities usable" half is supported. P6 credit should
nevertheless wait on the submission record and on a decision about the unwitnessed MCP
mutation path and the unverified client handshake.

## Recommendation

Return T6 to VERIFYING for a bounded repair confined to the active T6 lifecycle:

1. Create the `0042` awaiting-approval entry, including the T3/T5 gate-narrowing decision
   and its justification.
2. Repair the MCP authority/timeout contract mismatch and add a fixture for the MCP
   apply-authority write, its refusal, and its receipt.
3. Emit a JSON error envelope from `sidecar mcp` when the adapter is absent.
4. Stop replying to id-less requests and accept `notifications/initialized`, with one
   handshake fixture — or record explicitly in the park entry that client conformance is
   deferred to T8.
5. Re-run the T6 and cumulative gates from a clean tree and cite those receipts.

Items 6-13 in Findings are advisory and informational; they do not require action before
approval. This review is evidence, not a ruling. The operator grants approval, PARKED
status, and P6 credit; T0-T5 remain parked and untouched by this review.
