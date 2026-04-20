"""Local LLM calls via Ollama (Phi-3)."""

from __future__ import annotations

import ollama

# Ollama model tag for Microsoft Phi-3 (e.g. `ollama pull phi3`)
PHI3_MODEL = "phi3"
SYSTEM_PROMPT = (
    "You are CORA, a local home assistant. You have exactly two response modes:\n\n"
    "1. COMMAND — for smart home actions only. Use this exact format:\n"
    "ACTION: <service> | <entity> | <value>\n"
    "Example: ACTION: light.turn_on | kitchen_light | brightness=100\n\n"
    "2. ANSWER — for questions and conversation. One sentence maximum.\n\n"
    "Rules:\n"
    "- Never invent device names or actions\n"
    "- Never guess entity names\n"
    "- If a device is unknown say: I don't have that device\n"
    "- Never add preamble or explanation\n"
    "- Never combine COMMAND and ANSWER in one response\n"
    "- ANSWER mode only, never COMMAND, for questions about the world"
    "- If you are not sure about the answer, say: I'm not sure"
    "- Answer questions as concisely as possible"
    "- Only ask a follow up question if clarification is needed"
    
)

# Alternating user / assistant messages (no system here).
MAX_EXCHANGES = 10
_history: list[dict[str, str]] = []


def clear_history() -> None:
    """Drop all stored conversation turns."""
    global _history
    _history = []


def respond(user_input: str) -> str:
    """Send ``user_input`` to Phi-3 with recent history and return the reply."""
    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *_history,
        {"role": "user", "content": user_input},
    ]
    response = ollama.chat(model=PHI3_MODEL, messages=messages)
    reply = response.message.content or ""

    _history.append({"role": "user", "content": user_input})
    _history.append({"role": "assistant", "content": reply})

    max_messages = MAX_EXCHANGES * 2
    if len(_history) > max_messages:
        _history[:] = _history[-max_messages:]

    return reply
