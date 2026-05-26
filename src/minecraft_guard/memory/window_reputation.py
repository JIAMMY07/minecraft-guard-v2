from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WindowReputation:
    window_id: str
    score: float = 0.5

    def register_failure(self) -> None:
        self.score = max(0.0, self.score - 0.1)

    def register_success(self) -> None:
        self.score = min(1.0, self.score + 0.05)

