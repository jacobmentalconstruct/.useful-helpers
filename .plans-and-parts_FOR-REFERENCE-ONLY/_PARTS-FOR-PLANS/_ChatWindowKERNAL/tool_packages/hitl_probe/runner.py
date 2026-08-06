from __future__ import annotations


def run(arguments: dict) -> dict:
    subject = str(arguments.get("subject", "tool review"))
    return {
        "tool": "hitl.probe",
        "subject": subject,
        "requires_human_review": True,
        "recommended_action": "Open Agent HUD and record a human decision before continuing.",
        "arguments": arguments,
    }
