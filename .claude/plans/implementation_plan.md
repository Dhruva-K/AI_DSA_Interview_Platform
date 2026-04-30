# Implementation Plan — AI DSA Interview Platform

## 1. Data Models (SQLite)

Seven tables: `users`, `problems`, `sessions`, `submissions`, `code_reviews`, `pattern_detections`, `progress_records`.

**Key design decisions:**
- `sessions` carries a `phase` column (state machine) and `conversation_history` as a JSON array — the full chat log
- `submissions` links to a `sessions` row; each code submit creates one row
- `code_reviews` is 1:1 with a submission — stores structured LLM output (correctness score, complexity verdict, edge cases missed, quality issues)
- `pattern_detections` is upserted by user+pattern_type+topic with an occurrence counter and severity (`low`/`medium`/`high`)
- All inter-agent communication uses a typed JSON envelope: `{agent, action, session_id, user_id, payload}`

### Table: `users`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| username | TEXT UNIQUE | |
| email | TEXT UNIQUE | |
| password_hash | TEXT | bcrypt |
| preferred_difficulty | TEXT | "easy" / "medium" / "hard" |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### Table: `problems`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| slug | TEXT UNIQUE | e.g. "two-sum" |
| title | TEXT | |
| topic | TEXT | "arrays" / "trees" / "dp" / "graphs" / "strings" / "heaps" / "tries" / "backtracking" / "sliding-window" / "binary-search" / "linked-lists" / "stack-queue" |
| difficulty | TEXT | "easy" / "medium" / "hard" |
| description | TEXT | |
| constraints | TEXT | JSON array of strings |
| examples | TEXT | JSON array of {input, output, explanation} |
| test_cases | TEXT | JSON array of {input, expected_output, is_hidden, edge_case_label} |
| brute_force_hint | TEXT | |
| optimal_hint | TEXT | |
| optimal_time_complexity | TEXT | e.g. "O(n log n)" |
| optimal_space_complexity | TEXT | e.g. "O(n)" |
| follow_up_questions | TEXT | JSON array of strings |
| source_tags | TEXT | JSON array e.g. ["leetcode-1", "classic"] |

### Table: `sessions`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| user_id | INTEGER FK | |
| problem_id | INTEGER FK | |
| status | TEXT | "active" / "completed" / "abandoned" |
| phase | TEXT | "problem_presentation" / "clarification" / "brute_force" / "optimization" / "coding" / "code_review" / "wrap_up" |
| conversation_history | TEXT | JSON array of {role, content, timestamp} |
| started_at | DATETIME | |
| ended_at | DATETIME | nullable |
| duration_seconds | INTEGER | computed on close |

### Table: `submissions`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| session_id | INTEGER FK | |
| user_id | INTEGER FK | |
| problem_id | INTEGER FK | |
| code | TEXT | |
| language | TEXT | "python" initially |
| attempt_number | INTEGER | 1-indexed within session |
| sandbox_stdout | TEXT | |
| sandbox_stderr | TEXT | |
| sandbox_exit_code | INTEGER | |
| test_cases_passed | INTEGER | |
| test_cases_total | INTEGER | |
| all_passed | BOOLEAN | |
| runtime_ms | INTEGER | |
| submitted_at | DATETIME | |

### Table: `code_reviews`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| submission_id | INTEGER FK | |
| correctness_score | REAL | 0.0–1.0 |
| detected_time_complexity | TEXT | |
| detected_space_complexity | TEXT | |
| complexity_verdict | TEXT | "optimal" / "suboptimal" / "incorrect" |
| edge_cases_missed | TEXT | JSON array of strings |
| code_quality_issues | TEXT | JSON array of {type, line, description} |
| improvement_suggestions | TEXT | JSON array of strings |
| overall_feedback | TEXT | |
| llm_raw_response | TEXT | stored for debugging |

### Table: `pattern_detections`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| user_id | INTEGER FK | |
| pattern_type | TEXT | "off-by-one" / "missing-edge-case" / "bad-dp-transition" / "inefficient-loop" / "wrong-base-case" / "incorrect-pointer-movement" / "missing-null-check" |
| topic | TEXT | |
| occurrence_count | INTEGER | |
| first_seen_at | DATETIME | |
| last_seen_at | DATETIME | |
| example_submission_ids | TEXT | JSON array |
| severity | TEXT | "low" / "medium" / "high" |

