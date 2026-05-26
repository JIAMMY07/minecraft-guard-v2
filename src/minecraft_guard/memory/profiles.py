from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InstanceProfile:
    name: str
    launcher_hint: str | None = None
    states_seen: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def remember_state(self, state: str) -> None:
        self.states_seen.append(state)
        self.states_seen = self.states_seen[-20:]

