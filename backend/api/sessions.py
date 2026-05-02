import json

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.deps import get_current_user
from backend.models.schemas import MessageRequest, SubmitCodeRequest
from backend.services import orchestrator
from backend.services.db import get_db

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def start_session(user: dict = Depends(get_current_user)):
    try:
        result = await orchestrator.start_session(user["user_id"])
        return {
            "session_id": result["session_id"],
            "problem": result["problem"],
            "phase": result["phase"],
            "opening_message": result["opening_message"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}")
async def get_session(session_id: int, user: dict = Depends(get_current_user)):
    async with get_db() as db:
        cur = await db.execute("SELECT * FROM sessions WHERE id=?", (session_id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        session = dict(row)
        if session["user_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Forbidden")

        cur = await db.execute("SELECT * FROM problems WHERE id=?", (session["problem_id"],))
        problem_row = await cur.fetchone()
        problem = dict(problem_row)
        for field in ("constraints", "examples", "test_cases", "follow_up_questions", "source_tags"):
            problem[field] = json.loads(problem[field])

    return {
        "session_id": session["id"],
        "problem": problem,
        "phase": session["phase"],
        "status": session["status"],
        "conversation_history": json.loads(session["conversation_history"]),
    }


@router.post("/{session_id}/message")
async def send_message(
    session_id: int,
    body: MessageRequest,
    user: dict = Depends(get_current_user),
):
    try:
        result = await orchestrator.process_message(session_id, user["user_id"], body.content)
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/submit-code")
async def submit_code(
    session_id: int,
    body: SubmitCodeRequest,
    user: dict = Depends(get_current_user),
):
    try:
        result = await orchestrator.submit_code(
            session_id, user["user_id"], body.code, body.language
        )
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/end")
async def end_session(session_id: int, user: dict = Depends(get_current_user)):
    try:
        result = await orchestrator.end_session(session_id, user["user_id"])
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/review")
async def get_review(session_id: int, user: dict = Depends(get_current_user)):
    async with get_db() as db:
        cur = await db.execute(
            "SELECT user_id FROM sessions WHERE id=?", (session_id,)
        )
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        if row["user_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Forbidden")

        cur = await db.execute(
            """
            SELECT cr.*
            FROM code_reviews cr
            JOIN submissions s ON s.id = cr.submission_id
            WHERE s.session_id=?
            ORDER BY cr.created_at DESC
            LIMIT 1
            """,
            (session_id,),
        )
        review_row = await cur.fetchone()
        if not review_row:
            raise HTTPException(status_code=404, detail="No review found for this session")

        review = dict(review_row)
        for field in ("edge_cases_missed", "code_quality_issues", "improvement_suggestions"):
            review[field] = json.loads(review[field])

    return review


@router.get("/{session_id}/debug")
async def session_debug(session_id: int, user: dict = Depends(get_current_user)):
    """Diagnostic endpoint: returns session row, submissions, and progress records for debugging."""
    user_id = user["user_id"]
    async with get_db() as db:
        cur = await db.execute("SELECT * FROM sessions WHERE id=?", (session_id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        session = dict(row)
        if session["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        cur = await db.execute("SELECT COUNT(*) as cnt FROM submissions WHERE session_id=?", (session_id,))
        subs_count = (await cur.fetchone())["cnt"]

        cur = await db.execute(
            "SELECT s.*, cr.correctness_score, cr.complexity_verdict FROM submissions s LEFT JOIN code_reviews cr ON cr.submission_id=s.id WHERE s.session_id=? ORDER BY s.attempt_number DESC LIMIT 1",
            (session_id,),
        )
        last_sub = await cur.fetchone()
        last_sub = dict(last_sub) if last_sub else None

        cur = await db.execute("SELECT COUNT(*) as cnt FROM progress_records WHERE session_id=?", (session_id,))
        progress_count = (await cur.fetchone())["cnt"]

        cur = await db.execute("SELECT * FROM progress_records WHERE session_id=? ORDER BY created_at DESC LIMIT 1", (session_id,))
        progress_row = await cur.fetchone()
        progress_row = dict(progress_row) if progress_row else None

    return {
        "session": session,
        "submissions_count": subs_count,
        "last_submission": last_sub,
        "progress_records_count": progress_count,
        "last_progress_record": progress_row,
    }