### Table: `progress_records`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| user_id | INTEGER FK | |
| session_id | INTEGER FK | |
| problem_id | INTEGER FK | |
| topic | TEXT | denormalized |
| difficulty | TEXT | denormalized |
| solved | BOOLEAN | |
| attempts_count | INTEGER | |
| time_to_solve_seconds | INTEGER | |
| final_correctness_score | REAL | |
| complexity_verdict | TEXT | |
| patterns_triggered | TEXT | JSON array of pattern_type strings |
| learning_path_snapshot | TEXT | JSON object |

---

## 2. Problem Dataset

**12 topics × 3 difficulties ≈ 150 problems minimum**

| Topic | Easy | Medium | Hard |
|---|---|---|---|
| Arrays | 8 | 10 | 5 |
| Strings | 6 | 8 | 4 |
| Linked Lists | 5 | 6 | 3 |
| Stacks / Queues | 4 | 6 | 3 |
| Binary Search | 4 | 6 | 4 |
| Sliding Window | 3 | 6 | 3 |
| Trees | 6 | 8 | 4 |
| Graphs | 4 | 7 | 4 |
| Dynamic Programming | 4 | 8 | 6 |
| Heaps | 3 | 5 | 3 |
| Tries | 2 | 4 | 2 |
| Backtracking | 2 | 5 | 3 |

Each problem carries: 3 visible examples + 7–15 hidden test cases covering empty input, single element, max constraint, duplicates, and at least one stress test.

Test case format:
```json
{
  "input": {"nums": [2,7,11,15], "target": 9},
  "expected_output": [0, 1],
  "is_hidden": true,
  "edge_case_label": "two elements"
}
```

**Sourcing:** ~50 hand-curated classics written from scratch → ~100 LLM-generated → all validated by running a reference solution through the sandbox before insert.

---

## 3. The Five Agents

### 3.1 Pattern Detection Agent
**File:** `backend/agents/pattern_detection_agent.py`
**Trigger:** At session start (read-only) and after every code review.

**Inputs:**
```json
{
  "user_id": 42,
  "scope": "recent | all_time",
  "recent_limit": 20,
  "code_reviews": [...],
  "submission_codes": [...]
}
```

**Outputs:**
```json
{
  "patterns": [
    {
      "pattern_type": "off-by-one",
      "topic": "arrays",
      "occurrences": 4,
      "severity": "high",
      "description": "...",
      "example_submission_ids": [11, 14, 17]
    }
  ],
  "summary_for_selector": {
    "weak_topics": ["dp", "trees"],
    "dominant_patterns": ["off-by-one", "missing-edge-case"]
  }
}
```

**Logic:** Two-pass — regex pre-filter (loop bounds, null checks, base cases) then LLM semantic pass for contextual patterns. Results merged and deduplicated. Severity: 1 occurrence = low, 2–3 = medium, 4+ = high.

**LLM config:** Temperature 0.2, constrained to fixed 7-pattern taxonomy, system prompt cached.

**Storage reads:** `submissions`, `code_reviews`
**Storage writes:** `pattern_detections` (upsert by user_id + pattern_type + topic)

---

### 3.2 Problem Selector Agent
**File:** `backend/agents/problem_selector_agent.py`
**Trigger:** Once at session start.

**Inputs:**
```json
{
  "user_id": 42,
  "pattern_summary": { "weak_topics": ["dp"], "dominant_patterns": ["off-by-one"] },
  "solved_problem_ids": [1, 7, 12],
  "topic_coverage": { "arrays": 5, "dp": 1 },
  "current_difficulty": "medium",
  "prefer_topic": null
}
```

**Outputs:**
```json
{
  "selected_problem_id": 88,
  "selection_rationale": "...",
  "topic": "dp",
  "difficulty": "medium"
}
```

**Logic:** Weighted scoring (deterministic):
- Weak topic bonus: +3.0
- Coverage balance (< 2 solved): +1.5
- Pattern alignment: +2.0
- Recency penalty (repeated topic in last 3 sessions): −1.0

