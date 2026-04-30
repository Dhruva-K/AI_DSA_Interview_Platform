"""
Orchestrator — the only module that instantiates and calls agents.
Agents never call each other directly.

Week 3: session start, message handling, code submission, session close.
Week 4: pattern detection agent wired in (stubs below marked TODO).
"""
import asyncio
import json
from datetime import datetime, timezone

import aiosqlite

from backend.agents import (
    code_review_agent,
    interview_simulation_agent,
    problem_selector_agent,
    progress_tracker_agent,
)
from backend.models.schemas import (
    ChatMessage,
    CodeReviewOutput,
    InterviewSimulationInput,
    PatternSummary,
    ProblemRecord,
    ProblemSelectorInput,
    SessionPhase,
    SandboxResult,
    SubmitCodeResponse,
    TestCaseResult,
)
from backend.services.db import get_db
from backend.services.sandbox import run_code

AGENT_TIMEOUT = 30  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_pattern_summary() -> PatternSummary:
    # TODO (Week 4): replace with real Pattern Detection Agent output
    return PatternSummary(weak_topics=[], dominant_patterns=[])


async def _get_problem(db: aiosqlite.Connection, problem_id: int) -> ProblemRecord:
    cur = await db.execute("SELECT * FROM problems WHERE id=?", (problem_id,))
    row = await cur.fetchone()
    if not row:
        raise ValueError(f"Problem {problem_id} not found")
    d = dict(row)
    for field in ("constraints", "examples", "test_cases", "follow_up_questions", "source_tags"):
        d[field] = json.loads(d[field])
    return ProblemRecord(**d)


async def _get_pattern_summary(db: aiosqlite.Connection, user_id: int) -> PatternSummary:
    # TODO (Week 4): call pattern_detection_agent.run() here
    cur = await db.execute(
        """
        SELECT pattern_type, occurrence_count
        FROM pattern_detections
        WHERE user_id=?
        ORDER BY occurrence_count DESC
        LIMIT 5
        """,
        (user_id,),
    )
    rows = await cur.fetchall()
    dominant = [r["pattern_type"] for r in rows]

    cur = await db.execute(
        """
        SELECT topic, SUM(solved) * 1.0 / COUNT(*) as rate
        FROM progress_records
        WHERE user_id=?
        GROUP BY topic
        HAVING rate < 0.5 AND COUNT(*) >= 2
        """,
        (user_id,),
    )
    weak_rows = await cur.fetchall()
    weak = [r["topic"] for r in weak_rows]

    return PatternSummary(weak_topics=weak, dominant_patterns=dominant)


async def _topic_coverage(db: aiosqlite.Connection, user_id: int) -> dict[str, int]:
    cur = await db.execute(
        "SELECT topic, COUNT(*) as cnt FROM progress_records WHERE user_id=? GROUP BY topic",
        (user_id,),
    )
    return {r["topic"]: r["cnt"] for r in await cur.fetchall()}


async def _solved_ids(db: aiosqlite.Connection, user_id: int) -> list[int]:
    cur = await db.execute(
        "SELECT DISTINCT problem_id FROM progress_records WHERE user_id=? AND solved=1",
        (user_id,),
    )
    return [r["problem_id"] for r in await cur.fetchall()]


async def _current_difficulty(db: aiosqlite.Connection, user_id: int) -> str:
    cur = await db.execute(
        "SELECT preferred_difficulty FROM users WHERE id=?", (user_id,)
    )
    row = await cur.fetchone()
    return row["preferred_difficulty"] if row else "medium"


async def _append_message(
    db: aiosqlite.Connection,
    session_id: int,
    role: str,
    content: str,
) -> None:
    cur = await db.execute(
        "SELECT conversation_history FROM sessions WHERE id=?", (session_id,)
    )
    row = await cur.fetchone()
    history = json.loads(row["conversation_history"])
    history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    await db.execute(
        "UPDATE sessions SET conversation_history=? WHERE id=?",
        (json.dumps(history), session_id),
    )
    await db.commit()


