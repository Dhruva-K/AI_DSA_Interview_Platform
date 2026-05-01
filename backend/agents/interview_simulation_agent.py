"""
Interview Simulation Agent.

Phase transitions are driven by a deterministic rules engine.
The LLM only generates the interviewer's conversational response.
"""
from backend.models.schemas import (
    ChatMessage,
    InterviewSimulationInput,
    InterviewSimulationOutput,
    PatternSummary,
    ProblemRecord,
    SessionPhase,
)
from backend.prompts.interview_simulation import (
    NEXT_PHASE,
    PHASE_MAX_TURNS,
    PHASE_TRANSITION_CUES,
    build_system_prompt,
    build_user_turn,
)
from backend.services.llm import chat


def _detect_phase_transition(
    current_phase: SessionPhase,
    user_message: str,
    turn_number: int,
) -> tuple[SessionPhase, str]:
    msg_lower = user_message.lower()
    for cue in PHASE_TRANSITION_CUES.get(current_phase, []):
        if cue in msg_lower:
            next_p = NEXT_PHASE[current_phase]
            if next_p != current_phase:
                return next_p, f"candidate_signalled_{cue.replace(' ', '_')}"

    max_t = PHASE_MAX_TURNS.get(current_phase, 999)
    if max_t > 0 and turn_number >= max_t:
        next_p = NEXT_PHASE[current_phase]
        if next_p != current_phase:
            return next_p, "max_turns_reached"

    return current_phase, ""


def run(inp: InterviewSimulationInput) -> InterviewSimulationOutput:
    phase_turns = sum(1 for m in inp.conversation_history if m.role == "user")

    next_phase, transition_reason = _detect_phase_transition(
        inp.current_phase, inp.user_message, phase_turns
    )

    should_request_code = next_phase == "coding" and inp.current_phase != "coding"
    session_complete = inp.current_phase == "wrap_up" and phase_turns >= 1

    system_prompt = build_system_prompt(
        problem=inp.problem.model_dump(),
        pattern_summary=inp.pattern_summary.model_dump(),
    )
    user_turn_content = build_user_turn(
        current_phase=next_phase,
        user_message=inp.user_message,
        turn_number=phase_turns,
    )

    # Convert stored history to message format (last 12 turns)
    history_messages = [
        {"role": m.role, "content": m.content}
        for m in inp.conversation_history[-12:]
    ]

    response_text = _fallback_response(next_phase)
    try:
        response_text = chat(
            system=system_prompt,
            user=user_turn_content,
            messages=history_messages,
            max_tokens=300,
            temperature=0.6,
        )
    except Exception:
        pass

    return InterviewSimulationOutput(
        interviewer_response=response_text,
        next_phase=next_phase,
        phase_transition_reason=transition_reason,
        should_request_code=should_request_code,
        session_complete=session_complete,
    )


def get_opening_message(problem: ProblemRecord, pattern_summary: PatternSummary) -> str:
    system_prompt = build_system_prompt(
        problem=problem.model_dump(),
        pattern_summary=pattern_summary.model_dump(),
    )
    try:
        return chat(
            system=system_prompt,
            user="[Phase: problem_presentation. Present the problem to the candidate now.]",
            max_tokens=400,
            temperature=0.5,
        )
    except Exception:
        return (
            f"Let's get started. Here's your problem:\n\n"
            f"**{problem.title}**\n\n{problem.description}\n\n"
            "Take a moment to read it and feel free to ask any clarifying questions."
        )


def _fallback_response(phase: SessionPhase) -> str:
    return {
        "problem_presentation": "Here's the problem. Take your time and feel free to ask questions.",
        "clarification":        "Good question. Could you clarify what you mean?",
        "brute_force":          "Walk me through your initial approach.",
        "optimization":         "Can you think of a more efficient solution?",
        "coding":               "Go ahead and code that up.",
        "code_review":          "Let's discuss what you've written. What's the time complexity?",
        "wrap_up":              "Great effort today. That wraps up our session.",
    }.get(phase, "Please continue.")
