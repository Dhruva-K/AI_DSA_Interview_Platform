SYSTEM = """\
You are a senior engineer analyzing algorithm complexity.
Given the code and problem constraints, return ONLY valid JSON (no markdown fences):
{
  "detected_time_complexity": "<Big-O string>",
  "detected_space_complexity": "<Big-O string>",
  "complexity_verdict": "optimal" | "suboptimal" | "incorrect"
}
Base the verdict solely on the provided optimal complexities.
Do not explain — return JSON only."""


def build_complexity_prompt(
    code: str,
    constraints: list[str],
    optimal_time: str,
    optimal_space: str,
) -> str:
    return (
        f"Optimal time complexity: {optimal_time}\n"
        f"Optimal space complexity: {optimal_space}\n"
        f"Problem constraints: {'; '.join(constraints)}\n\n"
        f"Code:\n```python\n{code}\n```"
    )
