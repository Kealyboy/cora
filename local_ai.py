"""Local LLM calls via Ollama (Phi-3)."""

import ollama

# Ollama model tag for Microsoft Phi-3 (e.g. `ollama pull phi3`)
PHI3_MODEL = "phi3"
SYSTEM_PROMPT = (
    "You are CORA, a helpful home assistant. Keep replies short and "
    "conversational (maximum 2-3 sentences). Never give long explanations "
    "unless the user specifically asks for one."
)


def respond(user_input: str) -> str:
    """Send ``user_input`` to Phi-3 and return the assistant reply as a string."""
    response = ollama.chat(
        model=PHI3_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
    )
    return response.message.content
