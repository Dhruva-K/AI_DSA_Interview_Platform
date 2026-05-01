# AI DSA Interview Platform

Multi-Agent Intelligent Interview Simulation System for Personalized DSA Mastery.

## Project Overview

A multi-agent system that emulates real technical interview environments. Five coordinated AI agents handle problem selection, interview simulation, code review, pattern detection, and progress tracking — giving users adaptive, personalized DSA interview practice.

## Architecture: Five Agents

| Agent | Responsibility |
|---|---|
| **Pattern Detection Agent** | Analyzes submission history to detect recurring mistake patterns (off-by-one errors, missing edge cases, bad DP transitions, inefficient loops) |
| **Problem Selector Agent** | Picks the next DSA problem based on weak topics, history, and difficulty progression; ensures balanced topic coverage |
| **Interview Simulation Agent** | Acts as a realistic interviewer — presents problems, asks clarifying questions, requests brute-force then optimized approaches, applies conversational pressure |
| **Code Review Agent** | Executes code in a sandboxed environment, runs test cases, checks time/space complexity, flags missing edge cases, returns structured feedback |
| **Progress Tracker Agent** | Maintains performance records, tracks solved problems, computes success rates, identifies weak areas, generates personalized learning paths |

An **orchestrator module** coordinates the flow between all agents.

## Tech Stack

- **Language:** Python
- **Backend:** FastAPI
- **AI/LLM:** Groq API (`llama-3.3-70b-versatile`), via the `groq` Python SDK
- **Storage:** SQLite or JSON-based persistence
- **Execution Sandbox:** Python isolated runner
- **Frontend:** React (preferred) or Streamlit
- **Version Control:** Git + GitHub

## Project Structure

```
├── backend/
│   ├── agents/         # One module per agent
│   ├── api/            # FastAPI routes
│   ├── models/         # Data models / schemas
│   ├── prompts/        # LLM prompt templates
│   └── services/       # Orchestrator and shared services
└── frontend/           # React or Streamlit UI
```

## Development Phases

1. Requirement analysis and dataset preparation (problems, constraints, test cases)
2. Architecture design — agent communication protocols, JSON schemas, orchestrator
3. Progress Tracker + Problem Selector implementation
4. Interview Simulation Agent
5. Code Review Agent + sandbox setup
6. Pattern Detection Agent
7. Integration and multi-agent workflow testing
8. User interface development
9. User testing and refinement
10. Final documentation

## Key Conventions

- Each agent lives in its own module under `backend/agents/`
- Agent communication uses JSON schemas — define these in `backend/models/`
- Prompt templates go in `backend/prompts/`, not inline in agent code
- Code execution must always go through the sandbox — never `eval`/`exec` raw user input directly
- SQLite is the default store; only switch to JSON persistence for stateless/ephemeral data