Top 5 candidates sent to LLM only to generate the one-sentence `selection_rationale`. Selection itself is never delegated to the LLM.

**Difficulty ladder:** steps up when last 3 sessions > 80% solved; steps down when < 40%.

**LLM config:** Temperature 0.4 (for rationale text only).

**Storage reads:** `problems`, `progress_records`, `pattern_detections`
**Storage writes:** none (orchestrator creates the session row)

---

### 3.3 Interview Simulation Agent
**File:** `backend/agents/interview_simulation_agent.py`
**Trigger:** On every user message turn.

**Inputs (per turn):**
```json
{
  "session_id": 99,
  "problem": { "title": "...", "description": "...", "examples": [...], "constraints": [...], "follow_up_questions": [...] },
  "current_phase": "clarification",
  "conversation_history": [...],
  "user_message": "Can we assume the array is sorted?",
  "pattern_summary": { ... }
}
```

**Outputs (per turn):**
```json
{
  "interviewer_response": "...",
  "next_phase": "brute_force",
  "phase_transition_reason": "clarification_complete",
  "should_request_code": false,
  "session_complete": false
}
```

**Phase transition rules (deterministic rules engine, not LLM):**
```
problem_presentation  → clarification          (automatic after problem delivered)
clarification         → brute_force            (after 2–4 turns or user signals understanding)
brute_force           → optimization           (after brute force articulated)
optimization          → coding                 (after optimal approach described OR timeout cue)
coding                → code_review            (on user code submission — triggered externally)
code_review           → wrap_up                (after review delivered)
wrap_up               → completed
ANY                   → abandoned              (on user exit)
```

**LLM config:** Problem statement cached per-session (`cache_control: ephemeral`). Per-turn prompt includes only the conversation history delta. Temperature 0.6. Pressure profile calibrated from pattern summary.

**Storage reads:** `sessions` (conversation_history), `problems`
**Storage writes:** `sessions` (conversation_history appended, phase updated)

---

### 3.4 Code Review Agent
**File:** `backend/agents/code_review_agent.py`
**Trigger:** After sandbox result is ready (orchestrator pre-populates sandbox result before calling this agent).

**Inputs:**
```json
{
  "submission_id": 55,
  "code": "def two_sum(nums, target):\n    ...",
  "language": "python",
  "problem": { "id": 88, "test_cases": [...], "optimal_time_complexity": "O(n)", "optimal_space_complexity": "O(n)" },
  "sandbox_result": {
    "stdout": "...", "stderr": "", "exit_code": 0, "runtime_ms": 43,
    "test_cases_passed": 9, "test_cases_total": 10,
    "failed_test_case": { "input": {...}, "expected": "...", "got": "..." }
  }
}
```

**Outputs:**
```json
{
  "correctness_score": 0.9,
  "detected_time_complexity": "O(n)",
  "detected_space_complexity": "O(n)",
  "complexity_verdict": "optimal",
  "edge_cases_missed": ["empty array input"],
  "code_quality_issues": [{ "type": "naming", "line": 3, "description": "..." }],
  "improvement_suggestions": ["..."],
  "overall_feedback": "...",
  "patterns_flagged": ["missing-edge-case"]
}
```

**Two LLM calls:**
- Call 1 (temp 0.1): complexity analysis only — receives code + constraints, returns complexity fields
- Call 2 (temp 0.3): quality + feedback — receives code, sandbox result, problem statement, call 1 output

**Deterministic (no LLM):**
- `correctness_score = test_cases_passed / test_cases_total`
- `patterns_flagged` computed by string-matching `edge_cases_missed` against the 7-pattern taxonomy

**Storage reads:** `problems`
**Storage writes:** `submissions` (sandbox fields), `code_reviews`

---

### 3.5 Progress Tracker Agent
**File:** `backend/agents/progress_tracker_agent.py`
**Trigger:** At session end; on-demand for dashboard.

**Inputs:**
```json
{
  "user_id": 42,
  "session_id": 99,
  "code_review": { ... },
  "pattern_detection": { ... },
  "problem": { "topic": "dp", "difficulty": "medium" },
  "session_duration_seconds": 2400,
  "solved": true
}
```

