SYSTEM = """\
You are a senior software engineer conducting a thorough code review after an interview submission.
You will receive the problem statement, the candidate's code, sandbox execution results, and complexity analysis.

Return ONLY valid JSON (no markdown fences):
{
  "edge_cases_missed": ["<description>", ...],
  "code_quality_issues": [
    {"type": "<naming|logic|style|redundancy>", "line": <int or null>, "description": "<short description>"}
  ],
  "improvement_suggestions": ["<actionable suggestion>", ...],
  "overall_feedback": "<2-3 sentences of honest, constructive feedback>"
}

Rules:
- Be specific — reference actual lines or variable names.
- edge_cases_missed should only list cases the code genuinely does not handle.
- Do not invent issues that don't exist.
- overall_feedback should acknowledge what is correct before pointing out issues."""


def build_quality_prompt(
    problem_title: str,
    problem_description: str,
    code: str,
    sandbox_result: dict,
    time_complexity: str,
    space_complexity: str,
    complexity_verdict: str,
) -> str:
    failed = sandbox_result.get("failed_test_case")
    failed_str = (
        f"First failing case — input: {failed['input']}, error: {failed['error']}"
        if failed
        else "All visible test cases passed."
    )
    return (
        f"Problem: {problem_title}\n"
        f"Description: {problem_description}\n\n"
        f"Candidate's code:\n```python\n{code}\n```\n\n"
        f"Execution result: {sandbox_result['test_cases_passed']}/{sandbox_result['test_cases_total']} test cases passed.\n"
        f"{failed_str}\n"
        f"Detected complexity: {time_complexity} time, {space_complexity} space ({complexity_verdict}).\n"
    )
