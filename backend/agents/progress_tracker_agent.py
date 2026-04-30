"""
Progress Tracker Agent.

All stats are computed via SQL aggregations.
The LLM is used only to generate focus_areas and milestone text.
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
from backend.services.llm import MODEL, get_client

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
    # -----------------------------------------------------------------------
    # 1. Insert the progress record for this session
    # -----------------------------------------------------------------------
    cur = await db.execute(
        """
        INSERT INTO progress_records
            (user_id, session_id, problem_id, topic, difficulty, solved,
             attempts_count, time_to_solve_seconds, final_correctness_score,
             complexity_verdict, patterns_triggered, learning_path_snapshot)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            user_id, session_id, problem_id, topic, difficulty,
            int(solved), attempts_count, time_to_solve_seconds,
            final_correctness_score, complexity_verdict,
            json.dumps(patterns_triggered), json.dumps(learning_path_snapshot),
        ),
    )
    await db.commit()
    record_id = cur.lastrowid

    # Mark session completed
    await db.execute(
        "UPDATE sessions SET status='completed', ended_at=?, duration_seconds=? WHERE id=?",
        (datetime.now(timezone.utc).isoformat(), time_to_solve_seconds, session_id),
    )
    await db.commit()

    # -----------------------------------------------------------------------
    # 2. Aggregate stats
    # -----------------------------------------------------------------------
    cur = await db.execute(
        "SELECT COUNT(*) as total, SUM(solved) as solved FROM progress_records WHERE user_id=?",
        (user_id,),
    )
    row = await cur.fetchone()
    total_sessions = row["total"]
    total_solved = row["solved"] or 0
    overall_rate = round(total_solved / total_sessions, 3) if total_sessions else 0.0

    cur = await db.execute(
        """
        SELECT topic,
               COUNT(*) as attempted,
               SUM(solved) as solved
        FROM progress_records
        WHERE user_id=?
        GROUP BY topic
        """,
        (user_id,),
    )
    topic_rows = await cur.fetchall()
    topic_stats: dict[str, TopicStats] = {}
    for r in topic_rows:
        att = r["attempted"]
        sol = r["solved"] or 0
        topic_stats[r["topic"]] = TopicStats(
            attempted=att,
            solved=sol,
            success_rate=round(sol / att, 3) if att else 0.0,
        )

    # -----------------------------------------------------------------------
    # 3. Determine suggested difficulty
    # -----------------------------------------------------------------------
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

    # -----------------------------------------------------------------------
    # 4. Identify weak topics and dominant patterns
    # -----------------------------------------------------------------------
    weak_topics: list[Topic] = [
        t for t, s in topic_stats.items() if s.success_rate < _WEAK_THRESHOLD and s.attempted >= 2
    ]

    cur = await db.execute(
        """
        SELECT pattern_type, occurrence_count
        FROM pattern_detections
        WHERE user_id=?
        ORDER BY occurrence_count DESC
        LIMIT 3
        """,
        (user_id,),
    )
    pattern_rows = await cur.fetchall()
    dominant_patterns = [r["pattern_type"] for r in pattern_rows]

    # -----------------------------------------------------------------------
    # 5. LLM: generate focus areas and milestone
    # -----------------------------------------------------------------------
    cur = await db.execute(
        """
        SELECT topic, difficulty, solved
        FROM progress_records
        WHERE user_id=?
        ORDER BY created_at DESC
        LIMIT 10
        """,
        (user_id,),
    )
    recent_raw = await cur.fetchall()
    recent_outcomes = [dict(r) for r in recent_raw]

    focus_areas, milestone = _fallback_focus(weak_topics, total_solved, suggested_difficulty)
    try:
        client = get_client()
        prompt = build_focus_prompt(
            total_sessions=total_sessions,
            total_solved=total_solved,
            topic_stats={t: {"attempted": s.attempted, "solved": s.solved} for t, s in topic_stats.items()},
            dominant_patterns=dominant_patterns,
            recent_outcomes=recent_outcomes,
            suggested_difficulty=suggested_difficulty,
        )
        msg = client.messages.create(
            model=MODEL,
            max_tokens=300,
            temperature=0.5,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        parsed = json.loads(msg.content[0].text)
        focus_areas = parsed.get("focus_areas", focus_areas)
        milestone = parsed.get("milestone", milestone)
    except Exception:
        pass  # keep fallback

    next_topics: list[Topic] = weak_topics[:3] if weak_topics else list(topic_stats.keys())[:2]

    learning_path = LearningPath(
        next_recommended_topics=next_topics,
        suggested_difficulty=suggested_difficulty,
        milestone=milestone,
        focus_areas=focus_areas,
    )

    stats = ProgressStats(
        total_sessions=total_sessions,
        total_solved=total_solved,
        overall_success_rate=overall_rate,
        topic_stats=topic_stats,
    )

    # Update the record with the learning path snapshot
    await db.execute(
        "UPDATE progress_records SET learning_path_snapshot=? WHERE id=?",
        (learning_path.model_dump_json(), record_id),
    )
    await db.commit()

    return ProgressTrackerOutput(
        progress_record_id=record_id,
        updated_stats=stats,
        learning_path=learning_path,
    )


def _fallback_focus(
    weak_topics: list[str],
    total_solved: int,
    suggested_difficulty: str,
) -> tuple[list[str], str]:
    areas = []
    if weak_topics:
        areas.append(f"Focus on {weak_topics[0]} problems — try at least 3 in a row before moving on.")
    areas.append("Before coding, state the time and space complexity of your approach out loud.")
    areas.append("Always test your solution against an empty input and a single-element input before submitting.")

    milestone = ""
    if total_solved == 1:
        milestone = "You've solved your first problem — great start!"
    elif total_solved % 10 == 0:
        milestone = f"You've solved {total_solved} problems. Keep the momentum going!"

    return areas, milestone