async def _get_conversation_history(
    db: aiosqlite.Connection, session_id: int
) -> list[ChatMessage]:
    cur = await db.execute(
        "SELECT conversation_history FROM sessions WHERE id=?", (session_id,)
    )
    row = await cur.fetchone()
    return [ChatMessage(**m) for m in json.loads(row["conversation_history"])]


async def _get_session(db: aiosqlite.Connection, session_id: int) -> dict:
    cur = await db.execute("SELECT * FROM sessions WHERE id=?", (session_id,))
    row = await cur.fetchone()
    if not row:
        raise ValueError(f"Session {session_id} not found")
    return dict(row)


# ---------------------------------------------------------------------------
# Public orchestrator actions
# ---------------------------------------------------------------------------

async def start_session(user_id: int) -> dict:
    """
    Select a problem, create a session row, generate the opening message.
    Returns: {session_id, problem, phase, opening_message}
    """
    async with get_db() as db:
        pattern_summary = await _get_pattern_summary(db, user_id)
        solved = await _solved_ids(db, user_id)
        coverage = await _topic_coverage(db, user_id)
        difficulty = await _current_difficulty(db, user_id)

        selector_input = ProblemSelectorInput(
            user_id=user_id,
            pattern_summary=pattern_summary,
            solved_problem_ids=solved,
            topic_coverage=coverage,
            current_difficulty=difficulty,
        )
        try:
            selector_out = await asyncio.wait_for(
                problem_selector_agent.run(db, selector_input),
                timeout=AGENT_TIMEOUT,
            )
        except asyncio.TimeoutError:
            # Fall back to any easy unsolved problem
            cur = await db.execute(
                "SELECT id FROM problems WHERE difficulty='easy' LIMIT 1"
            )
            row = await cur.fetchone()
            from backend.models.schemas import ProblemSelectorOutput
            selector_out = ProblemSelectorOutput(
                selected_problem_id=row["id"],
                selection_rationale="Fallback selection.",
                topic="arrays",
                difficulty="easy",
            )

        problem = await _get_problem(db, selector_out.selected_problem_id)

        cur = await db.execute(
            "INSERT INTO sessions (user_id, problem_id, status, phase, conversation_history) VALUES (?,?,?,?,?)",
            (user_id, problem.id, "active", "problem_presentation", "[]"),
        )
        await db.commit()
        session_id = cur.lastrowid

    # Generate opening message (outside DB context to avoid long LLM hold)
    opening = interview_simulation_agent.get_opening_message(problem, pattern_summary)

    async with get_db() as db:
        await _append_message(db, session_id, "assistant", opening)
        await db.execute(
            "UPDATE sessions SET phase=? WHERE id=?", ("clarification", session_id)
        )
        await db.commit()

    return {
        "session_id": session_id,
        "problem": problem,
        "phase": "clarification",
        "opening_message": opening,
    }


