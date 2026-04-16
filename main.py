"""CORA voice loop: listen, route, speak."""

from __future__ import annotations

import router
import speech_to_text
import text_to_speech


def _wants_exit_session(text: str) -> bool:
    """True if the user wants to end the session (decline or explicit exit)."""
    t = text.lower().strip().strip(".,!?")
    if not t:
        return False
    if t in ("that's it", "that is it", "that's all", "that is all"):
        return True
    words = t.split()
    return words[0] in (
        "no",
        "nope",
        "nah",
        "quit",
        "exit",
        "stop",
        "done",
        "goodbye",
        "bye",
        "q",
    )


def _sounds_like_question_or_request(text: str) -> bool:
    """Heuristic for whether text is likely a follow-up question/request."""
    t = text.strip()
    if not t:
        return False

    normalized = t.lower().strip(".,!?")
    words = normalized.split()
    if not words:
        return False

    if "?" in t:
        return True

    question_starters = {
        "what",
        "when",
        "where",
        "why",
        "how",
        "who",
        "which",
        "can",
        "could",
        "would",
        "will",
        "should",
        "is",
        "are",
        "do",
        "does",
        "did",
    }
    request_starters = {
        "set",
        "turn",
        "play",
        "open",
        "start",
        "stop",
        "tell",
        "show",
        "remind",
        "call",
        "send",
        "help",
        "please",
    }

    if words[0] in question_starters or words[0] in request_starters:
        return True

    # Single-word replies like "okay", "thanks", etc. are not follow-up requests.
    return len(words) > 1


def main() -> None:
    usage_count = 0
    pending_input: str | None = None

    while True:
        user_input = speech_to_text.listen() if pending_input is None else pending_input
        pending_input = None

        if not user_input.strip():
            continue

        print(f"You said: {user_input}")
        if _wants_exit_session(user_input):
            text_to_speech.speak("Goodbye")
            break

        usage_count += 1
        response = router.route(user_input, usage_count)
        print(response)
        text_to_speech.speak(response)

        next_input = speech_to_text.listen()
        if not next_input.strip():
            text_to_speech.speak("Goodbye")
            break

        if _wants_exit_session(next_input):
            text_to_speech.speak("Goodbye")
            break

        if not _sounds_like_question_or_request(next_input):
            text_to_speech.speak("Goodbye")
            break

        pending_input = next_input


if __name__ == "__main__":
    main()
