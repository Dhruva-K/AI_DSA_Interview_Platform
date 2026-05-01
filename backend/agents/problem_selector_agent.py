"""
Problem Selector Agent.

Scoring is fully deterministic. The LLM generates only a one-sentence rationale.
"""
import aiosqlite

from backend.models.schemas import (
    Difficulty,
    PatternSummary,
    ProblemSelectorInput,
    ProblemSelectorOutput,
    Topic,
)
from backend.prompts.problem_selector import SYSTEM, build_rationale_prompt
from backend.services.llm import chat

_WEAK_TOPIC_BONUS = 3.0
_COVERAGE_BONUS   = 1.5
_PATTERN_ALIGNMENT = 2.0
_RECENCY_PENALTY  = 1.0

_PATTERN_TOPIC_MAP: dict[str, list[str]] = {
    "off-by-one":               ["arrays", "binary-search", "sliding-window", "linked-lists"],
    "missing-edge-case":        ["arrays", "strings", "linked-lists", "stack-queue"],
    "bad-dp-transition":        ["dynamic-programming"],
    "inefficient-loop":         ["arrays", "strings", "dynamic-programming"],
    "wrong-base-case":          ["dynamic-programming", "trees", "backtracking"],
    "incorrect-pointer-movement": ["linked-lists", "sliding-window", "arrays"],
    "missing-null-check":       ["trees", "linked-lists", "graphs"],
}

_DIFFICULTY_ORDER = ["easy", "medium", "hard"]


def _difficulty_target(recent_outcomes: list[dict], current: Difficulty) -> Difficulty:
    last3 = [o["solved"] for o in recent_outcomes[-3:]]
    if len(last3) >= 3:
        rate = sum(last3) / len(last3)
        idx = _DIFFICULTY_ORDER.index(current)
        if rate > 0.80 and idx < 2:
            return _DIFFICULTY_ORDER[idx + 1]
        if rate < 0.40 and idx > 0:
            return _DIFFICULTY_ORDER[idx - 1]
    return current


def _score(
    problem: dict,
    target_difficulty: Difficulty,
    weak_topics: list[str],
    dominant_patterns: list[str],
    topic_coverage: dict[str, int],
    recent_topics: list[str],
) -> float:
    score = 0.0
    if problem["difficulty"] == target_difficulty:
        score += 5.0
    elif abs(_DIFFICULTY_ORDER.index(problem["difficulty"]) - _DIFFICULTY_ORDER.index(target_difficulty)) == 1:
        score += 2.0

    topic = problem["topic"]
    if topic in weak_topics:
        score += _WEAK_TOPIC_BONUS
    if topic_coverage.get(topic, 0) < 2:
        score += _COVERAGE_BONUS

    aligned: set[str] = set()
    for p in dominant_patterns:
        aligned.update(_PATTERN_TOPIC_MAP.get(p, []))
    if topic in aligned:
        score += _PATTERN_ALIGNMENT

    for t in recent_topics[-3:]:
        if t == topic:
            score -= _RECENCY_PENALTY

    return score


async def run(db: aiosqlite.Connection, inp: ProblemSelectorInput) -> ProblemSelectorOutput:
    cur = await db.execute(
        """
        SELECT p.topic, pr.solved
        FROM progress_records pr
        JOIN problems p ON p.id = pr.problem_id
        WHERE pr.user_id = ?
        ORDER BY pr.created_at DESC LIMIT 10
        """,
        (inp.user_id,),
    )
    rows = await cur.fetchall()
    recent_topics = [r["topic"] for r in rows]
    recent_outcomes = [{"topic": r["topic"], "solved": bool(r["solved"])} for r in rows]

    target_diff = _difficulty_target(recent_outcomes, inp.current_difficulty)

    if inp.solved_problem_ids:
        placeholders = ",".join("?" * len(inp.solved_problem_ids))
        cur = await db.execute(
            f"SELECT id, slug, title, topic, difficulty FROM problems WHERE id NOT IN ({placeholders})",
            inp.solved_problem_ids,
        )
    else:
        cur = await db.execute("SELECT id, slug, title, topic, difficulty FROM problems")
    candidates_raw = await cur.fetchall()

    if not candidates_raw:
        cur = await db.execute("SELECT id, slug, title, topic, difficulty FROM problems LIMIT 1")
        candidates_raw = await cur.fetchall()

    scored = sorted(
        [(
            _score(dict(r), target_diff, inp.pattern_summary.weak_topics,
                   inp.pattern_summary.dominant_patterns, inp.topic_coverage, recent_topics),
            dict(r),
        ) for r in candidates_raw],
        key=lambda x: x[0],
        reverse=True,
    )
    top5 = [p for _, p in scored[:5]]
    chosen = top5[0]

    rationale = _fallback_rationale(chosen, inp.pattern_summary)
    try:
        rationale = chat(
            system=SYSTEM,
            user=build_rationale_prompt(
                inp.pattern_summary.weak_topics,
                inp.pattern_summary.dominant_patterns,
                top5,
                chosen["slug"],
            ),
            max_tokens=80,
            temperature=0.4,
        )
    except Exception:
        pass

    return ProblemSelectorOutput(
        selected_problem_id=chosen["id"],
        selection_rationale=rationale,
        topic=chosen["topic"],
        difficulty=chosen["difficulty"],
    )


def _fallback_rationale(problem: dict, pattern_summary: PatternSummary) -> str:
    if problem["topic"] in pattern_summary.weak_topics:
        return f"Selected to target your weak area in {problem['topic']} at {problem['difficulty']} difficulty."
    return f"Selected a {problem['difficulty']} {problem['topic']} problem to build balanced coverage."