async def process_message(session_id: int, user_id: int, content: str) -> dict:
    """
    Pass a user message to the Interview Simulation Agent.
    Returns: {response, phase, should_show_code_editor, session_complete}
    """
    async with get_db() as db:
        session = await _get_session(db, session_id)
        if session["user_id"] != user_id:
            raise PermissionError("Session does not belong to this user")
        if session["status"] != "active":
            raise ValueError("Session is not active")

        problem = await _get_problem(db, session["problem_id"])
        history = await _get_conversation_history(db, session_id)
        pattern_summary = await _get_pattern_summary(db, user_id)

        sim_input = InterviewSimulationInput(
            session_id=session_id,
            problem=problem,
            current_phase=session["phase"],
            conversation_history=history,
            user_message=content,
            pattern_summary=pattern_summary,
        )

    try:
        sim_out = await asyncio.wait_for(
            asyncio.to_thread(interview_simulation_agent.run, sim_input),
            timeout=AGENT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        from backend.agents.interview_simulation_agent import _fallback_response
        sim_out = type("FallbackOut", (), {
            "interviewer_response": _fallback_response(sim_input.current_phase),
            "next_phase": sim_input.current_phase,
            "should_request_code": False,
            "session_complete": False,
        })()

    async with get_db() as db:
        await _append_message(db, session_id, "user", content)
        await _append_message(db, session_id, "assistant", sim_out.interviewer_response)
        await db.execute(
            "UPDATE sessions SET phase=? WHERE id=?", (sim_out.next_phase, session_id)
        )
        await db.commit()

    return {
        "role": "assistant",
        "content": sim_out.interviewer_response,
        "phase": sim_out.next_phase,
        "should_show_code_editor": sim_out.should_request_code,
        "session_complete": sim_out.session_complete,
    }


async def submit_code(session_id: int, user_id: int, code: str, language: str) -> dict:
    """
    Run sandbox → Code Review Agent → update DB.
    Returns the full review + interviewer follow-up.
    """
    async with get_db() as db:
        session = await _get_session(db, session_id)
        if session["user_id"] != user_id:
            raise PermissionError("Session does not belong to this user")

        problem = await _get_problem(db, session["problem_id"])

        cur = await db.execute(
            "SELECT COUNT(*) as cnt FROM submissions WHERE session_id=?", (session_id,)
        )
        row = await cur.fetchone()
        attempt_number = row["cnt"] + 1

    # Run sandbox (blocking, in thread pool)
    sandbox_result: SandboxResult = await asyncio.to_thread(
        run_code,
        code,
        problem.function_name,
        problem.test_cases,
    )

    # Persist submission
    async with get_db() as db:
        cur = await db.execute(
            """
            INSERT INTO submissions
                (session_id, user_id, problem_id, code, language, attempt_number,
                 sandbox_stdout, sandbox_stderr, sandbox_exit_code,
                 test_cases_passed, test_cases_total, all_passed, runtime_ms)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                session_id, user_id, problem.id, code, language, attempt_number,
                sandbox_result.stdout, sandbox_result.stderr, sandbox_result.exit_code,
                sandbox_result.test_cases_passed, sandbox_result.test_cases_total,
                int(sandbox_result.all_passed), sandbox_result.runtime_ms,
            ),
        )
        await db.commit()
        submission_id = cur.lastrowid

    # Code Review Agent (LLM calls, in thread pool)
    try:
        review: CodeReviewOutput = await asyncio.wait_for(
            asyncio.to_thread(code_review_agent.run, problem, code, sandbox_result),
            timeout=AGENT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        review = CodeReviewOutput(
            correctness_score=round(
                sandbox_result.test_cases_passed / max(sandbox_result.test_cases_total, 1), 3
            ),
            detected_time_complexity="unknown",
            detected_space_complexity="unknown",
            complexity_verdict="unknown",
            edge_cases_missed=[],
            code_quality_issues=[],
            improvement_suggestions=[],
            overall_feedback="Review timed out. Check your solution manually.",
            patterns_flagged=[],
        )

    # Persist code review
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO code_reviews
                (submission_id, correctness_score, detected_time_complexity,
                 detected_space_complexity, complexity_verdict, edge_cases_missed,
                 code_quality_issues, improvement_suggestions, overall_feedback)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                submission_id, review.correctness_score,
                review.detected_time_complexity, review.detected_space_complexity,
                review.complexity_verdict,
                json.dumps(review.edge_cases_missed),
                json.dumps([i.model_dump() for i in review.code_quality_issues]),
                json.dumps(review.improvement_suggestions),
                review.overall_feedback,
            ),
        )

        new_phase: SessionPhase = "code_review"
        if sandbox_result.all_passed:
            new_phase = "wrap_up"

        await db.execute(
            "UPDATE sessions SET phase=? WHERE id=?", (new_phase, session_id)
        )
        await db.commit()

    # Interviewer follow-up after review
    async with get_db() as db:
        session = await _get_session(db, session_id)
        problem = await _get_problem(db, session["problem_id"])
        history = await _get_conversation_history(db, session_id)
        pattern_summary = await _get_pattern_summary(db, user_id)

    follow_up_content = (
        "All test cases passed! Well done. " + review.overall_feedback
        if sandbox_result.all_passed
        else f"{review.overall_feedback} Would you like to revise your solution?"
    )

    try:
        sim_input = InterviewSimulationInput(
            session_id=session_id,
            problem=problem,
            current_phase=new_phase,
            conversation_history=history,
            user_message=f"[System: Code submitted. {sandbox_result.test_cases_passed}/{sandbox_result.test_cases_total} tests passed.]",
            pattern_summary=pattern_summary,
        )
        sim_out = await asyncio.wait_for(
            asyncio.to_thread(interview_simulation_agent.run, sim_input),
            timeout=AGENT_TIMEOUT,
        )
        follow_up_content = sim_out.interviewer_response
    except Exception:
        pass

    async with get_db() as db:
        await _append_message(db, session_id, "assistant", follow_up_content)

    return {
        "submission_id": submission_id,
        "test_cases_passed": sandbox_result.test_cases_passed,
        "test_cases_total": sandbox_result.test_cases_total,
        "all_passed": sandbox_result.all_passed,
        "test_case_results": [r.model_dump() for r in sandbox_result.test_case_results],
        "review": review.model_dump(),
        "interviewer_follow_up": follow_up_content,
    }


async def end_session(session_id: int, user_id: int) -> dict:
    """
    Close the session and run the Progress Tracker Agent.
    Returns: {session_summary, learning_path}
    """
    async with get_db() as db:
        session = await _get_session(db, session_id)
        if session["user_id"] != user_id:
            raise PermissionError("Session does not belong to this user")
        if session["status"] == "completed":
            raise ValueError("Session already completed")

        problem = await _get_problem(db, session["problem_id"])

        # Get the latest submission for this session
        cur = await db.execute(
            """
            SELECT s.*, cr.correctness_score, cr.complexity_verdict, cr.edge_cases_missed
            FROM submissions s
            LEFT JOIN code_reviews cr ON cr.submission_id = s.id
            WHERE s.session_id=?
            ORDER BY s.attempt_number DESC
            LIMIT 1
            """,
            (session_id,),
        )
        last_sub = await cur.fetchone()
        last_sub = dict(last_sub) if last_sub else {}

        started_at = datetime.fromisoformat(session["started_at"].replace("Z", "+00:00"))
        duration = int((datetime.now(timezone.utc) - started_at).total_seconds())

        solved = bool(last_sub.get("all_passed", False))
        attempts = last_sub.get("attempt_number", 0)
        correctness = last_sub.get("correctness_score", 0.0) or 0.0
        complexity_verdict = last_sub.get("complexity_verdict", "") or ""
        patterns_triggered = json.loads(last_sub.get("edge_cases_missed", "[]") or "[]")

        tracker_out = await asyncio.wait_for(
            progress_tracker_agent.run(
                db=db,
                user_id=user_id,
                session_id=session_id,
                problem_id=problem.id,
                topic=problem.topic,
                difficulty=problem.difficulty,
                solved=solved,
                attempts_count=attempts,
                time_to_solve_seconds=duration,
                final_correctness_score=correctness,
                complexity_verdict=complexity_verdict,
                patterns_triggered=patterns_triggered,
                learning_path_snapshot={},
            ),
            timeout=AGENT_TIMEOUT,
        )

    return {
        "session_summary": {
            "session_id": session_id,
            "problem_title": problem.title,
            "duration_seconds": duration,
            "solved": solved,
            "attempts": attempts,
            "final_correctness_score": correctness,
            "complexity_verdict": complexity_verdict,
            "patterns_triggered": patterns_triggered,
        },
        "learning_path": tracker_out.learning_path.model_dump(),
    }
