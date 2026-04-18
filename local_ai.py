"""Local LLM calls via Ollama (Phi-3)."""

from __future__ import annotations

import ollama

# Ollama model tag for Microsoft Phi-3 (e.g. `ollama pull phi3`)
PHI3_MODEL = "phi3"
SYSTEM_PROMPT = (
    "You are CORA, a smart home assistant. Respond with direct answers only, "
    "with no preamble. Maximum 1-2 sentences. Do not explain unless the user "
    "explicitly asks for an explanation."
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
