# _BDHyperNodeSPLITTER v2

Splits source documents into richly-contextual HyperHunks. Streams NDJSON to stdout.

**Status: Phase 1 baseline runnable** — Fallback, PEG, and TreeSitter paths are live. TreeSitter requires the grammar packages from `requirements.txt`, and deeper language coverage/enrichment still has room to grow.

## Quick start

```bat
setup_env.bat
run.bat stream ./your_docs/
```

## Builder-side signal profiles

The Splitter now accepts an optional builder-facing signal profile:

```powershell
python _BDHyperNodeSPLITTER/src/app.py stream .\_corpus_examples\python-3.11.15-docs-text\reference --signal-profile _BDHyperNodeSPLITTER\_docs\signal_profiles\python_reference_richer_refs_v1.json
```

This profile controls extraction and enrichment only. It does not change the Emitter scorer.

Tracked builder profiles now include:
- [`python_reference_richer_refs_v1.json`](C:/Users/jacob/Documents/_UsefulAgenticBuilderSANDBOX/Claude-Code/_BDNeuralTranslationSUITE/_BDHyperNodeSPLITTER/_docs/signal_profiles/python_reference_richer_refs_v1.json)
- [`python_reference_list_index_v1.json`](C:/Users/jacob/Documents/_UsefulAgenticBuilderSANDBOX/Claude-Code/_BDNeuralTranslationSUITE/_BDHyperNodeSPLITTER/_docs/signal_profiles/python_reference_list_index_v1.json)
