# Mechanical Tokenizer Bundle

Focused export of the `bdvec.inspect_text` mechanical tokenizer tool.

## Layout

```text
mechanical_tokenizer_bundle/
  inspect_text.py
  tool.json
  run_mechanical_tokenizer.ps1
  requirements.txt
  README.md
  bdvec/
    artifacts/
    bpe_svd/
```

## Included

- root entry script: `inspect_text.py`
- root tool manifest: `tool.json`
- BDVec tokenizer artifacts: `bdvec/artifacts/tokenizer.json`, `bdvec/artifacts/embeddings.npy`
- BDVec runtime source: `bdvec/bpe_svd`
- PowerShell launcher: `run_mechanical_tokenizer.ps1`

## Install

```powershell
pip install -r requirements.txt
```

## Quick Start

From this bundle root:

```powershell
./run_mechanical_tokenizer.ps1 -Text "hello manifold"
./run_mechanical_tokenizer.ps1 -Path "C:\path\to\file.txt" -NearestK 12
```

Direct invocation:

```powershell
python -B .\inspect_text.py --args-json "{\"text\":\"hello manifold\"}"
```

## Notes

- Mandatory Python dependency: `numpy`
- The bundle is intentionally narrow and does not include the broader HoloToolAgent runtime
