# ProjectMapper Workbench Completion and Tranche Plan

Status: Active governing plan

Contract authority: `_docs/BCC.md` configured with `SIDECAR_ROOT=".project-mapper"`

Date: 2026-08-02

This plan defines the expected completion state and tranche path for turning
ProjectMapper into the front door for a broader Project Workbench. This
project-local copy is the governing delivery plan for `.project-mapper`.

---

## 1. Project Identity

Working project root:

`/.project-mapper/`

Working product name:

`Project Workbench`

Initial application identity:

`ProjectMapper Workbench`

Reference sources:

- `_PARTS-FOR-PLANS/_ProjectMAPPER/`
- `_PARTS-FOR-PLANS/_TokenizingPATCHER/`
- `_PARTS-FOR-PLANS/_LineNUMBERIZER/`
- `_PARTS-FOR-PLANS/_GitPUSHER/`

Reference sources may inform implementation, but they must not become runtime
dependencies. Any borrowed behavior must be re-homed, owned, cleaned, and
documented when meaningful.

---

## 2. Completion State

The project may be considered complete when it is a self-contained desktop
application that lets the user open a project folder, inspect and select
project files through an explorer-style interface, and run the approved project
operations against the selected project context.

### 2.1 Required User Outcome

At completion, the user can:

- launch the app from the `.project-mapper` project root,
- choose or reopen a project folder,
- see a left folder tree with persistent check/toggle state,
- click a folder and see a right-pane listing of that folder's immediate
  contents with useful file metadata,
- click a text file and preview its contents,
- click a binary or unsupported file and see clear metadata plus unavailable
  preview status,
- build a selected working set by checking files and folders,
- run snapshot, file dump, file tree, and SQL/project-map operations from a
  normal top menu structure,
- review operation outputs and errors clearly,
- find generated outputs in predictable project-local output folders,
- run tests or documented checks that verify the core behavior,
- inspect `_docs/` and the app journal to understand architecture, tranche
  history, decisions, risks, and next steps.

### 2.2 Required Application Shape

The app must provide:

- a conventional top menu bar: File, Edit, View, Tools, Window, Help,
- a stable left explorer pane for navigation and inclusion toggles,
- a right context pane that changes by selected item type,
- a status/log surface for operation progress and diagnostics,
- a project context model that separates navigation selection from operation
  inclusion state,
- project-local output handling,
- graceful handling for unreadable, too-large, binary, skipped, or excluded
  paths,
- vendorable packaging/run instructions.

### 2.3 Required Tooling Surface

The first completed version must support these operations:

- create SQLite project snapshot,
- export file tree,
- export file dump,
- export combined tree and dump,
- inspect or list generated outputs.

The following operations are explicitly later than the first mapper-workbench
completion unless pulled into scope by a documented tranche change:

- multi-file tokenizing patcher,
- line numberizer integration,
- git push/publish workflow.

### 2.4 Required Documentation State

The completed project must contain:

- `_docs/ARCHITECTURE.md`,
- `_docs/PROJECT_PLAN.md`,
- `_docs/_AppJOURNAL/` or `_docs/_journalDB/app_journal.sqlite3`,
- README with run/install/use instructions,
- SOURCE_PROVENANCE.md if reference logic is meaningfully borrowed,
- TESTING.md once test conventions become non-trivial,
- TOOLS.md once project-local tools become significant.

### 2.5 Required Quality Gates

Completion requires:

- no runtime dependency on the parts bin or sibling projects,
- clear UI/core/storage ownership boundaries,
- no large unowned monolith remaining as the primary architecture,
- snapshot outputs verified by schema/row-count checks or equivalent tests,
- folder tree and right-pane behavior manually smoke-tested,
- selected-set operation behavior tested or documented with residual risk,
- tranche closeout recorded in the app journal.

---

## 3. Architectural Doctrine

The application is an explorer-driven workbench, not a collection of separate
tool windows.

Core flow:

`project scan -> tree model -> browse selection -> inclusion set -> operation runner -> output artifact`

Clicking and checking are different:

- click selects the item to inspect in the right pane,
- check/toggle includes the item in the operation working set.

The explorer is persistent. Operations are isolated under top-menu commands and
act on the current project context and inclusion set.

