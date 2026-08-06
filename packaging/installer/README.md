# Useful Helpers - sidecar installer

Drop the toolkit into any project as a self-contained `.useful-helpers/` folder.

## What's in this package

- `run.bat` - Windows launcher (double-click it)
- `run.sh`   - macOS / Linux launcher (`./run.sh`)
- `install.py`    - the installer itself (needs only Python 3)
- `useful-helpers-toolkit.zip` - the toolkit payload it installs

## Use it (with a window)

Run `run.bat` (Windows) or `./run.sh` (macOS/Linux). A folder picker opens:

1. Choose the project you want to install into.
2. Confirm. The installer creates exactly one folder - `.useful-helpers/` - and changes nothing
   else in your project.
3. If a sidecar is already there, it asks: **Reinstall** (wipe and install fresh),
   **Update** (replace the code but KEEP the accumulated journal/evidence memory), or **Cancel**.

The folder picker needs Tkinter (bundled with Python on Windows/macOS; on Linux install
`python3-tk` if prompted).

## Use it (no window / scripted)

```
python install.py --target /path/to/project --mode install     # new install
python install.py --target /path/to/project --mode update      # keep existing memory
python install.py --target /path/to/project --mode reinstall   # wipe and reinstall
```

## After installing

```
cd /path/to/project/.useful-helpers
python -m src.app cli tool-list          # or run.bat list  (Windows)
```

The toolkit's control plane runs on plain Python. For the dependency-backed tools (PDF,
embeddings) run `setup_env.bat` (Windows) or `pip install -r requirements.txt` inside
`.useful-helpers/`.

The sidecar's memory (`journal` / `evidence`) starts empty and fills with your project's work.
It writes only inside `.useful-helpers/`; your project is never modified.
