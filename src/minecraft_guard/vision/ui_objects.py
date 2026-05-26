from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class UIObject:
    kind: str
    confidence: float
    bbox: tuple[int, int, int, int] | None = None
    evidence: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

