# AI DSA Interview Platform

A multi-agent intelligent interview simulation system for personalised Data Structures and Algorithms mastery. Five coordinated AI agents handle problem selection, live interview simulation, sandboxed code execution, automated code review, pattern detection, and progress tracking — giving you adaptive, realistic DSA interview practice.

---

## Features

- **Conversational interview simulation** — an AI interviewer that guides you through clarification, brute-force, optimisation, coding, and code-review phases
- **Adaptive problem selection** — problems chosen based on your weak topics, error history, and difficulty progression
- **Sandboxed code execution** — your Python solution is run against hidden test cases in an isolated subprocess with a 10-second timeout
- **Automated code review** — LLM-powered analysis of time/space complexity, missed edge cases, and code quality
- **Pattern detection** — recurring mistakes (off-by-one errors, missing null checks, bad DP transitions, etc.) tracked across sessions
- **Personalised learning paths** — focus areas and recommended topics generated after every session

---

## Architecture

Five agents are orchestrated by a central service; no agent calls another directly.

```
Pattern Detection Agent ──┐
Problem Selector Agent  ──┤
Interview Simulation    ──┼── Orchestrator ── FastAPI ── React SPA
Code Review Agent       ──┤
Progress Tracker Agent  ──┘
```

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, FastAPI 0.115, uvicorn |
| LLM | Groq API — `llama-3.3-70b-versatile` |
| Database | SQLite + aiosqlite (WAL mode) |
| Auth | JWT (HS256) + bcrypt |
| Frontend | React 19, Vite 5, React Router 7 |
| Code editor | Monaco Editor |
| Sandbox | Python `subprocess`, static import blocking |

---

## Repository layout

```
backend/
├── agents/       # One module per agent
├── api/          # FastAPI route handlers
├── models/       # Pydantic schemas
├── prompts/      # LLM prompt templates
├── services/     # Orchestrator, LLM client, sandbox, DB, auth
├── scripts/      # Seed scripts
└── tests/        # pytest test suite
frontend/
├── src/
│   ├── pages/    # Dashboard, Session, Progress, Login, Register
│   ├── api.js    # Axios client
│   └── AuthContext.jsx
report.tex        # Dissertation-style project report (LaTeX)
requirements.txt  # Python dependencies
```

---

## Quickstart

### Prerequisites

- Python 3.10+
- Node 18+ and npm
- A [Groq API key](https://console.groq.com/)

### 1. Clone and set up environment variables

```bash
git clone <repo-url>
cd ai-dsa-interview-platform
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET=change-this-to-a-long-random-string
```

### 2. Backend

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cd backend
uvicorn main:app --port 8002 --reload
```

The API will be available at `http://localhost:8002`.  
Interactive API docs: `http://localhost:8002/docs`

### 3. Frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The app will open at `http://localhost:5173`.

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | Yes | — | Groq API key for LLM calls |
| `JWT_SECRET` | Yes | `change-me` | Secret used to sign JWTs — **change in production** |
| `JWT_EXPIRE_HOURS` | No | `24` | Token expiry duration |
| `DATABASE_URL` | No | `backend/data/db.sqlite3` | Path to SQLite database file |

---

## Running tests

```bash
cd backend
pytest tests/ -v
```

---

## Troubleshooting

- **Backend won't start** — confirm `GROQ_API_KEY` is set in `.env` and the virtual environment is activated.
- **LLM timeouts** — agent calls have a 30-second timeout with graceful fallbacks; a slow Groq response will not crash a session.
- **Code submission always fails** — check `backend_debug.log` for sandbox errors. Ensure your function name matches the problem's expected function name (snake_case and camelCase variants are resolved automatically).
- **Frontend shows "Network Error"** — confirm the backend is running on port 8002 and that `VITE_API_BASE_URL` (if overridden) is correct.

---

## Contributing

Open an issue describing your change before submitting a pull request.
