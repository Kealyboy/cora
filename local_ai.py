"""Local LLM calls via Ollama (Phi-3)."""

import ollama

# Ollama model tag for Microsoft Phi-3 (e.g. `ollama pull phi3`)
PHI3_MODEL = "phi3"


def respond(user_input: str) -> str:
    """Send ``user_input`` to Phi-3 and return the assistant reply as a string."""
    response = ollama.chat(
        model=PHI3_MODEL,
        messages=[{"role": "user", "content": user_input}],
    )
    return response.message.content
