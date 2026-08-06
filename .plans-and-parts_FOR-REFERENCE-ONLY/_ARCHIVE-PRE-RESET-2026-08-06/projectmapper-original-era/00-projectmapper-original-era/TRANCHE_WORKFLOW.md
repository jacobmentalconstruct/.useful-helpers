# Tranche Workflow

Status: pointer only

Contract authority: `_docs/BCC.md`, anchor `BCC-WORKFLOW-REQUIRED-TRANCHE-LOOP`.
Local side-car root is configured in BCC as `.project-mapper`.

The required tranche workflow lives in `_docs/BCC.md`. This file is intentionally
not authoritative and must not duplicate the workflow text.

Use this search when entering a tranche from `.project-mapper`:

```bat
rg "^\[ANCHOR: BCC-WORKFLOW-REQUIRED-TRANCHE-LOOP\]$" _docs\BCC.md
```

Use the BCC spine first when broader context is needed:

```bat
rg "^\[ANCHOR: BCC-SPINE\]$" _docs\BCC.md
```