**Outputs:**
```json
{
  "progress_record_id": 301,
  "updated_stats": {
    "total_sessions": 12,
    "total_solved": 9,
    "overall_success_rate": 0.75,
    "topic_stats": {
      "dp": { "attempted": 3, "solved": 1, "success_rate": 0.33 }
    }
  },
  "learning_path": {
    "next_recommended_topics": ["dp", "trees"],
    "suggested_difficulty": "medium",
    "milestone": "...",
    "focus_areas": ["...", "..."]
  }
}
```

**Logic:** All stats are SQL aggregations (deterministic). LLM only writes `focus_areas` (2–4 bullets) and `milestone` text. Temperature 0.5.

**Weak topic threshold:** success_rate < 0.5.

**Storage reads:** `progress_records`, `pattern_detections`, `sessions`
**Storage writes:** `progress_records` (insert), `sessions` (mark completed)

---

## 4. Orchestrator

**File:** `backend/services/orchestrator.py`

Agents never call each other — all coordination goes through the orchestrator.

### Session Lifecycle

1. `POST /sessions` → Pattern Detection (read) → Problem Selector → create session row
2. `POST /sessions/:id/message` → Interview Simulation → save to conversation_history → return response
3. `POST /sessions/:id/submit-code` → Sandbox → Code Review → Pattern Detection (incremental) → return review + follow-up
4. Session close → Progress Tracker → mark session `completed`

**Timeout policy:** every agent call wrapped in `asyncio.wait_for(30s)`. On timeout, return graceful fallback and log.

---

## 5. API Layer (FastAPI)

All routes under `/api/v1`. JWT auth server-side only — never trusted from request body. Session ownership enforced on every session route (403 if mismatch). Rate limit: 5 code submissions/minute/user at middleware level.

| Route | Method | Triggers |
|---|---|---|
| `/auth/register` | POST | — |
| `/auth/login` | POST | — |
| `/sessions` | POST | Pattern Detection + Problem Selector |
| `/sessions/:id` | GET | DB read |
| `/sessions/:id/message` | POST | Interview Simulation |
| `/sessions/:id/submit-code` | POST | Sandbox + Code Review + Pattern Detection |
| `/sessions/:id/end` | POST | Progress Tracker |
| `/sessions/:id/review` | GET | DB read |
| `/users/me/progress` | GET | DB aggregation |
| `/users/me/patterns` | GET | DB read |
| `/users/me/learning-path` | GET | Progress Tracker (read) |
| `/problems` | GET | DB read (admin/seed) |

---

## 6. Sandbox

**File:** `backend/services/sandbox.py`

Never uses `eval()`/`exec()` in the main process.

**Architecture:** user code written to temp file → `runner.py` harness imports it via `importlib` → spawned as subprocess receiving test input via stdin, writing JSON result to stdout.

**Resource limits:**
- Wall-clock: 10s (`subprocess.run(timeout=10)`, parent kills child on exceed)
- Memory: 256MB via `resource.RLIMIT_AS` (Linux prod)
- CPU: 5s via `resource.RLIMIT_CPU` (Linux prod)
- No network access; read-only working directory

**Pre-filter (first line of defense):** blocks `import os`, `import subprocess`, `import socket`, `open(`, `exec(`, `eval(` before subprocess starts — gives fast, friendly error message.

**Exit codes:**
| Condition | exit_code | stderr |
|---|---|---|
| Timeout | -1 | "Time limit exceeded (10s)" |
| Memory exceeded | -2 | "Memory limit exceeded" |
| Syntax error | 1 | Python traceback |
| Runtime exception | 1 | Python traceback |
| Blocked import | — | Pre-filter error (no subprocess) |

---

## 7. Frontend (React)

State management: React Context + `useReducer`. All API calls through a central `api.js` service that attaches JWT to every request.

| Page | Route | Key Components |
|---|---|---|
| Auth | `/login`, `/register` | Simple forms |
| Dashboard | `/dashboard` | Success rate, topic radar chart (Recharts), weak areas, recent sessions, Start button |
| Session View | `/session/:id` | Left: chat (40%), Right: Monaco editor + test results (60%), Top: phase stepper |
| Post-Session Review | `/session/:id/review` | Transcript, final code, full code review, patterns flagged |
| Progress | `/progress` | Topic bar chart by difficulty, patterns table, learning path card |

