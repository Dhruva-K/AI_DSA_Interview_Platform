from backend.models.schemas import Difficulty, Topic


SYSTEM = """\
You are a DSA interview coach selecting the most pedagogically effective next problem for a learner.
You will receive the learner's weak topics, dominant mistake patterns, and a short list of candidate problems.
Write a single concise sentence (max 25 words) explaining why the top candidate is the best choice right now.
Return only the rationale sentence — no preamble, no JSON."""


def build_rationale_prompt(
    weak_topics: list[Topic],
    dominant_patterns: list[str],
    candidates: list[dict],
    chosen_slug: str,
) -> str:
    candidate_lines = "\n".join(
        f"- {c['title']} ({c['topic']}, {c['difficulty']})" for c in candidates
    )
    return (
        f"Weak topics: {', '.join(weak_topics) or 'none identified yet'}\n"
        f"Dominant mistake patterns: {', '.join(dominant_patterns) or 'none identified yet'}\n"
        f"Candidate problems:\n{candidate_lines}\n"
        f"Selected problem: {chosen_slug}\n"
        f"Rationale:"
    )
