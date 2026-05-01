"""
Pattern Detection Agent.

Two-pass design:
  Pass 1 — regex/heuristic pre-filter on raw code strings (fast, cheap).
  Pass 2 — LLM semantic pass for contextual patterns the regex can't catch.

Results are merged, deduplicated, and upserted into pattern_detections.
"""
import json
import re

import aiosqlite

from backend.models.schemas import PatternSummary, Severity
from backend.prompts.pattern_detection import SYSTEM, build_detection_prompt
from backend.services.llm import chat

# ---------------------------------------------------------------------------
# Regex heuristics for fast pre-filtering
# ---------------------------------------------------------------------------

_HEURISTICS: list[tuple[str, str, str]] = [
    # (pattern_type, description, regex)
    ("off-by-one",
     "Loop bound uses < len when <= len may be needed, or vice versa",
     r"\bfor\b.+\brange\b\s*\(\s*\d*\s*,?\s*len\s*\([^)]+\)\s*[-+]\s*1\s*\)"),

    ("off-by-one",
     "Direct index access without bounds check near len()",
     r"\[\s*len\s*\([^)]+\)\s*[-+]\s*\d+\s*\]"),

    ("missing-null-check",
     "Attribute access on a variable that could be None without a prior None check",
     r"(?<!\bif\b.{0,30})\b(\w+)\s*\.\s*\w+\s*(?!\s*is\s+None)"),

    ("inefficient-loop",
     "Nested loop over the same collection suggesting O(n^2) where better is possible",
     r"for\s+\w+\s+in\s+(\w+).+\n.{0,20}for\s+\w+\s+in\s+\1"),

    ("wrong-base-case",
     "Recursive function missing a base case or base case placed after recursive call",
     r"def\s+\w+\s*\([^)]*\):\s*\n(?!\s*(if|return))"),
]

_SEVERITY_MAP = {1: "low", 2: "medium", 3: "high"}


def _severity(count: int) -> Severity:
    if count >= 4:
        return "high"
    if count >= 2:
        return "medium"
    return "low"


def _regex_pass(submissions: list[dict]) -> list[dict]:
    """Return list of {pattern_type, topic, submission_id, description} hits."""
    hits = []
    for s in submissions:
        code = s.get("code", "")
        for pattern_type, description, regex in _HEURISTICS:
            if re.search(regex, code, re.MULTILINE | re.DOTALL):
                hits.append({
                    "pattern_type": pattern_type,
                    "topic": s["topic"],
                    "submission_id": s["submission_id"],
                    "description": description,
                })
    return hits


def _merge(regex_hits: list[dict], llm_patterns: list[dict]) -> list[dict]:
    """
    Merge regex hits and LLM patterns.
    Key = (pattern_type, topic). Combine occurrence counts and submission IDs.
    """
    merged: dict[tuple, dict] = {}

    for h in regex_hits:
        key = (h["pattern_type"], h["topic"])
        if key not in merged:
            merged[key] = {
                "pattern_type": h["pattern_type"],
                "topic": h["topic"],
                "occurrences": 0,
                "description": h["description"],
                "example_submission_ids": [],
            }
        merged[key]["occurrences"] += 1
        sid = h["submission_id"]
        if sid not in merged[key]["example_submission_ids"]:
            merged[key]["example_submission_ids"].append(sid)

    for p in llm_patterns:
        key = (p["pattern_type"], p["topic"])
        if key not in merged:
            merged[key] = {
                "pattern_type": p["pattern_type"],
                "topic": p["topic"],
                "occurrences": p.get("occurrences", 1),
                "description": p.get("description", ""),
                "example_submission_ids": p.get("example_submission_ids", []),
            }
        else:
            # LLM confirms what regex found — boost occurrence count
            merged[key]["occurrences"] += p.get("occurrences", 1)
            for sid in p.get("example_submission_ids", []):
                if sid not in merged[key]["example_submission_ids"]:
                    merged[key]["example_submission_ids"].append(sid)
            if p.get("description"):
                merged[key]["description"] = p["description"]

    return list(merged.values())


async def run(
    db: aiosqlite.Connection,
    user_id: int,
    scope: str = "recent",
    recent_limit: int = 20,
) -> PatternSummary:
    """
    Analyse recent submissions, upsert pattern_detections, return PatternSummary.
    scope: "recent" | "all_time"
    """
    limit_clause = f"LIMIT {recent_limit}" if scope == "recent" else ""

    cur = await db.execute(
        f"""
        SELECT
            s.id as submission_id,
            s.code,
            s.all_passed,
            p.topic,
            p.difficulty,
            cr.edge_cases_missed,
            cr.code_quality_issues
        FROM submissions s
        JOIN problems p ON p.id = s.problem_id
        LEFT JOIN code_reviews cr ON cr.submission_id = s.id
        WHERE s.user_id = ?
        ORDER BY s.submitted_at DESC
        {limit_clause}
        """,
        (user_id,),
    )
    rows = await cur.fetchall()

    if not rows:
        return PatternSummary(weak_topics=[], dominant_patterns=[])

    submissions = []
    for r in rows:
        submissions.append({
            "submission_id": r["submission_id"],
            "code": r["code"],
            "all_passed": bool(r["all_passed"]),
            "topic": r["topic"],
            "difficulty": r["difficulty"],
            "edge_cases_missed": json.loads(r["edge_cases_missed"] or "[]"),
            "quality_issues": json.loads(r["code_quality_issues"] or "[]"),
        })

    # Pass 1: regex
    regex_hits = _regex_pass(submissions)

    # Pass 2: LLM (only if we have enough data to make it worthwhile)
    llm_patterns: list[dict] = []
    if len(submissions) >= 2:
        try:
            raw = chat(
                system=SYSTEM,
                user=build_detection_prompt(submissions),
                max_tokens=500,
                temperature=0.2,
            )
            raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            llm_patterns = json.loads(raw).get("patterns", [])
        except Exception:
            pass

    all_patterns = _merge(regex_hits, llm_patterns)

    # Upsert into pattern_detections
    for p in all_patterns:
        sids = json.dumps(p["example_submission_ids"][:5])
        severity = _severity(p["occurrences"])
        await db.execute(
            """
            INSERT INTO pattern_detections
                (user_id, pattern_type, topic, occurrence_count, severity,
                 example_submission_ids, last_seen_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(user_id, pattern_type, topic) DO UPDATE SET
                occurrence_count = occurrence_count + excluded.occurrence_count,
                severity = excluded.severity,
                example_submission_ids = excluded.example_submission_ids,
                last_seen_at = datetime('now')
            """,
            (user_id, p["pattern_type"], p["topic"], p["occurrences"], severity, sids),
        )
    await db.commit()

    # Build PatternSummary for downstream agents
    cur = await db.execute(
        """
        SELECT pattern_type FROM pattern_detections
        WHERE user_id = ?
        ORDER BY occurrence_count DESC LIMIT 5
        """,
        (user_id,),
    )
    dominant = [r["pattern_type"] for r in await cur.fetchall()]

    cur = await db.execute(
        """
        SELECT topic FROM progress_records
        WHERE user_id = ?
        GROUP BY topic
        HAVING CAST(SUM(solved) AS REAL) / COUNT(*) < 0.5 AND COUNT(*) >= 2
        """,
        (user_id,),
    )
    weak = [r["topic"] for r in await cur.fetchall()]

    return PatternSummary(weak_topics=weak, dominant_patterns=dominant)
