from __future__ import annotations

from enum import StrEnum


class VisualState(StrEnum):
    LOGIN_PROMPT = "login_prompt"
    LOBBY = "lobby"
    SURVIVAL_GAME = "survival_game"
    PAUSE_MENU = "pause_menu"
    LOADING = "loading"
    CHAT_OPEN = "chat_open"
    SERVER_SELECTOR = "server_selector"
    MENU_MODE = "menu_mode"
    UNCERTAIN = "uncertain"


DIAGNOSTIC_STATES = [state.value for state in VisualState]

