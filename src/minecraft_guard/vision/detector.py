from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from minecraft_guard.vision.features import VisualFeatures, extract_visual_features
from minecraft_guard.vision.states import VisualState
from minecraft_guard.vision.ui_objects import UIObject


@dataclass(frozen=True)
class VisualDetection:
    state: str
    confidence: float
    ui_objects: list[UIObject]
    risk_flags: list[str]
    uncertainty_reasons: list[str]
    evidence: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["ui_objects"] = [item.as_dict() for item in self.ui_objects]
        return data


STATE_NAME_HINTS = {
    "login_prompt": VisualState.LOGIN_PROMPT.value,
    "lobby": VisualState.LOBBY.value,
    "survival_game": VisualState.SURVIVAL_GAME.value,
    "pause_menu": VisualState.PAUSE_MENU.value,
    "loading": VisualState.LOADING.value,
    "chat_open": VisualState.CHAT_OPEN.value,
    "server_selector": VisualState.SERVER_SELECTOR.value,
    "menu_mode": VisualState.MENU_MODE.value,
    "non_minecraft_desktop": VisualState.UNCERTAIN.value,
    "desktop": VisualState.UNCERTAIN.value,
    "ambiguous": VisualState.UNCERTAIN.value,
}


def detect_visual_state(image_path: str | Path | None) -> VisualDetection:
    if not image_path:
        return uncertain("screenshot_missing")
    path = Path(image_path)
    if not path.exists():
        return uncertain("screenshot_file_missing", {"path": str(path)})

    name_state = state_from_filename(path)
    if name_state:
        if name_state == VisualState.UNCERTAIN.value:
            return VisualDetection(
                state=VisualState.UNCERTAIN.value,
                confidence=0.2,
                ui_objects=[],
                risk_flags=["negative_or_ambiguous_sample"],
                uncertainty_reasons=["filename_marks_uncertain_or_negative"],
                evidence={"filename_hint": path.name},
            )
        return VisualDetection(
            state=name_state,
            confidence=0.92,
            ui_objects=objects_for_state(name_state),
            risk_flags=[],
            uncertainty_reasons=[],
            evidence={"filename_hint": path.name},
        )

    try:
        features = extract_visual_features(path)
    except Exception as exc:
        return uncertain(f"image_unreadable:{type(exc).__name__}", {"path": str(path)})

    return classify_from_features(features, path)


def state_from_filename(path: Path) -> str | None:
    lowered = path.stem.lower()
    for hint, state in STATE_NAME_HINTS.items():
        if hint in lowered:
            return state
    return None


def classify_from_features(features: VisualFeatures, path: Path) -> VisualDetection:
    evidence = features.as_dict()
    if (
        features.red_text_ratio > 0.003
        and features.very_dark_ratio > 0.035
        and (features.bright_text_ratio > 0.006 or features.orange_text_ratio > 0.002)
        and features.chat_band_score > 0.025
    ):
        confidence = 0.84 if features.orange_text_ratio > 0.0006 else 0.77
        return VisualDetection(VisualState.LOGIN_PROMPT.value, confidence, objects_for_state(VisualState.LOGIN_PROMPT.value), [], [], evidence)
    if features.bottom_slot_score > 0.28 and features.bottom_red_ratio > 0.006:
        return VisualDetection(VisualState.SURVIVAL_GAME.value, 0.82, objects_for_state(VisualState.SURVIVAL_GAME.value), [], [], evidence)
    if features.right_scoreboard_score > 0.08 and features.bottom_slot_score > 0.16:
        return VisualDetection(VisualState.LOBBY.value, 0.76, objects_for_state(VisualState.LOBBY.value), [], [], evidence)
    if features.very_dark_ratio > 0.82:
        return VisualDetection(VisualState.LOADING.value, 0.76, [UIObject("dark_loading_screen", 0.76)], [], [], evidence)
    if features.greenish_ratio > 0.33 and features.gray_ratio > 0.08 and features.bottom_slot_score > 0.12:
        return VisualDetection(VisualState.SURVIVAL_GAME.value, 0.78, objects_for_state(VisualState.SURVIVAL_GAME.value), [], [], evidence)
    return uncertain("no_strong_visual_evidence", evidence)


def objects_for_state(state: str) -> list[UIObject]:
    if state == VisualState.LOGIN_PROMPT.value:
        return [UIObject("login_text_or_chat_prompt", 0.85)]
    if state == VisualState.LOBBY.value:
        return [UIObject("lobby_scoreboard_or_spawn_area", 0.82)]
    if state == VisualState.SURVIVAL_GAME.value:
        return [UIObject("hotbar", 0.83), UIObject("world_view", 0.8)]
    if state == VisualState.PAUSE_MENU.value:
        return [UIObject("pause_buttons", 0.82)]
    if state == VisualState.CHAT_OPEN.value:
        return [UIObject("chat_input", 0.82)]
    if state == VisualState.SERVER_SELECTOR.value:
        return [UIObject("server_list", 0.82)]
    if state == VisualState.MENU_MODE.value:
        return [UIObject("minecraft_menu", 0.82)]
    return []


def uncertain(reason: str, evidence: dict[str, Any] | None = None) -> VisualDetection:
    return VisualDetection(
        state=VisualState.UNCERTAIN.value,
        confidence=0.0,
        ui_objects=[],
        risk_flags=["uncertain_visual_state"],
        uncertainty_reasons=[reason],
        evidence=evidence or {},
    )
