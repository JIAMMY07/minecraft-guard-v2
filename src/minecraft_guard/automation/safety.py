from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from minecraft_guard.intelligence.perception import PerceptionResult


@dataclass(frozen=True)
class SafetyCheck:
    ok: bool
    reasons: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def passive_observer_allows_input() -> bool:
    return False


def validate_before_input(perception: PerceptionResult, required_state: str, min_confidence: float) -> SafetyCheck:
    reasons: list[str] = []
    if perception.visual_state != required_state:
        reasons.append("visual_state_mismatch")
    if perception.confidence < min_confidence:
        reasons.append("confidence_below_threshold")
    if perception.uncertainty_reasons:
        reasons.append("uncertainty_present")
    return SafetyCheck(ok=not reasons, reasons=reasons)

