"""
FILE:       src/app.py
ROLE:       Control-plane entry point. Boots one of: cli | mcp | ui | ui-probe.
DOMAIN:     core (composition root / app-state authority)
DOES:       Parse the mode arg, resolve paths, configure logging, dispatch to the chosen
            interface. The single place the suite is wired.
DEPENDS ON: src.core.config, src.lib.logging_setup, src.interfaces.{cli,mcp_server}
WIRES TO:   src.interfaces.cli, src.interfaces.mcp_server, src.ui.app_ui
NOTES:      Composition-root pattern, rewritten lean: core.invoke() is the one governed seam.
            ui-probe builds the real window, drives one invoke() through it, and exits  -
            deterministic verification without a blocking mainloop.
"""
from __future__ import annotations

import sys

from src.core import presence, registry
from src.core.config import NoTargetBound, resolve_paths
from src.interfaces import cli, mcp_server
from src.lib import logging_setup

USAGE = "usage: python -m src.app <cli|mcp|ui|map|install|plan|ui-probe|map-probe|install-probe|plan-probe> [options]"


def main(argv: list[str]) -> int:
    # stdout carries JSON for programmatic consumers; on Windows a piped stdout defaults to
    # cp1252, mangling any non-ASCII payload (em-dashes in git subjects, etc.). Force UTF-8.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):  # pragma: no cover - non-reconfigurable streams
            pass
    if not argv:
        sys.stderr.write(USAGE + "\n")
        return 2

    mode, rest = argv[0], argv[1:]
    try:
        paths = resolve_paths()
    except NoTargetBound as e:
        # An explicitly supplied target that does not exist is a hard stop, not a
        # fallback. Report it plainly rather than as a traceback.
        sys.stderr.write(f"error: {e}\n")
        return 2
    # A clean checkout has no derived registry. Generate it once, here, so any
    # entrance - cli, mcp, ui - works out of the box rather than requiring the
    # operator to know about `registry-refresh` first.
    registry.ensure_manifest(paths)

    # Presence is EPHEMERAL: a new session must not inherit the last one's
    # context. Stale presence is worse than none, because it answers
    # confidently. This is the restart the store is defined against.
    presence.clear(paths)

    scrub = [(str(paths.root), "<toolkit>")]
    if paths.project_root is not None:
        scrub.insert(0, (str(paths.project_root), "<project>"))
    logging_setup.configure(paths.logs, scrub_roots=tuple(scrub))

    if mode == "cli":
        return cli.dispatch(paths, rest)
    if mode == "mcp":
        return mcp_server.serve_stdio(paths)
    if mode == "ui":
        from src.ui import app_ui  # imported lazily; Tk not needed for cli/mcp
        return app_ui.run(paths)
    if mode == "map":
        from src.ui import app_ui
        return app_ui.run_mapper(paths)
    if mode == "install":
        from src.ui import app_ui
        return app_ui.run_installer(paths)
    if mode == "plan":
        from src.ui import app_ui
        return app_ui.run_planner(paths)
    if mode == "plan-probe":
        from src.ui import app_ui
        return app_ui.run_planner_probe(paths)
    if mode == "ui-probe":
        from src.ui import app_ui
        tool_id = rest[0] if rest else "ping"
        args_json = rest[1] if len(rest) > 1 else ""
        return app_ui.run_probe(paths, tool_id=tool_id, args_json=args_json)
    if mode == "map-probe":
        from src.ui import app_ui
        root_dir = rest[0] if rest else "."
        markdown = len(rest) > 1 and rest[1].lower() in ("1", "true", "md", "yes")
        return app_ui.run_mapper_probe(paths, root_dir=root_dir, markdown=markdown)
    if mode == "install-probe":
        from src.ui import app_ui
        target = rest[0] if rest else "."
        return app_ui.run_installer_probe(paths, target=target)

    sys.stderr.write(f"unknown mode: {mode}\n{USAGE}\n")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