Heavy runtime mechanics are not justified for the first completion target.
Use ordinary typed data flow, services, managers, and clear composition.

---

## 4. Proposed Scaffold

```text
.project-mapper/
  README.md
  LICENSE.md
  requirements.txt
  run.bat
  setup_env.bat
  assets/
  config/
  scripts/
  src/
    app.py
    ui/
    core/
    storage/
  tests/
  _docs/
    ARCHITECTURE.md
    PROJECT_PLAN.md
    _AppJOURNAL/
```

Suggested ownership:

- `src/app.py`: composition root only.
- `src/ui/`: Tkinter windows, panes, menus, widgets, view adapters.
- `src/core/`: project scanning, selection model, operation orchestration,
  export planning.
- `src/storage/`: SQLite snapshot writer/reader and schema helpers.
- `scripts/`: packaging and project-local operational helpers.
- `tests/`: tests for core selection, scan filtering, export/schema behavior.


## 4.1 Tranche Workflow

The operational workflow for every meaningful tranche is contract-required in `_docs/BCC.md` at anchor `BCC-WORKFLOW-REQUIRED-TRANCHE-LOOP`.

Do not duplicate the workflow here. Use the BCC anchor as the source of truth and treat `_docs/TRANCHE_WORKFLOW.md` as pointer-only. For portable reuse, export `../artifacts/BCC.md`; it retains the `{{BCC_...}}` placeholders that a first-copy agent must fill after asking the user where to place the side-car.

---

## 5. Tranche Plan

### Tranche 0: Root, Contract, and Baseline

Goal:

Create or declare `.project-mapper` as the project root and establish the
documentation/journal baseline.

In scope:

- create the project root scaffold,
- copy/adapt this plan into `_docs/PROJECT_PLAN.md`,
- copy or reference the BCC as the governing constraint contract,
- create `_docs/ARCHITECTURE.md` with initial doctrine,
- create the first app journal entry,
- identify current ProjectMapper reference files and provenance expectations,
- decide whether to port behavior from the single-file app or rebuild around
  the existing behavior.

Non-goals:

- no feature expansion,
- no patcher/line-numberizer/git integration,
- no broad cleanup of the parts bin.

Completion:

- `.project-mapper` exists and is the only write target for app code,
- docs and journal baseline exist,
- project can be opened by a future agent without guessing the direction.

### Tranche 1: Reference Audit and Architecture Map

Goal:

Understand the existing ProjectMapper behavior well enough to preserve it while
moving to owned components.

In scope:

- audit the current ProjectMapper single-file app,
- identify UI, scan, selection, export, SQLite, and vendor-export
  responsibilities,
- record borrowed or ported behavior in SOURCE_PROVENANCE if needed,
- define the initial component map,
- write tests for pure helpers where low-risk and useful.

Non-goals:

- no major UI redesign,
- no operation expansion,
- no patching tool work.

Completion:

- architecture map is documented,
- migration ownership is clear,
- risks and behavior-preservation notes are journaled.

### Tranche 2: Explorer Shell

Goal:

Build the front-door UI shell: menu bar, left tree, right context pane, status
surface.

In scope:

- top menu structure: File, Edit, View, Tools, Window, Help,
- choose/open project folder,
- scan folder into a tree model,
- left explorer tree with check/toggle state,
- right folder listing with name, type, size, modified date,
- right file preview for text files,
- metadata/unsupported view for binary or unreadable files,
- basic status/log reporting.

Non-goals:

- no final snapshot compiler rewrite,
- no patcher integration,
- no git integration.

Completion:

- user can browse a real project folder,
- click versus check behavior is clear,
- the app is usable as an explorer even before all operations are complete.

### Tranche 3: Selection Model and Filtering

Goal:

Make the inclusion set reliable enough for operations.

In scope:

- explicit project context model,
- persistent checked/unchecked/partial state for files and folders,
- exclusion defaults and user-visible skipped paths,
- selected working-set computation,
- large/binary/unreadable path classification,
- tests for inclusion/exclusion behavior.

Non-goals:

- no new export formats beyond mapper-required outputs,
- no multi-project workspace behavior.

Completion:

- operations can consume a deterministic selected working set,
- selection behavior is tested or otherwise inspectably verified.

