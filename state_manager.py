"""Conversation state tracking for CORA."""

from __future__ import annotations

from enum import Enum, auto


class ConversationState(Enum):
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()


# Allowed edges: from_state -> {to_state, ...}
# SPEAKING may only go to IDLE; LISTENING must be reached from IDLE (not from SPEAKING).
_VALID_TRANSITIONS: dict[ConversationState, frozenset[ConversationState]] = {
    ConversationState.IDLE: frozenset({ConversationState.LISTENING}),
    ConversationState.LISTENING: frozenset(
        {ConversationState.PROCESSING, ConversationState.IDLE}
    ),
    ConversationState.PROCESSING: frozenset(
        {ConversationState.SPEAKING, ConversationState.IDLE}
    ),
    ConversationState.SPEAKING: frozenset({ConversationState.IDLE}),
}


class StateManager:
    def __init__(self) -> None:
        self._state: ConversationState = ConversationState.IDLE

    def get_state(self) -> ConversationState:
        return self._state

    def set_state(self, new_state: ConversationState) -> None:
        if new_state == self._state:
            return
        allowed = _VALID_TRANSITIONS.get(self._state, frozenset())
        if new_state not in allowed:
            raise ValueError(
                f"Invalid state transition: {self._state.name} -> {new_state.name}"
            )
        old = self._state
        self._state = new_state
        print(f"CORA state: {old.name} -> {new_state.name}")

    def is_idle(self) -> bool:
        return self._state == ConversationState.IDLE

    def is_listening(self) -> bool:
        return self._state == ConversationState.LISTENING

    def is_speaking(self) -> bool:
        return self._state == ConversationState.SPEAKING

    def is_processing(self) -> bool:
        return self._state == ConversationState.PROCESSING