### Key UI Flows

**Starting a session:** Click "Start Interview" → `POST /sessions` (loading: "Selecting problem based on your history...") → navigate to session view with interviewer opening message pre-populated.

**Mid-interview message:** User types → `POST /sessions/:id/message` → typing indicator → response appears → phase stepper updates → if `should_show_code_editor: true`, right panel animates in.

**Code submission:** Click "Submit Code" → `POST /sessions/:id/submit-code` (loading: "Running test cases...") → test case results render (green/red) → interviewer follow-up in chat → if `all_passed: true`, success banner + session moves to wrap-up.

---

## 8. Testing Strategy

| Layer | Tool | Key Scenarios |
|---|---|---|
| Unit | pytest | Per-agent with mocked LLM + DB. Scoring logic, phase transitions, severity thresholds, sandbox isolation |
| Integration | pytest + real Claude API | Full session lifecycle, cross-agent data flow. Guarded by `RUN_INTEGRATION_TESTS=true` env flag |
| Scenario | scripted against local server | 3 personas: Beginner / Intermediate-DP-weak / Advanced |
| Frontend | React Testing Library + Vitest | Chat rendering, phase stepper, submit button state, dashboard charts |

**3 user personas for scenario tests:**
- Beginner: all-weak, verify system never selects medium/hard until 3 consecutive easy solves
- Intermediate (DP weak): verify Problem Selector consistently picks DP over 5 sessions; Pattern Detection identifies bad DP transitions
- Advanced: all easy/medium solved; verify step-up to hard problems

---

## 9. Build Order & Week Checkpoints

---

### Week 1 — Foundation ✅ DONE
**Built:** DB schema (`db.py`), all Pydantic models (`schemas.py`), sandbox (`sandbox.py`), 30-problem seed script (`seed_problems.py`), `requirements.txt`, `.gitignore`, `.env.example`.

**What to test manually:**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Seed the database (creates backend/data/db.sqlite3 with 30 problems)
python -m backend.scripts.seed_problems

# 3. Verify the DB has problems
python -c "
import asyncio, aiosqlite
async def check():
    async with aiosqlite.connect('backend/data/db.sqlite3') as db:
        cur = await db.execute('SELECT count(*) FROM problems')
        print('Problems in DB:', (await cur.fetchone())[0])
asyncio.run(check())
"

# 4. Smoke-test the sandbox with a correct solution
python -c "
from backend.models.schemas import ProblemTestCase
from backend.services.sandbox import run_code
code = '''
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
'''
result = run_code(code, 'two_sum', [
    ProblemTestCase(input={'nums': [2,7,11,15], 'target': 9}, expected_output=[0,1])
])
print('All passed:', result.all_passed)
print('Runtime ms:', result.runtime_ms)
"

# 5. Test sandbox timeout protection
python -c "
from backend.models.schemas import ProblemTestCase
from backend.services.sandbox import run_code
code = 'def two_sum(nums, target):\n    while True: pass'
result = run_code(code, 'two_sum', [ProblemTestCase(input={'nums':[1],'target':1}, expected_output=[0,0])])
print('Exit code (should be -1):', result.exit_code)
print('Stderr:', result.stderr)
"
```

---

### Week 2 — Core Agents & Auth ✅ DONE
**Built:** `backend/services/auth.py` (JWT), `backend/services/llm.py` (Anthropic client), `backend/api/auth.py` (register/login routes), `backend/api/deps.py` (JWT middleware), `backend/agents/problem_selector_agent.py`, `backend/agents/progress_tracker_agent.py`, `backend/prompts/problem_selector.py`, `backend/prompts/progress_tracker.py`, `backend/main.py`.

**What to test manually:**

```bash
# 1. Copy env file and add your Anthropic key
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY and JWT_SECRET

# 2. Start the API server
uvicorn backend.main:app --reload

# 3. Register a user (in a new terminal)
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"password123"}' | python -m json.tool

# 4. Login and grab the token
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"password123"}' | python -m json.tool

# 5. Try accessing a protected route without a token (should get 403)
curl -s http://localhost:8000/api/v1/users/me/progress

