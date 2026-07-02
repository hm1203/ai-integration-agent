"""
agent.py
The "bridge" layer: exposes the mock enterprise API (mock_api.py) as tools
an LLM agent can call, then runs an interactive loop where the agent decides
which API calls to make in order to answer a user's question.

This mirrors the same idea as MuleSoft's MCP-style "agent-ready API" pattern:
an existing System API gets wrapped so an AI agent can discover and call it
safely, instead of the agent guessing at data or hallucinating numbers.

Prerequisites:
    1. Start the mock API first, in a separate terminal:
         uvicorn mock_api:app --reload --port 8000
    2. Put your Anthropic API key in a .env file (see .env.example)

Run with:
    python agent.py
"""

import os
import json
import requests
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8000"
MODEL = "claude-sonnet-4-6"

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ---------------------------------------------------------------------------
# 1. Tool definitions — this is the "agent-ready API" contract.
#    Each tool maps 1:1 to a real endpoint in mock_api.py.
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "list_employees",
        "description": "List employees, optionally filtered by department or status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "department": {"type": "string", "description": "e.g. Engineering, Finance"},
                "status": {"type": "string", "description": "e.g. active, on_leave"},
            },
        },
    },
    {
        "name": "get_timesheet",
        "description": "Get the current week's timesheet (regular + overtime hours) for a single employee.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string", "description": "e.g. E1001"},
            },
            "required": ["employee_id"],
        },
    },
    {
        "name": "flag_anomaly",
        "description": "Record an anomaly flag against an employee's timesheet record (e.g. excessive overtime).",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string"},
                "reason": {"type": "string", "description": "Why this record is being flagged"},
            },
            "required": ["employee_id", "reason"],
        },
    },
]

SYSTEM_PROMPT = """You are an internal HR operations assistant for a timekeeping system.
You have tools that call a real backend API — never guess or invent employee data.

When asked about overtime anomalies, use this rule: an employee's timesheet is
anomalous if overtime_hours > 10 for the week. If you find anomalies, call
flag_anomaly for each one with a clear, specific reason, then summarize what
you found and flagged in plain English.
"""

# ---------------------------------------------------------------------------
# 2. Tool execution — translates a tool call into a real HTTP request
#    against the mock API. This is the piece a real integration engineer
#    would swap for an actual MuleSoft Process API call.
# ---------------------------------------------------------------------------


def execute_tool(name: str, tool_input: dict) -> dict:
    try:
        if name == "list_employees":
            resp = requests.get(f"{API_BASE}/employees", params=tool_input, timeout=10)
        elif name == "get_timesheet":
            emp_id = tool_input["employee_id"]
            resp = requests.get(f"{API_BASE}/employees/{emp_id}/timesheet", timeout=10)
        elif name == "flag_anomaly":
            resp = requests.post(f"{API_BASE}/timesheet/flag-anomaly", json=tool_input, timeout=10)
        else:
            return {"error": f"Unknown tool: {name}"}

        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Could not reach mock API. Is it running on port 8000? (uvicorn mock_api:app --reload)"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"API returned an error: {e}"}


# ---------------------------------------------------------------------------
# 3. Agent loop — sends the conversation to Claude, executes any tool calls
#    it requests, feeds results back, and repeats until Claude gives a
#    final text answer.
# ---------------------------------------------------------------------------


def run_agent(user_message: str, verbose: bool = True) -> str:
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Collect any text Claude produced this turn
        text_parts = [b.text for b in response.content if b.type == "text"]
        tool_uses = [b for b in response.content if b.type == "tool_use"]

        if not tool_uses:
            # No more tools to call — this is the final answer
            return "\n".join(text_parts)

        # Claude wants to call one or more tools. Append its turn, then
        # execute each tool and append the results as a user turn.
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for call in tool_uses:
            if verbose:
                print(f"  [tool call] {call.name}({call.input})")
            result = execute_tool(call.name, call.input)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": json.dumps(result),
                }
            )

        messages.append({"role": "user", "content": tool_results})


def main():
    print("AI Integration Agent — connected to mock timekeeping API")
    print("Try: 'Which employees have overtime anomalies this week?'")
    print("Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue

        answer = run_agent(user_input)
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
