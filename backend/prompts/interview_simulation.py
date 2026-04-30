from backend.models.schemas import SessionPhase

# This system prompt is static per-session and should be cached
SYSTEM_TEMPLATE = """\
You are a professional technical interviewer at a top software company conducting a live DSA interview.

PROBLEM YOU ARE INTERVIEWING ON:
Title: {title}
Description: {description}
Examples: {examples}
Constraints: {constraints}
Optimal approach (known only to you, never reveal): {optimal_hint}
Optimal time complexity: {optimal_time}
Follow-up questions available: {follow_ups}

YOUR BEHAVIOR RULES:
- Stay strictly in character as an interviewer. Never break the fourth wall.
- Ask ONE question at a time. Wait for the candidate's response before proceeding.
- Do NOT give away the solution or optimal approach. Use Socratic nudging only.
- Be professional, encouraging but honest. Acknowledge good reasoning.
- Keep responses concise — 1 to 4 sentences.
- Current interview pressure profile: {pressure_profile}

PHASE-SPECIFIC INSTRUCTIONS:
- problem_presentation: Read out the problem clearly. Invite questions.
- clarification: Answer clarifying questions accurately. Keep answers brief.
- brute_force: Prompt the candidate to describe their initial approach. Do not guide toward optimal yet.
- optimization: Ask if they can do better. Hint at constraints if stuck after 2 failed attempts.
- coding: Say "Go ahead and code that up." Monitor silently. Answer syntax questions only.
- code_review: Discuss the submitted solution. Ask about edge cases and complexity.
- wrap_up: Summarize the session briefly. End professionally."""


PHASE_TRANSITION_CUES = {
    "clarification": [
        "i understand", "i think i get it", "that makes sense",
        "no more questions", "i'm ready", "let me think about",
    ],
    "brute_force": [
        "brute force", "naive approach", "o(n^2)", "o(n2)", "nested loop",
        "check every", "try all",
    ],
    "optimization": [
        "hash map", "hash table", "two pointer", "sliding window",
        "binary search", "dynamic programming", "o(n)", "o(log n)",
        "optimize", "better approach", "more efficient",
    ],
    "coding": [
        "let me code", "i'll implement", "let me write", "start coding",
        "write the code",
    ],
}

# How many turns each phase can last before the interviewer nudges forward
PHASE_MAX_TURNS = {
    "problem_presentation": 1,
    "clarification": 5,
    "brute_force": 4,
    "optimization": 5,
    "coding": 0,   # coding phase ends only on code submission
    "code_review": 4,
    "wrap_up": 2,
}

NEXT_PHASE: dict[str, SessionPhase] = {
    "problem_presentation": "clarification",
    "clarification":        "brute_force",
    "brute_force":          "optimization",
    "optimization":         "coding",
    "coding":               "code_review",
    "code_review":          "wrap_up",
    "wrap_up":              "wrap_up",
}


def build_system_prompt(problem: dict, pattern_summary: dict) -> str:
    dominant = pattern_summary.get("dominant_patterns", [])
    if "missing-edge-case" in dominant:
        pressure = "Probe edge cases aggressively — candidate has a history of missing them."
    elif "bad-dp-transition" in dominant:
        pressure = "Push the candidate to explain their recurrence relation step by step."
    elif "off-by-one" in dominant:
        pressure = "Ask the candidate to trace through boundary conditions carefully."
    else:
        pressure = "Standard — be encouraging and give reasonable thinking time."

    examples_str = "; ".join(
        f"Input {e['input']} → Output {e['output']}"
        for e in problem.get("examples", [])[:2]
    )

    return SYSTEM_TEMPLATE.format(
        title=problem["title"],
        description=problem["description"],
        examples=examples_str or "See problem statement.",
        constraints=", ".join(problem.get("constraints", [])),
        optimal_hint=problem.get("optimal_hint", ""),
        optimal_time=problem.get("optimal_time_complexity", ""),
        follow_ups=", ".join(problem.get("follow_up_questions", [])),
        pressure_profile=pressure,
    )


def build_user_turn(
    current_phase: SessionPhase,
    user_message: str,
    turn_number: int,
) -> str:
    phase_context = {
        "problem_presentation": "Present the problem clearly.",
        "clarification":        "Answer the candidate's clarifying question.",
        "brute_force":          "Probe the candidate's initial approach.",
        "optimization":         "Push the candidate toward a more efficient solution.",
        "coding":               "The candidate is coding. Stay in standby unless they ask something.",
        "code_review":          "Discuss the solution the candidate just submitted.",
        "wrap_up":              "Wrap up the interview professionally.",
    }.get(current_phase, "")

    nudge = ""
    max_t = PHASE_MAX_TURNS.get(current_phase, 5)
    if max_t > 0 and turn_number >= max_t:
        nudge = " (The candidate has been in this phase a while — gently move things forward.)"

    return f"[Phase: {current_phase}. {phase_context}{nudge}]\nCandidate: {user_message}"
