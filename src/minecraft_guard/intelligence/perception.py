from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from minecraft_guard.instances.log_parser import LogHint
from minecraft_guard.vision.detector import VisualDetection
from minecraft_guard.vision.ocr import read_text
from minecraft_guard.vision.states import VisualState
from minecraft_guard.vision.ui_objects import UIObject


@dataclass(frozen=True)
class PerceptionResult:
    window_id: str
    visual_state: str
    confidence: float
    detected_ui_objects: list[UIObject]
    readable_text: list[str]
    log_hint: str | None
    risk_flags: list[str]
    uncertainty_reasons: list[str]
    recommended_next_step: str
    explanation: str
    evidence: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["detected_ui_objects"] = [item.as_dict() for item in self.detected_ui_objects]
        return data


def build_perception(
    window_id: str,
    screenshot_path: str | None,
    detection: VisualDetection,
    log_hint: LogHint | None,
    min_confidence: float = 0.75,
) -> PerceptionResult:
    text = read_text(screenshot_path) if screenshot_path else []
    confidence = detection.confidence
    reasons = list(detection.uncertainty_reasons)
    risk_flags = list(detection.risk_flags)
    if detection.state == VisualState.UNCERTAIN.value:
        confidence = min(confidence, 0.44)
        reasons.append("visual_state_uncertain")
    elif confidence < min_confidence:
        risk_flags.append("below_confidence_threshold")
        reasons.append("confidence_below_threshold")

    recommended = recommendation_for_state(detection.state, confidence, min_confidence)
    hint = log_hint.hint if log_hint else None
    evidence = dict(detection.evidence)
    if log_hint:
        evidence["log_hint"] = log_hint.as_dict()
    explanation = (
        f"Vedo {detection.state} con confidenza {confidence:.2f}. "
        f"Azione consigliata: {recommended}."
    )
    if reasons:
        explanation += " Motivi prudenza: " + ", ".join(sorted(set(reasons))) + "."
    return PerceptionResult(
        window_id=window_id,
        visual_state=detection.state,
        confidence=round(confidence, 3),
        detected_ui_objects=detection.ui_objects,
        readable_text=text,
        log_hint=hint,
        risk_flags=risk_flags,
        uncertainty_reasons=sorted(set(reasons)),
        recommended_next_step=recommended,
        explanation=explanation,
        evidence=evidence,
    )


def recommendation_for_state(state: str, confidence: float, min_confidence: float) -> str:
    if state == VisualState.UNCERTAIN.value or confidence < min_confidence:
        return "stop_uncertain"
    if state == VisualState.LOGIN_PROMPT.value:
        return "login"
    if state == VisualState.LOBBY.value:
        return "enter_survival"
    if state == VisualState.SURVIVAL_GAME.value:
        return "already_ok"
    return "observe_only"

