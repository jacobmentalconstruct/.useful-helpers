from __future__ import annotations


def run(arguments: dict) -> dict:
    text = str(arguments.get("text", ""))
    if not text:
        text = "No text provided."

    words = text.split()
    return {
        "tool": "echo.summary",
        "input_length": len(text),
        "word_count": len(words),
        "preview": " ".join(words[:12]),
        "arguments": arguments,
    }
