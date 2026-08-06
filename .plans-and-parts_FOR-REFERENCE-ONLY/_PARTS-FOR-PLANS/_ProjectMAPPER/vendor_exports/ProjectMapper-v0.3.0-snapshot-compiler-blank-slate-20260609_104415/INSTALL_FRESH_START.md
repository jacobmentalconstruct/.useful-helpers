# ProjectMapper Blank-Slate Vendor Export

Package: `ProjectMapper-v0.3.0-snapshot-compiler-blank-slate-20260609_104415`
Created: `2026-06-09T10:44:15`

This export is intended for clean external testing. It contains the installable ProjectMapper app files only.

## What Is Included

- App source under `src/`
- Runtime scripts: `setup_env.bat` and `run.bat`
- README, license, requirements, and app assets
- A vendor export manifest

## What Is Not Included

- Git history or repository metadata
- Local virtual environments
- Python caches
- Previous `_projectmapper` snapshot outputs
- Prior SQLite databases, logs, or generated vendor exports
- Local `.env*` files

## Fresh Install Test

1. Copy this folder into a blank test project or any external project folder.
2. Run `setup_env.bat` from this folder.
3. Run `run.bat`.
4. In the app, choose the project root you want to test.
5. Compile a snapshot. New records will be created only under the selected project's `_projectmapper` output folder.

The app does not need prior ProjectMapper records to start.
