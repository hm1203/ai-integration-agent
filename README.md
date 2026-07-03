# AI Integration Agent

A small, self-contained demo that wraps a REST API (a mock enterprise
timekeeping system) as tools an AI agent can call — the same core pattern
used in enterprise "API-led connectivity" integration, applied to AI agent
tooling instead of a human-facing frontend.

Enterprise integration platforms are increasingly being asked to expose existing System/Process APIs as "agent-ready" tools
so AI agents can act on real data instead of guessing. This project is a
minimal, from-scratch implementation of that idea: a real API, a tool
schema layer, and an LLM agent loop that decides which API calls to make.

## Architecture

```
 ┌─────────────┐        tool call         ┌──────────────────┐        HTTP        ┌──────────────────┐
 │             │ ───────────────────────▶ │                  │ ─────────────────▶ │                  │
 │  User query │                          │  agent.py         │                     │  mock_api.py      │
 │ (natural    │ ◀─────────────────────── │  (Claude + tools) │ ◀────────────────── │  (FastAPI /       │
 │  language)  │        final answer      │                  │     JSON response   │  System API)      │
 └─────────────┘                          └──────────────────┘                     └──────────────────┘
```

- **`mock_api.py`** — a FastAPI "System API" simulating a Workday/PeopleSoft-style
  backend: employees, timesheets, an anomaly-flagging endpoint. Narrow,
  predictable, resource-based — the kind of contract you'd design in
  MuleSoft's API-led connectivity model.
- **`data.py`** — deterministic mock data (50 employees, ~15% with an
  overtime spike so there's something real to find).
- **`agent.py`** — wraps each API endpoint as a Claude tool, runs an agent
  loop: the model decides which tools to call, the code executes real HTTP
  requests against `mock_api.py`, and results get fed back until the model
  produces a final answer.

## Setup

**Requirements:** Python 3.10+, an Anthropic API key.

```bash
# 1. Clone or unzip this project, then cd into it
cd ai-integration-agent

# 2. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
cp .env.example .env
# then edit .env and paste your real ANTHROPIC_API_KEY
```

## Running it

You need two terminals.

**Terminal 1 — start the mock API:**
```bash
uvicorn mock_api:app --reload --port 8000
```
Check it's alive: open http://localhost:8000/health in a browser, or
`curl http://localhost:8000/health`.

**Terminal 2 — start the agent:**
```bash
python agent.py
```

Then try prompts like:
- `Which employees have overtime anomalies this week?`
- `Show me everyone in Engineering`
- `Get the timesheet for E1001`

The agent will print which tools it's calling (so you can see the
decision-making), then give a plain-English answer. When it finds
overtime anomalies, it will actually call `flag_anomaly` against the
mock API — you can verify this persisted by re-querying the API.

## What this demonstrates

- Designing API contracts an AI agent can safely call (not just a human UI)
- Tool-use / function-calling with the Claude API
- A working agent loop: request → tool call → real API execution → response
- Applying enterprise integration patterns (System API design, clean
  resource boundaries, predictable schemas) to AI agent tooling — the same
  shift integration platforms like MuleSoft are building toward with
  agent-ready API exposure (MCP support, Agent Fabric, etc.)



