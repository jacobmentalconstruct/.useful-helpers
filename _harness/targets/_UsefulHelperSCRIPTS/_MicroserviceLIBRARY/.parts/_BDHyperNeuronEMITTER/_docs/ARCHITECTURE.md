# _BDHyperNeuronEMITTER v2 — Architecture

## Domain

Consume richly-contextual HyperHunks from the v2 Splitter.
Evaluate pair-wise edge scores via the Bootstrap Nucleus (Phase 1: fixed weights).
Persist the resulting graph into the Cold Artifact (cold_anatomy.db).
Own the embedding math: BPE tokenizer, co-occurrence, NPMI, spectral.

## Non-domain

- No document splitting (that belongs to the Splitter)
- No graph traversal or ANN index (belongs to the query layer)
- No FFN Nucleus training (Phase 2 — deferred until Phase 1 training data exists)

## Builder Contract

See `builder_constraint_contract.md` in this folder.

---

## Project Structure (Builder Contract §2.1 compliant)

```
_BDHyperNeuronEMITTER/
  src/
    app.py                          <- composition root + CLI entry
    ui/
      __init__.py
      gui_main.py                   <- training / inspection GUI (Tkinter)
    core/
      __init__.py
      contract/
        __init__.py
        hyperhunk.py                <- v2 HyperHunk + Relational DSL extension
      engine/
        __init__.py
        training/
          __init__.py
          bpe_trainer.py            <- BPE tokenizer training
          cooccurrence.py           <- co-occurrence matrix construction
          npmi_matrix.py            <- NPMI weighting
          spectral.py               <- spectral decomposition / eigenvectors
        inference/
          __init__.py
          hot_engine.py             <- dual-state manifold neuron
          provider.py               <- embedding provider
          retrieval.py              <- subgraph retrieval
      assembler/
        __init__.py
        core.py                     <- HyperHunk → HyperNode assembly
      surveyor/
        __init__.py
        hyperhunk.py                <- HyperHunk validation / inspection
  _docs/
    ARCHITECTURE.md                 <- this file
    builder_constraint_contract.md
    _AppJOURNAL/                    <- builder memory surface
  requirements.txt
  setup_env.bat
  run.bat
  README.md
  LICENSE.md
```

---

## Composition Root (`src/app.py`)

`app.py` is the CLI entry point and composition root.

Modes:
- `emit`     — read HyperHunk NDJSON from stdin, build the Cold Artifact graph
               (BootstrapNucleus → GraphAssembler → cold_anatomy.db)
- `train`    — train BPE tokenizer + NPMI matrix + SVD embeddings on a corpus
               (writes tokenizer.json, embeddings.npy, inhibit_edges.json)
- `ui`       — launch the Tkinter training / inspection GUI

It does NOT contain embedding or graph logic. All domain logic lives in `src/core/`.

---

## HyperHunk Contract Extension (`src/core/contract/hyperhunk.py`)

The Emitter's local copy of HyperHunk extends the v2 base with:

### attention_weight property
Semantic gravity of this node_kind. Used when writing the Cold Artifact.

```
function_definition / class_definition   2.0
decorated_definition / method_definition 1.8
md_heading / md_code_block               1.5 / 1.4
module_preamble                          1.2
paragraph / md_paragraph                 1.0
fragment_of_*                            0.7
everything else                          1.0
```

V2 upgrade: attention_weight should also consider:
- `decorators` — a `@property` method gets slightly higher weight than a bare function
- `heading_trail` depth — deeper headings get slightly lower weight
- `token_count` — very short hunks (< 20 tokens) get a floor weight reduction

### relations property
Relational DSL: converts DAG pointer fields to algebraic JSON relations.
```json
{"op": "pull",     "target": "<occurrence_id>", "weight": 1.0}
{"op": "precedes", "target": "<occurrence_id>", "weight": 0.8}
```

V2 upgrade: add relations for:
- `scope_stack` entries → `{"op": "scope_member_of", "target": "<scope_name>", "weight": 1.5}`
- `heading_trail` entries → `{"op": "section_of", "target": "<heading_text>", "weight": 1.2}`
- `cross_refs` links → `{"op": "references", "target": "<ref>", "weight": 0.9}`

---

## Assembler (`src/core/assembler/core.py`)

The Assembler converts a HyperHunk into a 3-vertex HyperNode cold artifact:

```
VectorVertex    — the embedding vector
StaticVertex    — the cold anatomy record (content, metadata, v2 context fields)
RelationVertex  — the DAG and relational edges (from v2 relations property)
```

V2 upgrades:
- StaticVertex must store all v2 context fields (scope_stack, heading_trail, etc.)
- StaticVertex must store context_window (for retrieval overlap inspection)
- RelationVertex must include the extended v2 relation ops

### Surveyor (`src/core/surveyor/hyperhunk.py`)

