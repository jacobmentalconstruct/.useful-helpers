# Sidecar Workbench

Sidecar Workbench is a self-contained local instrument attached to one directory. It
observes that directory, builds durable evidence-backed knowledge about it, exposes
deterministic capabilities over it, and allows humans or agents to make governed
changes through one control plane.

The experiential standard is: **a calm workbench with receipts**.

This repository is a clean implementation. Its own architecture is defined in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). The current code stops at the Phase 1
identity-and-hands milestone described in [`docs/PHASE_1.md`](docs/PHASE_1.md).

## Try the Phase 1 prototype

Python 3.11 or newer is required. From this repository:

```powershell
python -m factory attach C:\path\to\target
python C:\path\to\target\.sidecar\bin\sidecar.py status
python C:\path\to\target\.sidecar\bin\sidecar.py tools
python C:\path\to\target\.sidecar\bin\sidecar.py call inventory --args '{}'
```

An intentional write requires both Apply authority and an explicit confirmation:

```powershell
python C:\path\to\target\.sidecar\bin\sidecar.py call write_file `
  --authority apply `
  --args '{"path":"notes.txt","content":"hello\n","confirm":true}'
```

The installed instrument writes its own code and state only beneath
`TARGET/.sidecar/`. A confirmed target edit is a work product and remains if the
instrument is removed.

## Verify

```powershell
python -m unittest discover -s tests -v
```
