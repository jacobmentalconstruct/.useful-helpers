"""
Owns: project-relative filesystem path discovery for the installed kernel.
Does not own: config parsing, state persistence, or logging behavior.
Collaborates with: bootstrap code and shell services that need stable paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    root: Path
    config_dir: Path
    state_dir: Path
    logs_dir: Path
    runtime_dir: Path
    crash_reports_dir: Path
    snapshots_dir: Path
    src_dir: Path
    assets_dir: Path
    tool_packages_dir: Path
    scripts_dir: Path
    app_config_file: Path
    logging_config_file: Path
    ui_defaults_file: Path
    window_state_file: Path
    ui_state_file: Path
    session_state_file: Path
    log_file: Path
    agent_db_file: Path


def build_app_paths(root: Path) -> AppPaths:
    config_dir = root / "config"
    state_dir = root / "state"
    logs_dir = root / "logs"
    runtime_dir = root / "runtime"
    crash_reports_dir = runtime_dir / "crash_reports"
    snapshots_dir = runtime_dir / "snapshots"

    return AppPaths(
        root=root,
        config_dir=config_dir,
        state_dir=state_dir,
        logs_dir=logs_dir,
        runtime_dir=runtime_dir,
        crash_reports_dir=crash_reports_dir,
        snapshots_dir=snapshots_dir,
        src_dir=root / "src",
        assets_dir=root / "assets",
        tool_packages_dir=root / "tool_packages",
        scripts_dir=root / "scripts",
        app_config_file=config_dir / "app_config.json",
        logging_config_file=config_dir / "logging.json",
        ui_defaults_file=config_dir / "ui_defaults.json",
        window_state_file=state_dir / "window_state.json",
        ui_state_file=state_dir / "ui_state.json",
        session_state_file=state_dir / "session_state.json",
        log_file=logs_dir / "app.log",
        agent_db_file=state_dir / "agent_memory.db",
    )
