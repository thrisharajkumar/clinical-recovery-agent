"""
LLM integration layer. Talks to a local, free model via Ollama
(https://ollama.com) only — there is no paid backend in this repository.

Amy (the LLM) may only *communicate* recommendations that come from
app.core.recommendation_engine.get_recommendation — she never generates
recommendation content herself. The tool-use loop below is what enforces
that structurally: the model must call get_recommendation to receive one
at all; it cannot fabricate the recommendation content itself.
"""
import json
from typing import List

import requests

from app.config import settings
from app.core.recommendation_engine import get_recommendation
from app.core.system_prompt import SYSTEM_PROMPT

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_recommendation",
            "description": "Get a recovery exercise recommendation for the patient's "
                            "procedure type and how many days post-surgery they are.",
            "parameters": {
                "type": "object",
                "properties": {
                    "procedure_type": {"type": "string", "description": "e.g. 'knee', 'hip'"},
                    "recovery_day": {"type": "integer", "description": "Days since surgery"},
                },
                "required": ["procedure_type", "recovery_day"],
            },
        },
    }
]


def _run_tool(tool_name: str, tool_input: dict) -> dict:
    if tool_name == "get_recommendation":
        rec = get_recommendation(**tool_input)
        return rec.model_dump()
    raise ValueError(f"Unknown tool: {tool_name}")


def generate_reply(history: List[dict]) -> tuple[str, bool, dict | None]:
    """Runs the tool-use loop against the local Ollama server.
    Returns (reply_text, used_recommendation_engine, last_recommendation).
    last_recommendation is the exact structured dict the recommendation
    engine returned, if the tool was called — used by main.py to verify
    the reply actually reflects it (provenance check), rather than trusting
    that a tool call happening means the reply is faithful to it.

    Requires `ollama serve` running locally and a model pulled
    (default: `ollama pull qwen3:8b`). Tool-call reliability depends on the
    model — this has not been benchmarked here against alternatives, see
    README "Verification provenance"."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(history)
    used_engine = False
    last_recommendation = None

    for _ in range(3):  # cap the loop — never let this run away
        resp = requests.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": messages,
                "tools": _TOOLS,
                "stream": False,
            },
            timeout=60,
        )
        resp.raise_for_status()
        message = resp.json().get("message", {})
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            return message.get("content", ""), used_engine, last_recommendation

        messages.append(message)
        for call in tool_calls:
            fn = call.get("function", {})
            used_engine = used_engine or fn.get("name") == "get_recommendation"
            result = _run_tool(fn.get("name"), fn.get("arguments", {}))
            if fn.get("name") == "get_recommendation":
                last_recommendation = result
            messages.append({"role": "tool", "content": json.dumps(result)})

    return ("I'm having trouble putting together a response right now — please try again.",
            used_engine, last_recommendation)
