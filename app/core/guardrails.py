"""
Safety guardrails for Amy.

Deliberately simple and rule-based for the prototype stage — explainable and
auditable, which matters more than being clever at this stage of a regulated
health product. A trained classifier is a "what changes in production" item,
not a prototype requirement.
"""
from dataclasses import dataclass
from typing import Optional

# Non-exhaustive on purpose for a prototype — but each entry should be a term
# a real post-surgical patient plausibly types, not textbook jargon.
RED_FLAG_TERMS = [
    "chest pain", "can't breathe", "cant breathe", "difficulty breathing",
    "shortness of breath", "severe pain", "unbearable pain",
    "wound is bleeding", "won't stop bleeding", "wont stop bleeding",
    "fever", "pus", "infection", "swollen and red", "blue lips",
    "suicidal", "want to end my life", "kill myself", "self harm",
    "don't want to be here anymore", "dont want to be here anymore",
    "passed out", "fainted", "confused and dizzy",
]

# Amy must never do these things, regardless of what the LLM generates.
DISALLOWED_OUTPUT_PATTERNS = [
    "you should take", "increase your dose", "stop taking your medication",
    "you don't need to see a doctor", "you dont need to see a doctor",
    "it's definitely", "it is definitely",  # overclaiming certainty
]


@dataclass
class RedFlagResult:
    triggered: bool
    matched_terms: list[str]


def check_red_flags(user_message: str) -> RedFlagResult:
    text = user_message.lower()
    matched = [term for term in RED_FLAG_TERMS if term in text]
    return RedFlagResult(triggered=len(matched) > 0, matched_terms=matched)


def escalation_message() -> str:
    return (
        "That sounds like something your care team or emergency services "
        "need to know about right away — I'm not able to assess this safely. "
        "Please contact your care team now, or call emergency services if "
        "this feels urgent. I'll pause the coaching conversation here."
    )


def check_output_safety(draft_reply: str) -> Optional[str]:
    """Returns a violated-pattern string if the draft reply looks unsafe, else None.
    In production this would be a second classifier call, not a substring match —
    this is the honest prototype version, not a shortcut being hidden."""
    lowered = draft_reply.lower()
    for pattern in DISALLOWED_OUTPUT_PATTERNS:
        if pattern in lowered:
            return pattern
    return None


def check_recommendation_provenance(reply: str, recommendation: Optional[dict]) -> bool:
    """Verifies the reply actually mentions the exercise the recommendation
    engine returned, when one was used. This catches a real failure mode
    the tool-use loop alone doesn't prevent: the LLM calling the tool
    correctly, then still describing a *different* exercise in its final
    text (e.g. adding an invented dosage, or substituting a different
    activity). Returns True if there's no recommendation to check against,
    or if the reply contains it; False if the reply looks like it drifted
    from what the engine actually returned.

    This is a simple substring check, not semantic verification — it will
    miss a paraphrase that changes meaning while keeping the exercise name.
    A production version would compare structured fields more rigorously
    (e.g. did the reply state a frequency/dosage not present in the
    recommendation at all)."""
    if recommendation is None:
        return True
    exercise = recommendation.get("exercise", "")
    if not exercise:
        return True
    return exercise.lower() in reply.lower()
