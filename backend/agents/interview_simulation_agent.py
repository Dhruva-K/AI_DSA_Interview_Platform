"""
Interview Simulation Agent.

Phase transitions are driven by a deterministic rules engine — the LLM is
never asked to decide when to move to the next phase.
The LLM only generates the interviewer's conversational response within the
current phase's constraints.
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
from backend.services.llm import MODEL, get_client


def _detect_phase_transition(
    current_phase: SessionPhase,
    user_message: str,
    turn_number: int,
) -> tuple[SessionPhase, str]:
    """Return (next_phase, reason). Returns current phase if no transition."""
    msg_lower = user_message.lower()
    cues = PHASE_TRANSITION_CUES.get(current_phase, [])

    # Check keyword cues
    for cue in cues:
        if cue in msg_lower:
            next_p = NEXT_PHASE[current_phase]
            if next_p != current_phase:
                return next_p, f"candidate_signalled_{cue.replace(' ', '_')}"

    # Check turn limit
    max_t = PHASE_MAX_TURNS.get(current_phase, 999)
    if max_t > 0 and turn_number >= max_t:
        next_p = NEXT_PHASE[current_phase]
        if next_p != current_phase:
            return next_p, "max_turns_reached"

    return current_phase, ""


def run(inp: InterviewSimulationInput) -> InterviewSimulationOutput:
    client = get_client()

    # Count turns already spent in the current phase
    phase_turns = sum(
        1 for m in inp.conversation_history
        if m.role == "user"
    )

    # Determine phase transition before generating response
    next_phase, transition_reason = _detect_phase_transition(
        inp.current_phase,
        inp.user_message,
        phase_turns,
    )

    should_request_code = next_phase == "coding" and inp.current_phase != "coding"
    session_complete = inp.current_phase == "wrap_up" and phase_turns >= 1

    # Build messages for the LLM
    system_prompt = build_system_prompt(
        problem=inp.problem.model_dump(),
        pattern_summary=inp.pattern_summary.model_dump(),
    )
    user_turn_content = build_user_turn(
        current_phase=next_phase,  # use next_phase so response fits the new phase
        user_message=inp.user_message,
        turn_number=phase_turns,
    )

    # Convert stored history to Anthropic message format
    messages = []
    for msg in inp.conversation_history[-12:]:  # keep last 12 turns to stay within context
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_turn_content})

    response_text = _fallback_response(next_phase)
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=300,
            temperature=0.6,
            system=system_prompt,
            messages=messages,
        )
        response_text = msg.content[0].text.strip()
    except Exception:
        pass  # keep fallback

    return InterviewSimulationOutput(
        interviewer_response=response_text,
        next_phase=next_phase,
        phase_transition_reason=transition_reason,
        should_request_code=should_request_code,
        session_complete=session_complete,
    )


def get_opening_message(problem: ProblemRecord, pattern_summary: PatternSummary) -> str:
    """Generate the first interviewer message that presents the problem."""
    client = get_client()
    system_prompt = build_system_prompt(
        problem=problem.model_dump(),
        pattern_summary=pattern_summary.model_dump(),
    )
    opening_user = "[Phase: problem_presentation. Present the problem to the candidate now.]"
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=400,
            temperature=0.5,
            system=system_prompt,
            messages=[{"role": "user", "content": opening_user}],
        )
        return msg.content[0].text.strip()
    except Exception:
        return (
            f"Let's get started. Here's your problem:\n\n"
            f"**{problem.title}**\n\n{problem.description}\n\n"
            "Take a moment to read it and feel free to ask any clarifying questions."
        )


def _fallback_response(phase: SessionPhase) -> str:
    return {
        "problem_presentation": "Here's the problem. Take your time and let me know if you have any questions.",
        "clarification":        "Good question. Could you rephrase that so I can answer precisely?",
        "brute_force":          "Walk me through your initial approach — even a simple one is a good start.",
        "optimization":         "Interesting. Can you think of a way to make this more efficient?",
        "coding":               "Go ahead and code that up. Let me know if you have any questions.",
        "code_review":          "Let's discuss what you've written. What's the time complexity?",
        "wrap_up":              "Great effort today. That wraps up our session.",
    }.get(phase, "Please continue.")
