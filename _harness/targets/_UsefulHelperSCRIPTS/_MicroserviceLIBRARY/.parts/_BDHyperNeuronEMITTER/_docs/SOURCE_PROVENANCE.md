# Source Provenance — _BDHyperNeuronEMITTER

_Per Builder Constraint Contract §6.9 — provenance shall be recorded when logic is extracted, transplanted, or materially informed by reference sources._

---

## Provenance Table

| Destination | Source | Borrowed Unit | Reason | Treatment |
|---|---|---|---|---|
| `src/core/engine/training/bpe_trainer.py` | `_BDHyperNeuronEMITTER/src/engine/training/bpe_trainer.py` | Full module | Deterministic BPE greedy merge — rewrite would risk breaking reproducibility | Re-homed, import paths updated, print→logging, v2 docstrings |
| `src/core/engine/training/cooccurrence.py` | `_BDHyperNeuronEMITTER/src/engine/training/cooccurrence.py` | Full module | Sliding 1/distance weighting math — @HITL_PERMS protected | Re-homed, @HITL_PERMS preserved, v2 docstrings |
| `src/core/engine/training/npmi_matrix.py` | `_BDHyperNeuronEMITTER/src/engine/training/npmi_matrix.py` | Full module | NPMI = PMI / -log(P(a,b)) + InhibitEdge — @HITL_PERMS protected | Re-homed, @HITL_PERMS preserved, v2 docstrings |
| `src/core/engine/training/spectral.py` | `_BDHyperNeuronEMITTER/src/engine/training/spectral.py` | Full module | SVD sign canonicalization — @HITL_PERMS protected | Re-homed, @HITL_PERMS preserved, v2 docstrings |
| `src/core/engine/inference/provider.py` | `_BDHyperNeuronEMITTER/src/engine/inference/provider.py` | Full module | BPE encode + mean-pool embedding — exact algorithm must match training output | Re-homed, internal imports updated (`engine.*` → `core.engine.*`), print→logging |
| `src/core/engine/inference/hot_engine.py` | `_BDHyperNeuronEMITTER/src/engine/inference/hot_engine.py` | Full module | Physics equation `h_{t+1} = α·h_t + A·h_t - H·h_t` — must remain exact | Re-homed, v2 docstrings, math untouched |
| `src/core/engine/inference/retrieval.py` | `_BDHyperNeuronEMITTER/src/engine/inference/retrieval.py` | Full module | FTS5+ANN anchor strategies + inhibit pair derivation — tightly coupled to db schema | Re-homed, v2 docstrings |

---

## Why Borrowing Was Necessary (per §1 borrowing exception conditions)

All seven modules satisfy the full exception test:

1. **Cannot be feasibly rewritten without breaking correctness** — The training pipeline (BPE→cooccurrence→NPMI→SVD) is a mathematically specific pipeline where any step change breaks the downstream embedding arithmetic. The inference pipeline physics equation (`h_{t+1} = α·h_t + A·h_t - H·h_t`) must match exactly to maintain activation semantics.

2. **Functionally necessary** — The training modules produce the token embeddings consumed by inference. The inference modules are the entire query/reactor subsystem.

3. **Rewrite would materially risk breaking behavior** — The `@HITL_PERMS` markers explicitly record this for cooccurrence, npmi_matrix, and spectral. The BPE encode logic in provider.py must produce identical token IDs to those used during training.

4. **Can be re-homed into project root in compliance with this contract** — Done. All modules are in `src/core/engine/` under correct ownership.

5. **Provenance recorded** — This document.

6. **No lighter-weight extraction was sufficient** — The mathematical logic is holistic. Extracting partial functions would leave broken chains.

---

## Compliance Adjustments Applied

- All `print()` calls replaced with `logging` calls (§9.1)
- All module docstrings updated to v2 context with `V1 reference:` line identifying source (§8.4)
- Import paths updated from `engine.*` to `core.engine.*` to match v2 scaffold (§6.8)
- All `@HITL_PERMS` markers preserved verbatim — these are not documentation, they are mathematical protection guards
- No mathematical changes made to any borrowed module

---

## What Was NOT Borrowed

The following modules were written originally for v2 and have no v1 counterpart:

- `src/core/engine/training/__init__.py` — scaffold only
- `src/core/engine/inference/__init__.py` — scaffold only
- `src/core/contract/hyperhunk.py` — Emitter's enriched HyperHunk (Tranche 6, not yet written)
- `src/core/nucleus/` — Bootstrap Nucleus (Tranche 6, not yet written)
- `src/core/assembler/core.py` — Graph Assembler (Tranche 6, not yet written)
- `src/core/surveyor/hyperhunk.py` — Validation surface (Tranche 6, not yet written)
