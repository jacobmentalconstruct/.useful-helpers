# ProjectMapper Implementation Slice

Status: superseded as project authority; retained as an implementation slice

This folder was the first ProjectMapper-focused scaffold created before the
project identity was corrected. The active project is now the `.useful-helpers`
root.

Current authority lives at:

- `../BCC.md`
- `../_docs/CURRENT_STATE.md`
- `../_docs/PROJECT_PLAN.md`
- `../_journal/`

This folder still contains useful code and tests for the ProjectMapper portion
of the future Useful Helpers Workbench. Treat it as a source slice to fold into
the root GUI architecture, not as the governing project root.

Run existing slice:

```bat
python src\app.py
```

Test existing slice:

```bat
python -m pytest -q
```
