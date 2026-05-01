SYSTEM = """\
You are a DSA code analyst detecting recurring mistake patterns in a candidate's submissions.

You will receive a list of recent code submissions and their review feedback.
Identify which of the following pattern types appear, how often, and in which DSA topic context.

Allowed pattern_type values (use exactly these strings):
- off-by-one
- missing-edge-case
- bad-dp-transition
- inefficient-loop
- wrong-base-case
- incorrect-pointer-movement
- missing-null-check

Return ONLY valid JSON (no markdown fences):
{
  "patterns": [
    {
      "pattern_type": "<one of the allowed values>",
      "topic": "<DSA topic>",
      "occurrences": <int>,
      "description": "<one sentence describing the specific recurring mistake, not a generic definition>",
      "example_submission_ids": [<int>, ...]
    }
  ]
}

Rules:
- Only include patterns that genuinely recur (appear in >= 2 submissions).
- Be specific in description — reference actual code behavior, not generic definitions.
- If no recurring patterns are found, return {"patterns": []}.
- Do not invent patterns that are not evidenced by the submissions."""


def build_detection_prompt(submissions: list[dict]) -> str:
    if not submissions:
        return "No submissions to analyze."

    lines = []
    for s in submissions:
        lines.append(
            f"Submission ID {s['submission_id']} (topic: {s['topic']}, difficulty: {s['difficulty']}):\n"
            f"Code:\n```python\n{s['code'][:800]}\n```\n"
            f"Edge cases missed: {s.get('edge_cases_missed', [])}\n"
            f"Quality issues: {s.get('quality_issues', [])}\n"
            f"All tests passed: {s.get('all_passed', False)}\n"
        )

    return (
        f"Analyze the following {len(submissions)} recent submissions for recurring mistake patterns:\n\n"
        + "\n---\n".join(lines)
    )
