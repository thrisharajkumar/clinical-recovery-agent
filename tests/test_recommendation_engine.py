import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.recommendation_engine import get_recommendation


def test_knee_early_recovery_returns_known_rule():
    rec = get_recommendation("knee", 1)
    assert "ankle pumps" in rec.exercise.lower()
    assert rec.confidence > 0.5


def test_hip_later_recovery_returns_known_rule():
    rec = get_recommendation("hip", 5)
    assert "abduction" in rec.exercise.lower()


def test_unknown_procedure_falls_back_to_default():
    rec = get_recommendation("shoulder", 2)
    assert rec.confidence < 0.5


def test_always_returns_a_rationale():
    rec = get_recommendation("knee", 10)
    assert len(rec.rationale) > 0
