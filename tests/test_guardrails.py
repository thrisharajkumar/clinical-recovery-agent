import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.guardrails import check_red_flags, check_output_safety


def test_chest_pain_triggers_escalation():
    result = check_red_flags("I have really bad chest pain right now")
    assert result.triggered
    assert "chest pain" in result.matched_terms


def test_normal_question_does_not_trigger():
    result = check_red_flags("What exercises should I do today?")
    assert not result.triggered


def test_case_insensitive_matching():
    result = check_red_flags("CHEST PAIN is getting worse")
    assert result.triggered


def test_output_safety_blocks_dosage_advice():
    violation = check_output_safety("You should take an extra dose of painkiller")
    assert violation is not None


def test_output_safety_allows_safe_reply():
    violation = check_output_safety("Great job on your exercises today!")
    assert violation is None


def test_provenance_passes_when_no_recommendation_used():
    from app.core.guardrails import check_recommendation_provenance
    assert check_recommendation_provenance("Great job today!", None) is True


def test_provenance_passes_when_reply_matches_recommendation():
    from app.core.guardrails import check_recommendation_provenance
    rec = {"exercise": "Ankle pumps, 10 reps every hour", "rationale": "..."}
    reply = "You should try ankle pumps, 10 reps every hour, gently."
    assert check_recommendation_provenance(reply, rec) is True


def test_provenance_fails_when_reply_drifts_from_recommendation():
    from app.core.guardrails import check_recommendation_provenance
    rec = {"exercise": "Ankle pumps, 10 reps every hour", "rationale": "..."}
    reply = "You should do a 30 minute jog."  # not what the engine returned
    assert check_recommendation_provenance(reply, rec) is False
