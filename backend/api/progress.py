import json

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_current_user
from backend.models.schemas import TopicStats
from backend.services.db import get_db

router = APIRouter(prefix="/users/me", tags=["progress"])


@router.get("/progress")
async def get_progress(user: dict = Depends(get_current_user)):
    user_id = user["user_id"]
    async with get_db() as db:
        cur = await db.execute(
            "SELECT COUNT(*) as total, SUM(solved) as solved FROM progress_records WHERE user_id=?",
            (user_id,),
        )
        row = await cur.fetchone()
        total = row["total"] or 0
        solved = row["solved"] or 0

        cur = await db.execute(
            """
            SELECT topic, COUNT(*) as attempted, SUM(solved) as solved
            FROM progress_records WHERE user_id=?
            GROUP BY topic
            """,
            (user_id,),
        )
        topic_rows = await cur.fetchall()
        topic_stats = {
            r["topic"]: TopicStats(
                attempted=r["attempted"],
                solved=r["solved"] or 0,
                success_rate=round((r["solved"] or 0) / r["attempted"], 3),
            )
            for r in topic_rows
        }

        cur = await db.execute(
            """
            SELECT pr.id as session_id, p.title, p.topic, p.difficulty, pr.solved, pr.created_at
            FROM progress_records pr
            JOIN problems p ON p.id = pr.problem_id
            WHERE pr.user_id=?
            ORDER BY pr.created_at DESC
            LIMIT 10
            """,
            (user_id,),
        )
        recent = [dict(r) for r in await cur.fetchall()]

    return {
        "total_sessions": total,
        "total_solved": solved,
        "overall_success_rate": round(solved / total, 3) if total else 0.0,
        "topic_stats": topic_stats,
        "recent_sessions": recent,
    }


@router.get("/patterns")
async def get_patterns(user: dict = Depends(get_current_user)):
    async with get_db() as db:
        cur = await db.execute(
            """
            SELECT pattern_type, topic, occurrence_count, severity,
                   first_seen_at, last_seen_at, example_submission_ids
            FROM pattern_detections
            WHERE user_id=?
            ORDER BY occurrence_count DESC
            """,
            (user["user_id"],),
        )
        rows = [dict(r) for r in await cur.fetchall()]
        for r in rows:
            r["example_submission_ids"] = json.loads(r["example_submission_ids"])
    return {"patterns": rows}


@router.get("/learning-path")
async def get_learning_path(user: dict = Depends(get_current_user)):
    async with get_db() as db:
        cur = await db.execute(
            """
            SELECT learning_path_snapshot
            FROM progress_records
            WHERE user_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user["user_id"],),
        )
        row = await cur.fetchone()
        if not row or not row["learning_path_snapshot"]:
            return {
                "next_recommended_topics": [],
                "suggested_difficulty": "easy",
                "milestone": "",
                "focus_areas": ["Complete your first session to get a personalized learning path."],
            }
        return json.loads(row["learning_path_snapshot"])
