# Journal 001 — Bootstrap

Date: 2026-03-26

## What happened

Scaffolded the v2 _BDHyperNeuronEMITTER inside the `final/` staging area.

This is Tranche 1: scaffold only. No implementation code yet.

## Why this exists

The v1 Emitter has two structural problems:

1. **Mixed cognitive eras** — Three layers built at different times without a unified
   contract:
   - Era 1: BPE-only API (tokenize/chunk/embed/reverse/pipeline) — operates on raw text
   - Era 2: HyperNode API (embed_hypernode, scribe_hypernode) — the real model
   - Era 3: Reactor / Hot Engine (h_{t+1} = α·h_t + A·h_t - H·h_t) — correct physics
   Era 1 is still wired into the CLI and UI, creating confusion about what the
   operational path actually is.

2. **Thin HyperHunk input** — The v1 Splitter discards most structural context before
   the Emitter ever sees a hunk. The attention_weight and relations are computed from
   a very sparse signal. The H-matrix and static_mass can't become meaningful without
   richer input.

## What the v2 design addresses

The v2 Emitter consumes v2 HyperHunks (see `final/contract/hyperhunk.py`) and:

- Stores all v2 context fields (scope_stack, heading_trail, etc.) in the StaticVertex
- Stores context_window in the StaticVertex for retrieval overlap inspection
- Extends the Relational DSL with new ops:
  - scope_member_of (scope_stack entries → DAG)
  - section_of (heading_trail entries → DAG)
  - references (cross_refs → DAG)
- Updates attention_weight to consider decorators, heading depth, token_count floor
- Detects and reports v1 vs v2 hunk richness via the Surveyor

## What was decided

- Suite model: kept.
- src/ui/ layer: kept. The training and inspection GUI stays in the Emitter.
- src/core/ layer: all domain logic moves here. The cli.py → app.py rename
  aligns with the builder contract's composition root model.
- Era 1 code (raw BPE API): NOT re-homed. The v2 Emitter is built cleanly
  from Era 2/3 concepts. Era 1 stays in the v1 codebase as historical reference.
- Builder constraint contract: copied into `_docs/` and governs all build decisions.

## Current state

Scaffold complete. Architecture documented. No implementation code yet.
Active tranche: Tranche 1 (scaffold). Complete when `app.py` runs without import errors.

## Next step

After the Splitter's Tranche 2 (Negotiator upgrade) is done:
Tranche 2 here: Assembler v2 (handle all new v2 fields in StaticVertex,
store context_window in cold artifact).
