from __future__ import annotations

from minecraft_guard.vision.states import VisualState


ALLOWED_ACTIVE_TRANSITIONS = {
    VisualState.LOGIN_PROMPT.value: "login",
    VisualState.LOBBY.value: "enter_survival",
    VisualState.SURVIVAL_GAME.value: "already_ok",
}


def action_for_state(state: str) -> str:
    return ALLOWED_ACTIVE_TRANSITIONS.get(state, "stop_uncertain")