### Tranche 4: Mapper Operations

Goal:

Restore and cleanly own the existing ProjectMapper outputs.

In scope:

- SQLite snapshot creation,
- schema ownership in storage layer,
- project tree export,
- file dump export,
- combined tree and file dump export,
- manifest/metadata output,
- output folder conventions,
- operation progress and error reporting,
- snapshot verification checks.

Non-goals:

- no multi-file patching,
- no line-numberizer UI,
- no git pushing.

Completion:

- the app can map a selected project as SQLite and Markdown outputs,
- generated outputs are predictable and inspectable,
- snapshot verification is documented and passing.

### Tranche 5: Hardening, Packaging, and First Completion Gate

Goal:

Bring the mapper workbench to its first contract-complete state.

In scope:

- manual smoke test checklist,
- automated tests for core scan/selection/export behavior,
- README run/install update,
- vendorable cleanup,
- package/export helper if still needed,
- documentation closeout,
- app journal tranche closeout.

Non-goals:

- no patcher/line-numberizer/git expansion unless first completion fails
  without them.

Completion:

- first ProjectMapper Workbench completion state is met,
- remaining tool integrations are documented as next-phase backlog.

### Tranche 6: Multi-File Patcher Integration

Goal:

Bring in tokenizing patcher behavior as an operation over the selected working
set.

In scope:

- audit TokenizingPATCHER reference app,
- define patch operation UX,
- preview multi-file patch plans,
- apply patches only after review,
- record patch evidence and errors,
- tests for patch planning and application boundaries.

Non-goals:

- no automatic agent patch generation unless separately justified,
- no hidden writes outside the selected project root.

Completion:

- selected files can be patched through a reviewable multi-file workflow.

### Tranche 7: Line Numberizer Polish

Goal:

Add line-numbered viewing/export polish where it strengthens inspection and
handoff.

In scope:

- audit LineNUMBERIZER reference app,
- add line-numbered file preview or export mode,
- optionally support strip/restore behavior only if needed,
- document where line numbers are view-only versus artifact output.

Non-goals:

- no broad editor implementation.

Completion:

- line-numbered inspection/export is available without confusing source file
  contents.

### Tranche 8: Git Push/Publish Workflow

Goal:

Add git project workflow once the workbench is stable.

In scope:

- audit GitPUSHER reference app,
- inspect git status,
- review selected or whole-project changes,
- stage/commit/push through explicit user actions,
- surface command output and failures,
- preserve safety around credentials/remotes.

Non-goals:

- no hidden auto-push,
- no destructive git reset/checkout flows without explicit approval.

Completion:

- user can safely move from project inspection to publish flow in one app.

---

## 6. Next Recommended Action

Start Tranche 2: explorer shell.

Do not add snapshot/export/pusher/pather functionality yet. Build the first UI
shell against the existing owned core contracts, preserving the distinction
between browse selection and operation inclusion state.

---

## 7. Current Park Point

As of BCC portability and handoff alignment closeout:

- the active local BCC exists at `.project-mapper/_docs/BCC.md`,
- the active local BCC is configured with `SIDECAR_ROOT=".project-mapper"`,
- the standalone export seed exists at `artifacts/BCC.md` with intentional
  `{{BCC_...}}` placeholders,
- `.project-mapper` exists as the side-car/project root for this workbench,
- `_docs/TRANCHE_WORKFLOW.md` is pointer-only and not authoritative,
- the current ProjectMapper reference source remains under the parts bin as a
  reference-only source,
- Tranche 0 setup is closed,
- Tranche 1 reference audit and architecture mapping is closed,
- the core foundation repair is closed with tests passing,
- current handoff state is summarized in `.project-mapper/_docs/CURRENT_STATE.md`,
- next feature work must begin with Tranche 2 explorer shell against owned core
  contracts.

Pickup checklist:

1. Read `_docs/BCC.md` anchors `BCC-SPINE`, `BCC-BOOTSTRAP-SIDECAR`, and
   `BCC-WORKFLOW-REQUIRED-TRANCHE-LOOP`.
2. Read `_docs/CURRENT_STATE.md`.
3. Declare Tranche 2 scope and non-goals in the app journal.
4. Implement only the explorer shell foundation.
