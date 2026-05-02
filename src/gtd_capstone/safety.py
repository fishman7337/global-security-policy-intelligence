"""Safety guardrails for aggregate historical GTD analysis."""

from __future__ import annotations

from gtd_capstone.constants import UNSAFE_CHAT_TERMS


REFUSAL = (
    "I can help with historical, aggregate, educational analysis of the GTD dataset, "
    "but I cannot provide tactical, targeting, weaponization, evasion, or operational guidance."
)


def is_unsafe_request(text: str) -> bool:
    """Return whether a user request crosses the project safety boundary.

    Args:
        text: User-provided prompt text.

    Returns:
        True when the prompt asks for disallowed operational guidance.
    """
    normalized = " ".join(text.lower().split())
    return any(term in normalized for term in UNSAFE_CHAT_TERMS)


def aggregate_only_note() -> str:
    """Return the standard aggregate-analysis safety note.

    Returns:
        Human-readable project safety statement.
    """
    return (
        "All geospatial and model outputs are intended for aggregate historical analysis. "
        "Incident-level tactical use is outside the scope of this project."
    )
