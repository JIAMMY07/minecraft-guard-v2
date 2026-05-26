from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class Cooldowns:
    until_by_window: dict[str, datetime] = field(default_factory=dict)

    def set(self, window_id: str, seconds: float) -> None:
        self.until_by_window[window_id] = datetime.now(timezone.utc) + timedelta(seconds=seconds)

    def active(self, window_id: str) -> bool:
        until = self.until_by_window.get(window_id)
        return bool(until and until > datetime.now(timezone.utc))

