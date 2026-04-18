"""CORA voice loop: listen, route, speak."""

from __future__ import annotations

import router
import speech_to_text
import text_to_speech
import wake_word
from state_manager import ConversationState, StateManager


def _speak(state: StateManager, text: str) -> bool:
    """
    TTS in SPEAKING state. Wake word stays active during playback (see text_to_speech.speak).
    Returns True if playback finished, False if interrupted by wake word (state already IDLE).
    """
    state.set_state(ConversationState.SPEAKING)
    wake_word.set_microphone_muted(False)
    completed = True
    try:
        completed = text_to_speech.speak(text, state)
    finally:
        wake_word.set_microphone_muted(False)
        if completed:
            state.set_state(ConversationState.IDLE)
    return completed


def _sounds_like_follow_up(text: str) -> bool:
    """Return True when text looks like a real follow-up question/request."""
    t = text.strip()
    if not t:
        return False

    normalized = t.lower().strip().strip(".,!?")
    words = normalized.split()
    if not words:
        return False

    short_acknowledgements = {
        "ok",
        "okay",
        "thanks",
        "thank you",
        "cool",
        "nice",
        "great",
        "yep",
        "yeah",
    }
    if normalized in short_acknowledgements:
        return False

    if "?" in t:
        return True

    request_starters = {
        "turn",
        "set",
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
        "can",
        "could",
        "would",
        "will",
        "please",
    }
    if words[0] in request_starters:
        return True

    return len(words) >= 2


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
    pending_input: str | None = None
    state = StateManager()
    skip_wake = False

    while True:
        if pending_input is None:
            if not skip_wake:
                if wake_word.listen_for_wake_word():
                    print("CORA activated")
            else:
                skip_wake = False
                print("CORA activated")
            state.set_state(ConversationState.LISTENING)
            user_input = speech_to_text.listen()
            if not user_input.strip():
                state.set_state(ConversationState.IDLE)
                continue
            state.set_state(ConversationState.PROCESSING)
        else:
            state.set_state(ConversationState.LISTENING)
            state.set_state(ConversationState.PROCESSING)
            user_input = pending_input
            pending_input = None

        print(f"You said: {user_input}")
        if _wants_exit_session(user_input):
            completed = _speak(state, "Goodbye")
            print("Goodbye")
            if completed:
                break
            skip_wake = True
            continue

        usage_count += 1
        response = router.route(user_input, usage_count)
        print(response)
        completed = _speak(state, response)
        if not completed:
            skip_wake = True
            continue

        state.set_state(ConversationState.LISTENING)
        follow_up = speech_to_text.listen(max_wait_seconds=5, verbose=False)
        if not follow_up.strip():
            state.set_state(ConversationState.IDLE)
        else:
            state.set_state(ConversationState.PROCESSING)
            if _sounds_like_follow_up(follow_up):
                pending_input = follow_up
            state.set_state(ConversationState.IDLE)


if __name__ == "__main__":
    main()
