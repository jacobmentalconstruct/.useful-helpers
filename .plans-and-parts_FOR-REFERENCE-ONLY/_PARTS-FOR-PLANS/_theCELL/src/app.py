from .backend import Backend
from .ui import CELL_UI
from src.microservices._TkinterAppShellMS import TkinterAppShellMS


def main():
    # Initialize the logic hub
    backend = Backend()

    # Load persisted theme preference (default Dark)
    theme = (backend.get_setting('theme_preference') or 'Dark').strip().title()
    if theme not in ('Dark', 'Light'):
        theme = 'Dark'

    # Initialize the Mother Ship (Shell)
    shell = TkinterAppShellMS({
        "title": f"_theCELL [{backend.cell_name}]",
        "geometry": "1000x800",
        "theme": theme
    })

    # Dock the UI into the shell
    app_ui = CELL_UI(shell, backend)

    # Auto-save session on close
    def _on_close():
        backend.save_current_session()
        shell.root.destroy()

    shell.root.protocol("WM_DELETE_WINDOW", _on_close)

    # Ignition
    shell.launch()


if __name__ == "__main__":
    main()