# 6. Use the Swagger UI to explore all routes
# Open: http://localhost:8000/docs
```

---

### Week 3 — Code Review Agent & Interview Simulation Agent
**Build:** `backend/agents/code_review_agent.py`, `backend/agents/interview_simulation_agent.py`, `backend/prompts/code_review_complexity.py`, `backend/prompts/code_review_quality.py`, `backend/prompts/interview_simulation.py`, all session/progress FastAPI routes.

**What to test manually (after build):**

```bash
# Start the server
uvicorn backend.main:app --reload

# Register + login, save token to TOKEN variable
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"password123"}' | python -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Trigger a code review directly (submit a correct Two Sum solution)
curl -s -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
# Note the session_id from the response

# Send an opening message to the interviewer
curl -s -X POST http://localhost:8000/api/v1/sessions/1/message \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"I understand the problem. My approach is to use a hash map."}' | python -m json.tool

# Submit a solution
curl -s -X POST http://localhost:8000/api/v1/sessions/1/submit-code \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target-n], i]\n        seen[n] = i",
    "language": "python"
  }' | python -m json.tool
# Expect: all_passed=true, correctness_score=1.0, complexity_verdict="optimal"
```

---

### Week 4 — Orchestrator & Pattern Detection Agent
**Build:** `backend/services/orchestrator.py` (session state machine), `backend/agents/pattern_detection_agent.py`, `backend/prompts/pattern_detection.py`.

**What to test manually (after build):**

```bash
# Run a complete session end-to-end from start to close
# 1. Start session (problem is auto-selected)
# 2. Have a multi-turn conversation through all phases
# 3. Submit code
# 4. End session and check learning path

# Check pattern detections after a few sessions
curl -s http://localhost:8000/api/v1/users/me/patterns \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Check full progress
curl -s http://localhost:8000/api/v1/users/me/progress \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Check generated learning path
curl -s http://localhost:8000/api/v1/users/me/learning-path \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

---

### Week 5 — React Frontend
**Build:** Vite + React app in `frontend/`, Auth pages, Session View with Monaco Editor, Dashboard, Progress page.

**What to test manually (after build):**

```bash
# Terminal 1: run the backend
uvicorn backend.main:app --reload

# Terminal 2: run the frontend
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173

# Golden path to test:
# 1. Register a new account
# 2. Click "Start Interview" from the Dashboard
# 3. Chat through clarification → brute force → optimization phases
# 4. Write a solution in the Monaco editor and submit
# 5. Review the code feedback panel
# 6. Check the Progress page for updated stats and learning path
```

---

### Week 6 — Polish & Performance
**Build:** Prompt caching (`cache_control` headers), rate limiting middleware, expand problem dataset to 100+.

**What to test manually (after build):**

```bash
# Verify prompt caching is active — check Anthropic usage dashboard for cache hit rate
# Hit the same session endpoint twice and compare response times

# Test rate limiting: fire 6 code submissions in under a minute
# Should receive HTTP 429 on the 6th

# Confirm 100+ problems in the DB
python -c "
import asyncio, aiosqlite
async def check():
    async with aiosqlite.connect('backend/data/db.sqlite3') as db:
        cur = await db.execute('SELECT topic, COUNT(*) FROM problems GROUP BY topic')
        for row in await cur.fetchall():
            print(row[0], row[1])
asyncio.run(check())
"
```

---

### Prompt File Map

One file per agent under `backend/prompts/`:
- `pattern_detection.py`
- `problem_selector.py`
- `interview_simulation.py`
- `code_review_complexity.py`
- `code_review_quality.py`
- `progress_tracker.py`

Static system prompts separated from per-turn user prompt builders so Anthropic `cache_control` can be applied precisely.

---

## Critical Files (Implementation Start Points)

- `backend/services/db.py` — schema DDL + async connection pool
- `backend/services/sandbox.py` — highest-risk, build and test first
- `backend/models/schemas.py` — all Pydantic models and inter-agent JSON contracts
- `backend/services/orchestrator.py` — session state machine and agent coordination
- `backend/agents/interview_simulation_agent.py` — most complex agent (stateful, multi-turn)
