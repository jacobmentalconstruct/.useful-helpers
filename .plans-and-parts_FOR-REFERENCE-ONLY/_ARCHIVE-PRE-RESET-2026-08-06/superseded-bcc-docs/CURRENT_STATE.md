# Current State

Last updated: 2026-08-05, at the close of Tranche 1.

This document is the entry point for any agent or human resuming this project.
It is authoritative. Nothing under `.plans-and-parts_FOR-REFERENCE-ONLY/`,
`_design/`, or `_harness/` describes the state of this project.

---

## 1. One-Paragraph Summary

Useful Helpers Workbench has **no runtime code**. `src/` does not exist. Tranche
0 converted a copied sandbox into a truthful project starting point by
installing the builder contract for this root and creating the active control
documents. Tranche 1 audited the twelve inherited tool contracts and the
99-tool toolkit, and produced `CAPABILITY_MATRIX.md`, which decides ownership
for every planned capability. The central architectural question is answered.
No application code has been written, by deliberate instruction.

---

## 2. What Physically Exists

| Path | State |
| --- | --- |
| `.bcc/BUILDER-CONSTRAINT-CONTRACT.md` | Installed for this root; placeholders resolved |
| `.bcc/CURRENT_STATE.md` | This file |
| `.bcc/PROJECT_PLAN.md` | Created, Tranche 0 |
| `.bcc/ARCHITECTURE.md` | Created, Tranche 1 |
| `.bcc/CAPABILITY_MATRIX.md` | Created, Tranche 1 |
| `.bcc/SOURCE_PROVENANCE.md` | Created, Tranche 0 |
| `.bcc/TESTING.md` | Created, Tranche 0 |
| `_docs/AppJOURNAL/0001-*.md` | Active journal, entry 0001 |
| `.gitignore` | Created, Tranche 0 |
| `toolkit/` | Inherited, unmodified, 99 tools |
| `.plans-and-parts_FOR-REFERENCE-ONLY/` | Inherited reference, unmodified |
| `_design/`, `_harness/` | Inherited reference, unmodified |
| `src/` | **Does not exist** |
| `tests/` | **Does not exist** |
| `config/`, `assets/`, `scripts/`, `docs/` | **Do not exist** |
| `pyproject.toml`, `README.md`, `run.bat` | **Do not exist** |

No file in this repository outside `toolkit/` contains executable application
code written for this project.

---

## 3. Verification Standing

**Nothing has been executed.** The isolated Linux environment failed to start
throughout Tranche 0 and Tranche 1, and no Windows shell was available. All
findings about the toolkit were obtained by reading source.

Under BCC 2.7, every behavioral claim about the toolkit is **provisional**.
There are no test results. There is no smoke check. There is no baseline.

Historical test counts appearing anywhere in the inherited material are not
verification of this project and must never be reported as such.

---

## 4. Decisions Made and Locked

1. **Builder memory home.** The active journal is `_docs/AppJOURNAL/`, an
   explicit operator choice permitted by the BCC bootstrap rule. `.bcc/` holds
   contract, planning, state, provenance, testing, and the capability matrix.
   `_docs/` (underscore) is builder-control; a future `docs/` without the
   underscore is product-facing. Both are non-runtime.
2. **No toolkit fork for root binding.** The toolkit already accepts a target
   root via `SUITE_PROJECT_ROOT`, applied per invocation. See
   `CAPABILITY_MATRIX.md` §2.1.
3. **One dispatcher, owned by the workbench.** The toolkit seam is a backend
   transport reached only through `ToolkitBridge`.
4. **Envelope.** The workbench normalizes to its own `OperationResult`.
   Translation happens once, at the bridge. The toolkit is not modified.
5. **Authority ladder.** Four levels (`Observe`/`Prepare`/`Apply`/`External`)
   mapped onto the toolkit's three. `External` has no toolkit equivalent and is
   gated by a workbench allowlist.
6. **No heavy runtime mechanics.** No graph engine, no message bus, no event
   sourcing. The blueprint does not earn them.

---

## 5. Known Risks Carried Forward

| Risk | Severity | Disposition |
| --- | --- | --- |
| All toolkit findings unexecuted | High | Mandatory safety gate before Tranche 6 (`CAPABILITY_MATRIX.md` §7) |
| `toolkit/.suite_sidecar` makes the toolkit target this repository by default | High | Bridge must always bind the root explicitly |
| Toolkit falls back silently on an invalid `SUITE_PROJECT_ROOT` | High | Bridge validates the root and verifies the echoed root |
| Toolkit seam has no cancellation and no progress streaming | High | Workbench owns the task queue; may require a seam-bypassing launcher |
| 120 s hardcoded timeout may be too short for snapshot compiles | Medium | Resolve in Tranche 5 |
| Unparseable tool output is treated as success | Medium | Bridge treats it as failure |
| Precept guard walks the whole target twice per Observe call | Medium | Measure before Tranche 6 |
| Raw stderr may leak absolute host paths into the UI | Medium | Redaction at the bridge |
| Contract-era "91 tools" vs actual 99 | Low | Contract-era toolkit statements are dated evidence |

---

## 6. Next Tranche

**Tranche 2 — Minimal Runtime Scaffold.**

Create a runnable, testable workbench package with no product functionality
beyond startup: `src/app.py`, package structure, logging, path and configuration
providers, state-root resolution, a `--status` smoke mode, test configuration,
run/setup scripts, and a root README.

Completion: package imports; status smoke passes; tests run from the root; no
runtime module imports a reference source; no runtime state is checked in.

**Before Tranche 6**, the safety gate in `CAPABILITY_MATRIX.md` §7 must be
executed. It does not block Tranches 2–5.

### Restart guidance

A resuming agent should read, in order: `.bcc/BUILDER-CONSTRAINT-CONTRACT.md`
(anchors `BCC-CONTEXT-ENTRY` and `BCC-WORKFLOW-REQUIRED-TRANCHE-LOOP`), this
file, `PROJECT_PLAN.md`, `ARCHITECTURE.md`, `CAPABILITY_MATRIX.md`, and the
latest entry in `_docs/AppJOURNAL/`.

It should not read predecessor journals to determine current state.
