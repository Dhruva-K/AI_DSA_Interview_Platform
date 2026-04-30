SYSTEM = """\
You are a DSA interview coach writing personalized, motivating guidance for a learner.
Given the learner's performance stats and mistake patterns, produce exactly 2-4 short, specific,
actionable focus areas AND one brief milestone message.

Return JSON only:
{
  "focus_areas": ["...", "...", "..."],
  "milestone": "..."
}

Rules:
- Focus areas must be concrete actions (e.g. "Practice DP table initialization with pen-and-paper before coding").
- Do not use generic advice like "practice more".
- Milestone should acknowledge progress honestly; if nothing notable happened, return an empty string.
- Return valid JSON with no markdown fences."""


def build_focus_prompt(
    total_sessions: int,
    total_solved: int,
    topic_stats: dict,
    dominant_patterns: list[str],
    recent_outcomes: list[dict],
    suggested_difficulty: str,
) -> str:
    topic_lines = "\n".join(
        f"  {topic}: {stats['solved']}/{stats['attempted']} solved"
        for topic, stats in topic_stats.items()
    )
    recent_lines = "\n".join(
        f"  - {o['topic']} ({o['difficulty']}): {'solved' if o['solved'] else 'not solved'}"
        for o in recent_outcomes[-5:]
    )
    return (
        f"Sessions: {total_sessions}, Solved: {total_solved}\n"
        f"Topic breakdown:\n{topic_lines}\n"
        f"Dominant mistake patterns: {', '.join(dominant_patterns) or 'none'}\n"
        f"Recent sessions:\n{recent_lines}\n"
        f"Suggested next difficulty: {suggested_difficulty}\n"
    )
