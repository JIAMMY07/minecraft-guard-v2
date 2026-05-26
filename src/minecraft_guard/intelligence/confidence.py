from __future__ import annotations

from minecraft_guard.intelligence.perception import PerceptionResult
from minecraft_guard.vision.states import VisualState


class ConfidenceEngine:
    """Combines hints conservatively.

    Log hints and history may lower confidence or request observation, but they
    never promote an uncertain visual state to a safe one.
    """

    def refine(self, perception: PerceptionResult) -> PerceptionResult:
        if perception.visual_state == VisualState.UNCERTAIN.value:
            return perception
        confidence = perception.confidence
        risk_flags = list(perception.risk_flags)
        reasons = list(perception.uncertainty_reasons)
        if perception.log_hint == "disconnect_recent":
            confidence = min(confidence, 0.65)
            risk_flags.append("recent_disconnect")
            reasons.append("log_hint_disconnect_recent")
        if perception.log_hint and perception.log_hint not in {"login_prompt_recent", "login_success_recent", "disconnect_recent"}:
            confidence = min(confidence, 0.7)
        return PerceptionResult(
            window_id=perception.window_id,
            visual_state=perception.visual_state,
            confidence=round(confidence, 3),
            detected_ui_objects=perception.detected_ui_objects,
            readable_text=perception.readable_text,
            log_hint=perception.log_hint,
            risk_flags=sorted(set(risk_flags)),
            uncertainty_reasons=sorted(set(reasons)),
            recommended_next_step=perception.recommended_next_step if confidence >= 0.75 else "observe_only",
            explanation=perception.explanation,
            evidence=perception.evidence,
        )

