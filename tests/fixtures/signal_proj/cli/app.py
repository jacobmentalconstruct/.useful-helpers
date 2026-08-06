"""Typer-style CLI adapter (parse-only fixture)."""
from services import core

app = "typer_app_placeholder"


@app.command()
def plan_list():
    """A CLI command: invoked by the framework at runtime, never called in code.
    dead_code must NOT flag this high-confidence (framework entrypoint)."""
    return core.used_service()


@app.callback()
def main():
    return None
