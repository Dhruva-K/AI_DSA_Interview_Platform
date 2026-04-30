"""Unit tests for the problem selector scoring logic (no DB, no LLM)."""
import pytest

from backend.agents.problem_selector_agent import (
    _DIFFICULTY_ORDER,
    _difficulty_target,
    _score,
)
from backend.models.schemas import PatternSummary


# ---------------------------------------------------------------------------
# Difficulty ladder
# ---------------------------------------------------------------------------

def test_step_up_after_three_consecutive_solves():
    outcomes = [{"solved": True}, {"solved": True}, {"solved": True}]
    assert _difficulty_target(outcomes, "easy") == "medium"


def test_step_down_after_three_failures():
    outcomes = [{"solved": False}, {"solved": False}, {"solved": False}]
    assert _difficulty_target(outcomes, "medium") == "easy"


def test_no_change_mixed_results():
    outcomes = [{"solved": True}, {"solved": False}, {"solved": True}]
    assert _difficulty_target(outcomes, "medium") == "medium"


def test_no_step_above_hard():
    outcomes = [{"solved": True}, {"solved": True}, {"solved": True}]
    assert _difficulty_target(outcomes, "hard") == "hard"


def test_no_step_below_easy():
    outcomes = [{"solved": False}, {"solved": False}, {"solved": False}]
    assert _difficulty_target(outcomes, "easy") == "easy"


def test_fewer_than_three_sessions_no_change():
    outcomes = [{"solved": True}, {"solved": True}]
    assert _difficulty_target(outcomes, "easy") == "easy"


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _make_problem(topic, difficulty):
    return {"id": 1, "slug": "x", "title": "X", "topic": topic, "difficulty": difficulty}


def test_weak_topic_gets_bonus():
    p = _make_problem("dynamic-programming", "medium")
    s = _score(p, "medium", weak_topics=["dynamic-programming"], dominant_patterns=[], topic_coverage={}, recent_topics=[])
    s_no_bonus = _score(p, "medium", weak_topics=[], dominant_patterns=[], topic_coverage={}, recent_topics=[])
    assert s > s_no_bonus


def test_low_coverage_gets_bonus():
    p = _make_problem("trees", "medium")
    s_low = _score(p, "medium", weak_topics=[], dominant_patterns=[], topic_coverage={"trees": 0}, recent_topics=[])
    s_high = _score(p, "medium", weak_topics=[], dominant_patterns=[], topic_coverage={"trees": 5}, recent_topics=[])
    assert s_low > s_high


def test_pattern_alignment_bonus():
    p = _make_problem("dynamic-programming", "medium")
    s_aligned = _score(p, "medium", weak_topics=[], dominant_patterns=["bad-dp-transition"], topic_coverage={}, recent_topics=[])
    s_not_aligned = _score(p, "medium", weak_topics=[], dominant_patterns=["off-by-one"], topic_coverage={}, recent_topics=[])
    assert s_aligned > s_not_aligned


def test_recency_penalty():
    p = _make_problem("arrays", "medium")
    s_no_recent = _score(p, "medium", weak_topics=[], dominant_patterns=[], topic_coverage={}, recent_topics=["trees"])
    s_recent = _score(p, "medium", weak_topics=[], dominant_patterns=[], topic_coverage={}, recent_topics=["arrays"])
    assert s_no_recent > s_recent


def test_difficulty_mismatch_scores_lower():
    p_match = _make_problem("arrays", "medium")
    p_off = _make_problem("arrays", "hard")
    s_match = _score(p_match, "medium", weak_topics=[], dominant_patterns=[], topic_coverage={}, recent_topics=[])
    s_off = _score(p_off, "medium", weak_topics=[], dominant_patterns=[], topic_coverage={}, recent_topics=[])
    assert s_match > s_off


def test_dp_weak_topic_beats_array_no_bonus():
    dp_problem = _make_problem("dynamic-programming", "medium")
    arr_problem = _make_problem("arrays", "medium")
    common_kwargs = dict(
        target_difficulty="medium",
        weak_topics=["dynamic-programming"],
        dominant_patterns=[],
        topic_coverage={},
        recent_topics=[],
    )
    assert _score(dp_problem, **common_kwargs) > _score(arr_problem, **common_kwargs)
