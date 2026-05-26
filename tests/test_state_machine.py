from __future__ import annotations

from minecraft_guard.intelligence.confidence import ConfidenceEngine
from minecraft_guard.intelligence.explanations import ExplanationEngine
from minecraft_guard.intelligence.perception import PerceptionResult
from minecraft_guard.intelligence.planner import Planner
from minecraft_guard.intelligence.verifier import Verifier
from minecraft_guard.intelligence.world_model import WorldModel
from minecraft_guard.vision.ui_objects import UIObject


def perception(state: str, confidence: float, recommended: str | None = None) -> PerceptionResult:
    return PerceptionResult(
        window_id="1",
        visual_state=state,
        confidence=confidence,
        detected_ui_objects=[UIObject("test", confidence)] if state != "uncertain" else [],
        readable_text=[],
        log_hint=None,
        risk_flags=[],
        uncertainty_reasons=[] if state != "uncertain" else ["visual_state_uncertain"],
        recommended_next_step=recommended or ("stop_uncertain" if state == "uncertain" else "already_ok"),
        explanation="test",
        evidence={},
    )


def test_planner_does_not_authorize_uncertain() -> None:
    decision = Planner(passive_only=False).decide(perception("uncertain", 0.1), WorldModel())
    assert decision.action == "stop_uncertain"
    assert decision.allowed is False


def test_verifier_blocks_mismatch(tmp_path) -> None:
    from .conftest import make_png

    image = make_png(tmp_path / "after_lobby.png")
    result = Verifier().verify_screenshot(image, "survival_game")
    assert result.ok is False
    assert result.failure_reason == "state_after_action_mismatch"


def test_explanation_engine_produces_readable_reason() -> None:
    p = perception("survival_game", 0.92, "already_ok")
    decision = Planner(passive_only=True).decide(p, WorldModel())
    text = ExplanationEngine().explain(p, decision)
    assert "Vedo survival_game" in text
    assert "Motivo:" in text


def test_confidence_engine_does_not_promote_uncertain() -> None:
    p = perception("uncertain", 0.1, "stop_uncertain")
    refined = ConfidenceEngine().refine(p)
    assert refined.visual_state == "uncertain"
    assert refined.confidence == 0.1


def test_1000_synthetic_scenarios_zero_unsafe_inputs() -> None:
    planner = Planner(passive_only=False)
    states = ["login_prompt", "lobby", "survival_game", "pause_menu", "loading", "chat_open", "server_selector", "menu_mode", "uncertain"]
    unsafe = []
    negative_or_ambiguous = 0
    for index in range(1000):
        state = states[(index * 7) % len(states)]
        if index < 300:
            state = "uncertain" if index % 2 == 0 else "server_selector"
            negative_or_ambiguous += 1
        recommended = {
            "login_prompt": "login",
            "lobby": "enter_survival",
            "survival_game": "already_ok",
        }.get(state, "stop_uncertain" if state == "uncertain" else "observe_only")
        p = perception(state, 0.93 if state in {"login_prompt", "lobby", "survival_game"} else 0.4, recommended)
        decision = planner.decide(p, WorldModel())
        if (
            state in {"uncertain", "server_selector", "loading", "chat_open", "menu_mode", "pause_menu"}
            and decision.allowed
            and decision.action in {"login", "enter_survival"}
        ):
            unsafe.append((index, state, decision.action))
    assert negative_or_ambiguous >= 300
    assert unsafe == []
