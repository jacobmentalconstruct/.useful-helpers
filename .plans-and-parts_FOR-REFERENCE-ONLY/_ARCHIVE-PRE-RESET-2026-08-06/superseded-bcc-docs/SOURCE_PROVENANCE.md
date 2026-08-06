# Source Provenance

Last updated: 2026-08-05.

This document distinguishes **inheritance** from **current implementation**.

---

## 1. Standing Statement

This project was seeded from copied material: conversion plans for twelve
predecessor applications, the original source of those applications, a completed
Useful Helpers toolkit, and the toolkit's historical design and harness records.

**No line of that material has been incorporated into a workbench runtime
module, because no workbench runtime module exists.**

As of this entry, provenance consists entirely of inheritance. There is no
borrowed logic to record.

---

## 2. Inherited Material

| Zone | Contents | Origin | Runtime standing |
| --- | --- | --- | --- |
| `.plans-and-parts_FOR-REFERENCE-ONLY/_PLANS/` | 12 tool contracts, review journals, adapter capability maps, and a recovered ProjectMapper-era plan set | Predecessor workbench project | Requirements evidence. Never imported. |
| `.plans-and-parts_FOR-REFERENCE-ONLY/_PARTS-FOR-PLANS/` | 12 original applications, 468 files | Various predecessor projects | Implementation evidence. Never imported. |
| `toolkit/` | 99-tool governed toolkit with a dispatch seam | Separately evolved toolkit project | Conditional, through an explicit bridge only. |
| `_design/` | Toolkit charter, plan, audits, capability gaps | Toolkit factory project | Historical evidence. Never imported. |
| `_harness/` | Toolkit acceptance harness and probes | Toolkit factory project | Historical evidence. Never imported. |

These materials were copied from projects whose histories do not share a common
chronology.

---

## 3. History Reconciliation

The following are **not** this project's history and are never to be presented
as such:

- Old dates. They remain historical dates belonging to their source projects.
- Old tranche numbers. The `Root Tranche 10`, `Root Tranche 14x`, and
  `Root Tranche 15` identifiers appearing throughout the inherited contracts
  belong to a predecessor project. This project's tranche numbering starts at 0
  and is defined solely in `PROJECT_PLAN.md`.
- Old status declarations. Several inherited contracts carry headers such as
  "backend implemented; GUI wiring pending". That describes a predecessor
  codebase. **In this project, no backend is implemented.**
- Old test totals. They are not baseline verification here.
- Old adapter files (`adapter-*.py`). They are semantic design evidence, not
  installed runtime modules. No adapter is installed.
- Old current-state documents. They are snapshots of predecessor work.
- Old journals. They are not copied into `_docs/AppJOURNAL/`. The active
  journal begins at entry `0001`.

The inherited contracts reference runtime paths such as
`src/useful_helpers/tools/<family>/adapter.py`. **Those paths do not exist in
this repository.** They describe a predecessor layout.

---

## 4. Dated Evidence

Recorded so it is not mistaken for current fact:

- The manifold-mcp and TheDISMANTLER contract reviews both state the toolkit has
  "91 tools under `tools/`". The current count is 99. The toolkit evolved after
  those reviews were written. Contract-era descriptions of the toolkit are
  dated evidence and must be re-verified against the toolkit as it now stands.

---

## 5. Borrowed Logic Register

Empty.

When a capability is recovered from reference source it must be recorded here
with: capability, source file and line, what was taken, why a bounded rewrite
was insufficient, the owning workbench module, and the tests that cover it.

Preference order, per the BCC: original implementation first; bounded rewrite
second; smallest viable borrowed unit last.

---

## 6. Hygiene Requirements

Checked-in source must contain no inherited personal paths, remote URLs, tokens,
runtime databases, or crash data. Reference material may contain all of these
and is therefore never packaged.

A path-scrub audit and a secret audit are required deliverables of Tranche 15.
