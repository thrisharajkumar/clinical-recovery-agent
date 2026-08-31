"""
Mocked recommendation engine.

This is a DELIBERATE architectural boundary, not a shortcut: Amy (the LLM
layer) may only *communicate* recommendations that come from this function.
She must never free-generate a clinical recommendation herself. In production
this function is replaced by a real, clinically-validated engine — the
interface (input/output shape) is designed to stay stable across that swap.
"""
from app.models.schemas import Recommendation

# Simple rule table keyed by (procedure_type, recovery_day_bucket).
# A real engine would be clinician-authored and versioned; this is a stand-in
# with the same shape so the swap-in later is a drop-in replacement.
_RULES = {
    ("knee", "0-3"): Recommendation(
        exercise="Ankle pumps, 10 reps every hour while awake",
        rationale="Promotes circulation and reduces clot risk in the first days after surgery, "
                   "without loading the knee joint itself.",
        confidence=0.9,
    ),
    ("knee", "4-7"): Recommendation(
        exercise="Seated knee bends, gentle range within pain-free limits, 3x/day",
        rationale="Early controlled range-of-motion work at this stage helps prevent stiffness "
                   "while the surgical site is still healing.",
        confidence=0.85,
    ),
    ("hip", "0-3"): Recommendation(
        exercise="Short walks with your walker/frame, as tolerated, several times a day",
        rationale="Early mobilisation is one of the strongest predictors of good hip recovery "
                   "outcomes, as long as it stays within your surgeon's weight-bearing guidance.",
        confidence=0.85,
    ),
    ("hip", "4-7"): Recommendation(
        exercise="Standing hip abduction, light resistance, 2x/day",
        rationale="Builds hip stability once the initial swelling has started to settle.",
        confidence=0.8,
    ),
}

_DEFAULT = Recommendation(
    exercise="Gentle mobility as advised by your care team",
    rationale="I don't have a specific recommendation for this combination yet — "
              "your care team's written plan is the right source here.",
    confidence=0.3,
)


def get_recommendation(procedure_type: str, recovery_day: int) -> Recommendation:
    bucket = "0-3" if recovery_day <= 3 else "4-7" if recovery_day <= 7 else "8+"
    return _RULES.get((procedure_type.lower(), bucket), _DEFAULT)
