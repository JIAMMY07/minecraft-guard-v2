from __future__ import annotations

from minecraft_guard.intelligence.perception import PerceptionResult
from minecraft_guard.intelligence.planner import Decision


class ExplanationEngine:
    def explain(self, perception: PerceptionResult, decision: Decision) -> str:
        parts = [
            f"Vedo {perception.visual_state} con confidenza {perception.confidence:.2f}.",
            f"Azione consigliata: {decision.action}.",
            f"Consentita: {'si' if decision.allowed else 'no'}.",
            f"Motivo: {decision.reason}",
        ]
        if perception.detected_ui_objects:
            objects = ", ".join(item.kind for item in perception.detected_ui_objects)
            parts.append(f"Oggetti UI: {objects}.")
        if perception.uncertainty_reasons:
            parts.append("Incertezza: " + ", ".join(perception.uncertainty_reasons) + ".")
        if decision.expected_after_state:
            parts.append(f"Mi aspetterei dopo: {decision.expected_after_state}.")
        return " ".join(parts)