Validates and inspects incoming HyperHunks. V2 upgrade:
- Detect and log v1 hunks (missing v2 fields) — they are valid but tagged
- Report richness metrics: what % of hunks have scope_stack, heading_trail, context_window
- Alert if token_count = 0 on all hunks (indicates v1 Negotiator still in use)

---

## Sliding Window Integration

The `context_window` field (populated by the v2 Splitter's Negotiator) carries
the last N BPE tokens of the preceding hunk into the current hunk's representation.

The Emitter stores this in the StaticVertex. At retrieval time, the hot engine
can access it to smooth cross-boundary signal without re-reading the original doc.

This eliminates the hard cut edges that cause retrieval misses at hunk boundaries.

---

## Bootstrap Nucleus (`src/core/nucleus/bootstrap.py`)

Phase 1 fixed-weight edge scorer. No FFN — uses coupling constants from ontology.py.

The scaffold is now builder-tunable through:
- `BootstrapConfig` in code
- `--bootstrap-profile <json>` on `emit`
- CLI overrides for `--edge-threshold` and `--dominance-threshold`

Each emit run writes `bootstrap_profile_effective.json` beside the Cold Artifact so probe bundles remain reproducible.

```
W_base = mean(get_coupling(A.node_kind), get_coupling(B.node_kind))

Per-surface similarity:
  S_grammatical  — node_kind family + decorator/base_class Jaccard
  S_structural   — structural_path prefix + scope_stack Jaccard + heading_trail Jaccard
  S_statistical  — token_count ratio + word Jaccard
  S_semantic     — cosine on embedding vectors (0.0 if absent)
  S_verbatim     — substring containment + word Jaccard

Surface fractions (default profile):
  grammatical=0.35, structural=0.25, statistical=0.20, semantic=0.15, verbatim=0.05

Base scaffold dials now exposed:
- `edge_threshold`
- `dominance_threshold`
- `surface_fractions`
- `grammatical_match_profile`
- `semantic_absent_threshold_scale`

ConnectionStrength = Σ(W_base × fraction_i × S_i)
RoutingProfile = {surface: fraction_i × S_i / ConnectionStrength}
InteractionType = dominant surface if share ≥ 40%, else "multi_surface"
```

Every evaluation (above and below threshold) is accumulated in `_training_pairs`
for Phase 2 FFN training.  The Phase 2 FFN is EXPLICITLY DEFERRED — do not
build until Phase 1 has generated sufficient training data.

---

## Graph Assembler (`src/core/assembler/core.py`)

Ingest path (per hunk):
1. Optionally embed via DeterministicEmbedProvider
2. Upsert into Cold Artifact (content_node + occurrence_node)
3. Write structural edges (pull, precedes) from hunk.relations
4. Evaluate against sliding window of last 50 hunks via BootstrapNucleus
5. Write edges above threshold with routing_profile stored on the edge

Cold Artifact schema (cold_anatomy.db):
- `content_nodes`    — (hunk_id, node_kind, content, attention_weight, static_mass)
- `occurrence_nodes` — (occurrence_id, hunk_id, origin_id, structural_path, vector_blob)
- `relations`        — (source_occ_id, op, target_occ_id, weight, routing_profile, interaction_mode, interaction_vector)
- `inhibit_edges`    — (token_a, token_b, weight) from NPMI < −0.8
- `content_fts`      — FTS5 with auto-sync triggers on content_nodes

---

## Build Status (Phase 1 complete as of 2026-03-26)

### COMPLETE (all tranches 1–8 shipped)
- `contract/hyperhunk.py`         v2 wire format, 5 surface properties, surface_richness()
- `contract/ontology.py`          node type registry + coupling constants
- `contract/relations.py`         edge predicate registry (10 predicates)
- `core/contract/hyperhunk.py`    Emitter extension: embedding, attention_weight v2, relations
- `core/nucleus/bootstrap.py`     Phase 1 Bootstrap Nucleus (fixed weights)
- `core/assembler/core.py`        Graph Assembler, sliding window=50
- `core/assembler/sqlite_scribe.py` Cold Artifact schema with FTS5 sync triggers
- `core/surveyor/hyperhunk.py`    validate(), HunkSurveyor, StreamReport
- `core/engine/training/`         BPE → cooccurrence → NPMI → SVD pipeline
- `core/engine/inference/`        DeterministicEmbedProvider, HotEngine, BagOfEvidence retrieval
- `src/app.py`                    train + emit + ui CLI (fully wired)
- `src/ui/gui_main.py`            Tkinter GUI: Train / Embed / Nucleus / Inspect tabs

### DEFERRED (Phase 2)
- FFN Nucleus — requires Phase 1 training data; do NOT build until data exists
- TreeSitter engine (Tranche 2) — stub; grammatical_surface returns empty
- PEG engine (Tranche 3) — stub; structural_surface populated by Fallback only
