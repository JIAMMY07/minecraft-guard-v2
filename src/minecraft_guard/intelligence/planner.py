from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from minecraft_guard.intelligence.perception import PerceptionResult
from minecraft_guard.intelligence.world_model import WorldModel
from minecraft_guard.vision.states import VisualState


@dataclass(frozen=True)
class Decision:
    action: str
    allowed: bool
    confidence: float
    reason: str
    expected_after_state: str | None
    required_preconditions: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


PASSIVE_DECISIONS = {"observe_only", "wait", "already_ok", "stop_uncertain"}


class Planner:
    def __init__(self, min_active_confidence: float = 0.9, passive_only: bool = True) -> None:
        self.min_active_confidence = min_active_confidence
        self.passive_only = passive_only

    def decide(self, perception: PerceptionResult, world_model: WorldModel) -> Decision:
        if perception.visual_state == VisualState.UNCERTAIN.value:
            return Decision(
                "stop_uncertain",
                False,
                perception.confidence,
                "Stato visivo incerto: osservo e non invio input.",
                None,
                ["visual_state_confident"],
            )
        if perception.confidence < self.min_active_confidence and perception.recommended_next_step in {"login", "enter_survival"}:
            return Decision(
                "observe_only",
                False,
                perception.confidence,
                "Confidenza sotto soglia per azioni attive.",
                None,
                ["confidence_high_enough"],
            )
        if self.passive_only and perception.recommended_next_step not in PASSIVE_DECISIONS:
            return Decision(
                perception.recommended_next_step,
                False,
                perception.confidence,
                "Modalita osservatore: la diagnosi e pronta, ma l'azione attiva e disabilitata.",
                expected_after(perception.recommended_next_step),
                preconditions_for(perception.recommended_next_step),
            )
        action = perception.recommended_next_step
        allowed = action in PASSIVE_DECISIONS
        reason = "Decisione compatibile con lo stato osservato corrente."
        if action == "already_ok":
            reason = "La finestra sembra gia in survival_game; nessuna azione necessaria."
        return Decision(action, allowed, perception.confidence, reason, expected_after(action), preconditions_for(action))


def expected_after(action: str) -> str | None:
    if action == "login":
        return VisualState.LOBBY.value
    if action == "enter_survival":
        return VisualState.SURVIVAL_GAME.value
    return None


def preconditions_for(action: str) -> list[str]:
    if action == "login":
        return ["foreground_verified", "geometry_stable", "visual_state_login_prompt", "confidence_high_enough"]
    if action == "enter_survival":
        return ["foreground_verified", "geometry_stable", "visual_state_lobby", "confidence_high_enough"]
    return ["passive_observation"]

