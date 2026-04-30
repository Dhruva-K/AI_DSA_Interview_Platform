"""
Code Review Agent.

Two LLM calls:
  1. Complexity analysis (cheap, low-temp, deterministic output).
  2. Quality + feedback (richer, uses complexity result as input).

correctness_score and patterns_flagged are computed deterministically — never via LLM.
"""
import json

from backend.models.schemas import (
    CodeQualityIssue,
    CodeReviewOutput,
    ComplexityVerdict,
    PatternType,
    ProblemRecord,
    SandboxResult,
)
from backend.prompts.code_review_complexity import (
    SYSTEM as COMPLEXITY_SYSTEM,
    build_complexity_prompt,
)
from backend.prompts.code_review_quality import (
    SYSTEM as QUALITY_SYSTEM,
    build_quality_prompt,
)
from backend.services.llm import MODEL, get_client

# Which edge-case keywords map to which pattern types
_EDGE_CASE_PATTERN_MAP: dict[str, PatternType] = {
    "empty":          "missing-edge-case",
    "null":           "missing-null-check",
    "none":           "missing-null-check",
    "single":         "missing-edge-case",
    "boundary":       "off-by-one",
    "off-by-one":     "off-by-one",
    "index":          "off-by-one",
    "overflow":       "missing-edge-case",
    "negative":       "missing-edge-case",
    "duplicate":      "missing-edge-case",
    "zero":           "missing-edge-case",
}


def _flag_patterns(edge_cases_missed: list[str]) -> list[PatternType]:
    flagged: set[PatternType] = set()
    for desc in edge_cases_missed:
        lower = desc.lower()
        for keyword, pattern in _EDGE_CASE_PATTERN_MAP.items():
            if keyword in lower:
                flagged.add(pattern)
    return list(flagged)


def _call_complexity(
    code: str,
    constraints: list[str],
    optimal_time: str,
    optimal_space: str,
) -> tuple[str, str, ComplexityVerdict]:
    client = get_client()
    prompt = build_complexity_prompt(code, constraints, optimal_time, optimal_space)
    msg = client.messages.create(
        model=MODEL,
        max_tokens=150,
        temperature=0.1,
        system=COMPLEXITY_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        data = json.loads(msg.content[0].text)
        return (
            data.get("detected_time_complexity", "unknown"),
            data.get("detected_space_complexity", "unknown"),
            data.get("complexity_verdict", "unknown"),
        )
    except (json.JSONDecodeError, KeyError):
        return "unknown", "unknown", "unknown"


def _call_quality(
    problem: ProblemRecord,
    code: str,
    sandbox_result: SandboxResult,
    time_complexity: str,
    space_complexity: str,
    complexity_verdict: str,
) -> tuple[list[str], list[CodeQualityIssue], list[str], str]:
    client = get_client()
    prompt = build_quality_prompt(
        problem_title=problem.title,
        problem_description=problem.description,
        code=code,
        sandbox_result=sandbox_result.model_dump(),
        time_complexity=time_complexity,
        space_complexity=space_complexity,
        complexity_verdict=complexity_verdict,
    )
    msg = client.messages.create(
        model=MODEL,
        max_tokens=600,
        temperature=0.3,
        system=QUALITY_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        data = json.loads(msg.content[0].text)
        issues = [
            CodeQualityIssue(**i) if isinstance(i, dict) else CodeQualityIssue(type="logic", description=str(i))
            for i in data.get("code_quality_issues", [])
        ]
        return (
            data.get("edge_cases_missed", []),
            issues,
            data.get("improvement_suggestions", []),
            data.get("overall_feedback", ""),
        )
    except (json.JSONDecodeError, KeyError):
        return [], [], [], "Review could not be generated."


def run(
    problem: ProblemRecord,
    code: str,
    sandbox_result: SandboxResult,
) -> CodeReviewOutput:
    correctness_score = (
        sandbox_result.test_cases_passed / sandbox_result.test_cases_total
        if sandbox_result.test_cases_total > 0
        else 0.0
    )

    # LLM call 1: complexity
    time_c, space_c, verdict = _call_complexity(
        code,
        problem.constraints,
        problem.optimal_time_complexity,
        problem.optimal_space_complexity,
    )

    # LLM call 2: quality + feedback
    edge_cases, quality_issues, suggestions, overall = _call_quality(
        problem, code, sandbox_result, time_c, space_c, verdict
    )

    patterns_flagged = _flag_patterns(edge_cases)

    return CodeReviewOutput(
        correctness_score=round(correctness_score, 3),
        detected_time_complexity=time_c,
        detected_space_complexity=space_c,
        complexity_verdict=verdict,
        edge_cases_missed=edge_cases,
        code_quality_issues=quality_issues,
        improvement_suggestions=suggestions,
        overall_feedback=overall,
        patterns_flagged=patterns_flagged,
    )
