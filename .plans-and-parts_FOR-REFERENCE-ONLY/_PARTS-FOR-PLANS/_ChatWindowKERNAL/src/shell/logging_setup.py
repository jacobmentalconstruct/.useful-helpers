"""
Owns: logging initialization for file and console handlers.
Does not own: application lifecycle, crash routing, or message semantics.
Collaborates with: bootstrap code and every subsystem logger.
"""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Any

from src.utils.file_io import ensure_directory
from src.utils.json_utils import load_json_file
from src.utils.paths import AppPaths


def configure_logging(paths: AppPaths) -> logging.Logger:
    ensure_directory(paths.logs_dir)
    ensure_directory(paths.crash_reports_dir)
    ensure_directory(paths.snapshots_dir)

    config_payload = load_json_file(paths.logging_config_file, {})
    if config_payload:
        _patch_log_file(config_payload, paths.log_file)

    try:
        if config_payload:
            logging.config.dictConfig(config_payload)
        else:
            _configure_fallback_logging(paths.log_file)
    except Exception:
        _configure_fallback_logging(paths.log_file)
        logging.getLogger("app").exception("Failed to apply logging configuration.")

    logger = logging.getLogger("app")
    logger.debug("Logging configured. log_file=%s", paths.log_file)
    return logger


def _patch_log_file(config_payload: dict[str, Any], log_file: Path) -> None:
    handlers = config_payload.get("handlers", {})
    file_handler = handlers.get("file")
    if isinstance(file_handler, dict):
        file_handler["filename"] = str(log_file)


def _configure_fallback_logging(log_file: Path) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
