from __future__ import annotations

from pathlib import Path

from src.shell.app_kernel import launch


def main() -> None:
    launch(Path(__file__).resolve().parent)


if __name__ == "__main__":
    main()
