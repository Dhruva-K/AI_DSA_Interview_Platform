"""
Progress Tracker Agent.

All stats are SQL aggregations. The LLM generates focus_areas and milestone text only.
"""
import json
from datetime import datetime, timezone

import aiosqlite

from backend.models.schemas import (
    Difficulty,
    LearningPath,
    ProgressStats,
    ProgressTrackerOutput,
    Topic,
    TopicStats,
)
from backend.prompts.progress_tracker import SYSTEM, build_focus_prompt
from backend.services.llm import chat

_DIFFICULTY_ORDER = ["easy", "medium", "hard"]
_WEAK_THRESHOLD = 0.5


async def run(
    db: aiosqlite.Connection,
    user_id: int,
    session_id: int,
    problem_id: int,
    topic: str,
    difficulty: str,
    solved: bool,
    attempts_count: int,
    time_to_solve_seconds: int,
    final_correctness_score: float,
    complexity_verdict: str,
    patterns_triggered: list[str],
    learning_path_snapshot: dict,
) -> ProgressTrackerOutput:
    cur = await db.execute(
        """
        INSERT INTO progress_records
            (user_id, session_id, problem_id, topic, difficulty, solved,
             attempts_count, time_to_solve_seconds, final_correctness_score,
             complexity_verdict, patterns_triggered, learning_path_snapshot)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            user_id, session_id, problem_id, topic, difficulty, int(solved),
            attempts_count, time_to_solve_seconds, final_correctness_score,
            complexity_verdict, json.dumps(patterns_triggered), json.dumps(learning_path_snapshot),
        ),
    )
    await db.commit()
    record_id = cur.lastrowid

    await db.execute(
        "UPDATE sessions SET status='completed', ended_at=?, duration_seconds=? WHERE id=?",
        (datetime.now(timezone.utc).isoformat(), time_to_solve_seconds, session_id),
    )
    await db.commit()

    # --- Aggregate stats ---
    cur = await db.execute(
        "SELECT COUNT(*) as total, SUM(solved) as solved FROM progress_records WHERE user_id=?",
        (user_id,),
    )
    row = await cur.fetchone()
    total_sessions = row["total"]
    total_solved = row["solved"] or 0
    overall_rate = round(total_solved / total_sessions, 3) if total_sessions else 0.0

    cur = await db.execute(
        "SELECT topic, COUNT(*) as attempted, SUM(solved) as solved FROM progress_records WHERE user_id=? GROUP BY topic",
        (user_id,),
    )
    topic_stats: dict[str, TopicStats] = {
        r["topic"]: TopicStats(
            attempted=r["attempted"],
            solved=r["solved"] or 0,
            success_rate=round((r["solved"] or 0) / r["attempted"], 3),
        )
        for r in await cur.fetchall()
    }

    # --- Suggested difficulty ---
    cur = await db.execute(
        "SELECT difficulty, solved FROM progress_records WHERE user_id=? ORDER BY created_at DESC LIMIT 3",
        (user_id,),
    )
    last3 = await cur.fetchall()
    current_diff = difficulty
    if len(last3) >= 3:
        rate = sum(r["solved"] for r in last3) / 3
        idx = _DIFFICULTY_ORDER.index(current_diff)
        if rate > 0.80 and idx < 2:
            current_diff = _DIFFICULTY_ORDER[idx + 1]
        elif rate < 0.40 and idx > 0:
            current_diff = _DIFFICULTY_ORDER[idx - 1]
    suggested_difficulty: Difficulty = current_diff

    weak_topics: list[Topic] = [
        t for t, s in topic_stats.items()
        if s.success_rate < _WEAK_THRESHOLD and s.attempted >= 2
    ]

    cur = await db.execute(
        "SELECT pattern_type FROM pattern_detections WHERE user_id=? ORDER BY occurrence_count DESC LIMIT 3",
        (user_id,),
    )
    dominant_patterns = [r["pattern_type"] for r in await cur.fetchall()]

    cur = await db.execute(
        "SELECT topic, difficulty, solved FROM progress_records WHERE user_id=? ORDER BY created_at DESC LIMIT 10",
        (user_id,),
    )
    recent_outcomes = [dict(r) for r in await cur.fetchall()]

    # --- LLM: focus areas and milestone ---
    focus_areas, milestone = _fallback_focus(weak_topics, total_solved, suggested_difficulty)
    try:
        raw = chat(
            system=SYSTEM,
            user=build_focus_prompt(
                total_sessions=total_sessions,
                total_solved=total_solved,
                topic_stats={t: {"attempted": s.attempted, "solved": s.solved} for t, s in topic_stats.items()},
                dominant_patterns=dominant_patterns,
                recent_outcomes=recent_outcomes,
                suggested_difficulty=suggested_difficulty,
            ),
            max_tokens=300,
            temperature=0.5,
        )
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        parsed = json.loads(raw)
        focus_areas = parsed.get("focus_areas", focus_areas)
        milestone = parsed.get("milestone", milestone)
    except Exception:
        pass

    next_topics: list[Topic] = weak_topics[:3] if weak_topics else list(topic_stats.keys())[:2]
    learning_path = LearningPath(
        next_recommended_topics=next_topics,
        suggested_difficulty=suggested_difficulty,
        milestone=milestone,
        focus_areas=focus_areas,
    )

    await db.execute(
        "UPDATE progress_records SET learning_path_snapshot=? WHERE id=?",
        (learning_path.model_dump_json(), record_id),
    )
    await db.commit()

    return ProgressTrackerOutput(
        progress_record_id=record_id,
        updated_stats=ProgressStats(
            total_sessions=total_sessions,
            total_solved=total_solved,
            overall_success_rate=overall_rate,
            topic_stats=topic_stats,
        ),
        learning_path=learning_path,
    )


def _fallback_focus(weak_topics, total_solved, suggested_difficulty):
    areas = []
    if weak_topics:
        areas.append(f"Focus on {weak_topics[0]} — aim for 3 consecutive solves before moving on.")
    areas.append("State the time and space complexity of your approach before coding.")
    areas.append("Always test your solution against an empty input and a single-element input.")
    milestone = ""
    if total_solved == 1:
        milestone = "You've solved your first problem — great start!"
    elif total_solved % 10 == 0:
        milestone = f"You've solved {total_solved} problems. Keep the momentum going!"
    return areas, milestone
