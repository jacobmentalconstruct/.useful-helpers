"""
FILE:       src/core/docs.py
ROLE:       Generate the docs that are DERIVED from the registry, so they cannot drift.
DOMAIN:     core
DOES:       generate_tools_md: render docs/TOOLS.md from the discovered tool manifests - the
            single source of truth. Anything a manifest already knows is generated, never
            hand-maintained; drift becomes a bug the smoke suite catches, not rot nobody notices.
DEPENDS ON: src.core.{config,registry}, (stdlib) datetime, pathlib
WIRES TO:   invoked by interfaces.cli (`docs-refresh`); the output is checked by tests/test_smoke.
NOTES:      Phase 5. TOOLS.md carries a GENERATED banner and is byte-reproducible from the
            registry - the smoke suite regenerates it and asserts no diff, so a stale catalog
            fails CI instead of quietly lying (the exact rot Phase 5 exists to end).
"""
from __future__ import annotations

from datetime import datetime, timezone

from src.core import registry
from src.core.config import Paths

_BANNER = (
    "<!-- GENERATED FILE - do not edit by hand.\n"
    "     Regenerate with:  python -m src.app cli docs-refresh\n"
    "     Source of truth:  tools/*/tool.json (via config/registry.json).\n"
    "     The smoke suite asserts this file matches the registry, so edits here are reverted. -->\n"
)

# Stable, human-facing order; anything not listed falls to the end, alphabetically.
_CATEGORY_ORDER = [
    "orientation", "introspection", "code-intel", "memory", "packaging",
    "prompt-eval", "graph", "editing", "runtime", "net", "pdf", "uncategorized",
]

def _schema_hint(schema: dict) -> str:
    """A compact one-line hint of a tool's inputs: required in bold, the rest plain."""
    props = (schema or {}).get("properties") or {}
    if not props:
        return "-"
    required = set((schema or {}).get("required") or [])
    parts = [f"**{k}**" if k in required else k for k in props]
    shown = ", ".join(parts[:8])
    return shown + (f", +{len(parts) - 8} more" if len(parts) > 8 else "")


def render_tools_md(paths: Paths) -> str:
    tools = sorted(registry.list_tools(paths), key=lambda t: t.id)
    by_cat: dict[str, list] = {}
    for t in tools:
        by_cat.setdefault(t.category or "uncategorized", []).append(t)

    ordered = [c for c in _CATEGORY_ORDER if c in by_cat]
    ordered += sorted(c for c in by_cat if c not in _CATEGORY_ORDER)

    lines = [
        _BANNER,
        "# Tools - the capability catalog",
        "",
        f"{len(tools)} tools, grouped by category. Generated from the registry; **what** each "
        "tool does is here, **how to drive them** (sequencing, flags, trust) is in "
        "[OPERATIONS.md](OPERATIONS.md).",
        "",
        "Authority: `Observe` read-only | `Sandbox` temp/artifacts only | `Apply` writes for real. "
        "`writes` declares what a tool may touch (`none`/`toolkit`/`target`); the seam enforces it "
        "for Observe tools (see [ARCHITECTURE.md](ARCHITECTURE.md)).",
        "",
    ]
    for cat in ordered:
        rows = sorted(by_cat[cat], key=lambda t: t.id)
        lines.append(f"## {cat}  ({len(rows)})")
        lines.append("")
        lines.append("| tool | authority | writes | on | inputs | summary |")
        lines.append("|---|---|---|---|---|---|")
        for t in rows:
            summary = (t.summary or "").replace("|", "\\|")
            lines.append(
                f"| `{t.id}` | {t.authority} | {t.writes} | {t.operates_on} | "
                f"{_schema_hint(t.input_schema)} | {summary} |")
        lines.append("")

    lines.append("---")
    lines.append(f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d')} from "
                 f"{len(tools)} manifests._")
    return "\n".join(lines) + "\n"


def generate_tools_md(paths: Paths) -> dict:
    """Write docs/TOOLS.md from the registry. Returns a small report.

    The reported path is DERIVED from where the file was actually written, never a
    literal: this returned "_docs/TOOLS.md" while writing `docs/` for several tranches,
    so the one field a caller reads to find the output named the wrong place.
    """
    content = render_tools_md(paths)
    out = paths.docs / "TOOLS.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    try:
        where = out.relative_to(paths.root).as_posix()
    except ValueError:
        where = out.as_posix()
    return {"written": where, "bytes": len(content)}
