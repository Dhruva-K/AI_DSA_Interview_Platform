import os
import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "backend/data/db.sqlite3")

Path(DATABASE_URL).parent.mkdir(parents=True, exist_ok=True)

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    username         TEXT    NOT NULL UNIQUE,
    email            TEXT    NOT NULL UNIQUE,
    password_hash    TEXT    NOT NULL,
    preferred_difficulty TEXT NOT NULL DEFAULT 'medium',
    created_at       DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at       DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS problems (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    slug                      TEXT    NOT NULL UNIQUE,
    title                     TEXT    NOT NULL,
    topic                     TEXT    NOT NULL,
    difficulty                TEXT    NOT NULL,
    description               TEXT    NOT NULL,
    function_name             TEXT    NOT NULL,
    constraints               TEXT    NOT NULL DEFAULT '[]',
    examples                  TEXT    NOT NULL DEFAULT '[]',
    test_cases                TEXT    NOT NULL DEFAULT '[]',
    brute_force_hint          TEXT    NOT NULL DEFAULT '',
    optimal_hint              TEXT    NOT NULL DEFAULT '',
    optimal_time_complexity   TEXT    NOT NULL DEFAULT '',
    optimal_space_complexity  TEXT    NOT NULL DEFAULT '',
    follow_up_questions       TEXT    NOT NULL DEFAULT '[]',
    source_tags               TEXT    NOT NULL DEFAULT '[]',
    created_at                DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id              INTEGER NOT NULL REFERENCES users(id),
    problem_id           INTEGER NOT NULL REFERENCES problems(id),
    status               TEXT    NOT NULL DEFAULT 'active',
    phase                TEXT    NOT NULL DEFAULT 'problem_presentation',
    conversation_history TEXT    NOT NULL DEFAULT '[]',
    started_at           DATETIME NOT NULL DEFAULT (datetime('now')),
    ended_at             DATETIME,
    duration_seconds     INTEGER
);

CREATE TABLE IF NOT EXISTS submissions (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id         INTEGER NOT NULL REFERENCES sessions(id),
    user_id            INTEGER NOT NULL REFERENCES users(id),
    problem_id         INTEGER NOT NULL REFERENCES problems(id),
    code               TEXT    NOT NULL,
    language           TEXT    NOT NULL DEFAULT 'python',
    attempt_number     INTEGER NOT NULL DEFAULT 1,
    sandbox_stdout     TEXT    NOT NULL DEFAULT '',
    sandbox_stderr     TEXT    NOT NULL DEFAULT '',
    sandbox_exit_code  INTEGER NOT NULL DEFAULT 0,
    test_cases_passed  INTEGER NOT NULL DEFAULT 0,
    test_cases_total   INTEGER NOT NULL DEFAULT 0,
    all_passed         INTEGER NOT NULL DEFAULT 0,
    runtime_ms         INTEGER NOT NULL DEFAULT 0,
    submitted_at       DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS code_reviews (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id             INTEGER NOT NULL REFERENCES submissions(id),
    correctness_score         REAL    NOT NULL DEFAULT 0.0,
    detected_time_complexity  TEXT    NOT NULL DEFAULT '',
    detected_space_complexity TEXT    NOT NULL DEFAULT '',
    complexity_verdict        TEXT    NOT NULL DEFAULT '',
    edge_cases_missed         TEXT    NOT NULL DEFAULT '[]',
    code_quality_issues       TEXT    NOT NULL DEFAULT '[]',
    improvement_suggestions   TEXT    NOT NULL DEFAULT '[]',
    overall_feedback          TEXT    NOT NULL DEFAULT '',
    llm_raw_response          TEXT    NOT NULL DEFAULT '',
    created_at                DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pattern_detections (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id               INTEGER NOT NULL REFERENCES users(id),
    pattern_type          TEXT    NOT NULL,
    topic                 TEXT    NOT NULL,
    occurrence_count      INTEGER NOT NULL DEFAULT 1,
    severity              TEXT    NOT NULL DEFAULT 'low',
    first_seen_at         DATETIME NOT NULL DEFAULT (datetime('now')),
    last_seen_at          DATETIME NOT NULL DEFAULT (datetime('now')),
    example_submission_ids TEXT   NOT NULL DEFAULT '[]',
    UNIQUE(user_id, pattern_type, topic)
);

CREATE TABLE IF NOT EXISTS progress_records (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                 INTEGER NOT NULL REFERENCES users(id),
    session_id              INTEGER NOT NULL REFERENCES sessions(id),
    problem_id              INTEGER NOT NULL REFERENCES problems(id),
    topic                   TEXT    NOT NULL,
    difficulty              TEXT    NOT NULL,
    solved                  INTEGER NOT NULL DEFAULT 0,
    attempts_count          INTEGER NOT NULL DEFAULT 1,
    time_to_solve_seconds   INTEGER NOT NULL DEFAULT 0,
    final_correctness_score REAL    NOT NULL DEFAULT 0.0,
    complexity_verdict      TEXT    NOT NULL DEFAULT '',
    patterns_triggered      TEXT    NOT NULL DEFAULT '[]',
    learning_path_snapshot  TEXT    NOT NULL DEFAULT '{}',
    created_at              DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id    ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_session ON submissions(session_id);
CREATE INDEX IF NOT EXISTS idx_submissions_user    ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_progress_user       ON progress_records(user_id);
CREATE INDEX IF NOT EXISTS idx_patterns_user       ON pattern_detections(user_id);
"""


@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(DATABASE_URL) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys=ON")
        yield conn


async def init_db():
    async with aiosqlite.connect(DATABASE_URL) as conn:
        await conn.executescript(SCHEMA)
        await conn.commit()
