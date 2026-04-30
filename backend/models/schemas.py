from __future__ import annotations
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared enums / literals
# ---------------------------------------------------------------------------

Difficulty = Literal["easy", "medium", "hard"]
Topic = Literal[
    "arrays", "strings", "linked-lists", "stack-queue",
    "binary-search", "sliding-window", "trees", "graphs",
    "dynamic-programming", "heaps", "tries", "backtracking",
]
SessionPhase = Literal[
    "problem_presentation", "clarification", "brute_force",
    "optimization", "coding", "code_review", "wrap_up",
]
SessionStatus = Literal["active", "completed", "abandoned"]
ComplexityVerdict = Literal["optimal", "suboptimal", "incorrect", "unknown"]
PatternType = Literal[
    "off-by-one", "missing-edge-case", "bad-dp-transition",
    "inefficient-loop", "wrong-base-case",
    "incorrect-pointer-movement", "missing-null-check",
]
Severity = Literal["low", "medium", "high"]


# ---------------------------------------------------------------------------
# Problem dataset models
# ---------------------------------------------------------------------------

class ProblemTestCase(BaseModel):
    input: dict[str, Any]
    expected_output: Any
    is_hidden: bool = False
    edge_case_label: str = ""


class ProblemExample(BaseModel):
    input: str
    output: str
    explanation: str = ""


class ProblemRecord(BaseModel):
    id: int
    slug: str
    title: str
    topic: Topic
    difficulty: Difficulty
    description: str
    function_name: str
    constraints: list[str]
    examples: list[ProblemExample]
    test_cases: list[ProblemTestCase]
    brute_force_hint: str
    optimal_hint: str
    optimal_time_complexity: str
    optimal_space_complexity: str
    follow_up_questions: list[str]
    source_tags: list[str]


# ---------------------------------------------------------------------------
# Auth models
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: str
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    token: str
    user_id: int
    username: str


# ---------------------------------------------------------------------------
# Session models
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SessionStartResponse(BaseModel):
    session_id: int
    problem: ProblemRecord
    phase: SessionPhase
    opening_message: str


class MessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    role: Literal["assistant"]
    content: str
    phase: SessionPhase
    should_show_code_editor: bool
    session_complete: bool


class SubmitCodeRequest(BaseModel):
    code: str
    language: str = "python"


class TestCaseResult(BaseModel):
    index: int
    passed: bool
    edge_case_label: str = ""
    error: str = ""


class SubmitCodeResponse(BaseModel):
    submission_id: int
    test_cases_passed: int
    test_cases_total: int
    all_passed: bool
    test_case_results: list[TestCaseResult]
    review: CodeReviewOutput
    interviewer_follow_up: str


# ---------------------------------------------------------------------------
# Sandbox models
# ---------------------------------------------------------------------------

class SandboxResult(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    runtime_ms: int
    test_cases_passed: int
    test_cases_total: int
    all_passed: bool
    test_case_results: list[TestCaseResult]
    failed_test_case: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Code review models
# ---------------------------------------------------------------------------

class CodeQualityIssue(BaseModel):
    type: str
    line: int | None = None
    description: str


class CodeReviewOutput(BaseModel):
    correctness_score: float
    detected_time_complexity: str
    detected_space_complexity: str
    complexity_verdict: ComplexityVerdict
    edge_cases_missed: list[str]
    code_quality_issues: list[CodeQualityIssue]
    improvement_suggestions: list[str]
    overall_feedback: str
    patterns_flagged: list[PatternType]


# ---------------------------------------------------------------------------
# Pattern detection models
# ---------------------------------------------------------------------------

class DetectedPattern(BaseModel):
    pattern_type: PatternType
    topic: Topic
    occurrences: int
    severity: Severity
    description: str
    example_submission_ids: list[int]


class PatternDetectionOutput(BaseModel):
    user_id: int
    patterns: list[DetectedPattern]
    summary_for_selector: PatternSummary


class PatternSummary(BaseModel):
    weak_topics: list[Topic]
    dominant_patterns: list[PatternType]


# Fix forward reference
PatternDetectionOutput.model_rebuild()


# ---------------------------------------------------------------------------
# Problem selector models
# ---------------------------------------------------------------------------

class TopicCoverage(BaseModel):
    topic: Topic
    attempted: int
    solved: int


class ProblemSelectorInput(BaseModel):
    user_id: int
    pattern_summary: PatternSummary
    solved_problem_ids: list[int]
    topic_coverage: dict[str, int]
    current_difficulty: Difficulty
    prefer_topic: Topic | None = None


class ProblemSelectorOutput(BaseModel):
    selected_problem_id: int
    selection_rationale: str
    topic: Topic
    difficulty: Difficulty


# ---------------------------------------------------------------------------
# Interview simulation models
# ---------------------------------------------------------------------------

class InterviewSimulationInput(BaseModel):
    session_id: int
    problem: ProblemRecord
    current_phase: SessionPhase
    conversation_history: list[ChatMessage]
    user_message: str
    pattern_summary: PatternSummary


class InterviewSimulationOutput(BaseModel):
    interviewer_response: str
    next_phase: SessionPhase
    phase_transition_reason: str
    should_request_code: bool
    session_complete: bool


# ---------------------------------------------------------------------------
# Progress tracker models
# ---------------------------------------------------------------------------

class TopicStats(BaseModel):
    attempted: int
    solved: int
    success_rate: float


class LearningPath(BaseModel):
    next_recommended_topics: list[Topic]
    suggested_difficulty: Difficulty
    milestone: str
    focus_areas: list[str]


class ProgressTrackerOutput(BaseModel):
    progress_record_id: int
    updated_stats: ProgressStats
    learning_path: LearningPath


class ProgressStats(BaseModel):
    total_sessions: int
    total_solved: int
    overall_success_rate: float
    topic_stats: dict[str, TopicStats]


# Fix forward reference
ProgressTrackerOutput.model_rebuild()


# ---------------------------------------------------------------------------
# Inter-agent communication envelope
# ---------------------------------------------------------------------------

class AgentEnvelope(BaseModel):
    agent: str
    action: str
    session_id: int | None = None
    user_id: int
    payload: dict[str, Any]


# ---------------------------------------------------------------------------
# Progress API responses
# ---------------------------------------------------------------------------

class UserProgressResponse(BaseModel):
    total_sessions: int
    total_solved: int
    overall_success_rate: float
    topic_stats: dict[str, TopicStats]
    recent_sessions: list[RecentSession]


class RecentSession(BaseModel):
    session_id: int
    problem_title: str
    topic: Topic
    difficulty: Difficulty
    solved: bool
    started_at: datetime


# Fix forward reference
UserProgressResponse.model_rebuild()


class SessionEndResponse(BaseModel):
    session_summary: SessionSummary
    learning_path: LearningPath


class SessionSummary(BaseModel):
    session_id: int
    problem_title: str
    duration_seconds: int
    solved: bool
    attempts: int
    final_correctness_score: float
    complexity_verdict: ComplexityVerdict
    patterns_triggered: list[PatternType]
