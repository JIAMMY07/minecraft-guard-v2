from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class WindowState:
    window_id: str
    current_state: str | None = None
    last_state: str | None = None
    last_screenshot: str | None = None
    last_log_hint: str | None = None
    previous_action: str | None = None
    previous_outcome: str | None = None
    trust_level: float = 0.5

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorldModel:
    windows: dict[str, WindowState] = field(default_factory=dict)

    def update_observation(self, window_id: str, visual_state: str, screenshot: str | None, log_hint: str | None) -> WindowState:
        state = self.windows.get(window_id) or WindowState(window_id=window_id)
        state.last_state = state.current_state
        state.current_state = visual_state
        state.last_screenshot = screenshot
        state.last_log_hint = log_hint
        self.windows[window_id] = state
        return state

    def as_dict(self) -> dict[str, Any]:
        return {key: value.as_dict() for key, value in self.windows.items()}

