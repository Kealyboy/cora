"""CORA voice loop: listen, route, speak."""

from __future__ import annotations

import router
import wake_word
# import speech_to_text
# import text_to_speech


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


def main() -> None:
    usage_count = 0

    while True:
        if wake_word.listen_for_wake_word():
            print("CORA activated")

        # user_input = speech_to_text.listen()
        user_input = input("You: ")
        if not user_input.strip():
            continue

        print(f"You said: {user_input}")
        if _wants_exit_session(user_input):
            # text_to_speech.speak("Goodbye")
            print("Goodbye")
            break

        usage_count += 1
        response = router.route(user_input, usage_count)
        print(response)
        # text_to_speech.speak(response)


if __name__ == "__main__":
    main()
