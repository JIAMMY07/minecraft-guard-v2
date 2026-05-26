from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

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
        from PIL import Image  # type: ignore

        with Image.open(path) as image:
            image = image.convert("RGB").resize((64, 36))
            pixels = list(image.getdata())
    except Exception as exc:
        return uncertain(f"image_unreadable:{type(exc).__name__}", {"path": str(path)})

    return classify_from_pixels(pixels, path)


def state_from_filename(path: Path) -> str | None:
    lowered = path.stem.lower()
    for hint, state in STATE_NAME_HINTS.items():
        if hint in lowered:
            return state
    return None


def classify_from_pixels(pixels: list[tuple[int, int, int]], path: Path) -> VisualDetection:
    if not pixels:
        return uncertain("empty_image", {"path": str(path)})
    brightness = [sum(pixel) / 3 for pixel in pixels]
    avg = sum(brightness) / len(brightness)
    very_dark = sum(1 for value in brightness if value < 35) / len(brightness)
    greenish = sum(1 for r, g, b in pixels if g > r + 25 and g > b + 10) / len(pixels)
    gray = sum(1 for r, g, b in pixels if abs(r - g) < 12 and abs(g - b) < 12 and 60 < r < 200) / len(pixels)
    red_text = sum(1 for r, g, b in pixels if r > 150 and g < 95 and b < 95) / len(pixels)
    orange_text = sum(1 for r, g, b in pixels if r > 175 and 60 < g < 160 and b < 95) / len(pixels)
    bright_text = sum(1 for r, g, b in pixels if r > 180 and g > 180 and b > 180) / len(pixels)
    bottom_pixels = pixels[-max(1, int(len(pixels) * 0.28)) :]
    bottom_red = sum(1 for r, g, b in bottom_pixels if r > 140 and g < 85 and b < 85) / len(bottom_pixels)
    bottom_dark = sum(1 for r, g, b in bottom_pixels if r < 55 and g < 55 and b < 55) / len(bottom_pixels)
    bottom_gray = sum(1 for r, g, b in bottom_pixels if abs(r - g) < 16 and abs(g - b) < 16 and 50 < r < 210) / len(bottom_pixels)
    color_bucket = Counter("green" if g > r + 25 and g > b + 10 else "gray" if abs(r - g) < 12 and abs(g - b) < 12 else "other" for r, g, b in pixels)
    evidence = {
        "average_brightness": round(avg, 2),
        "very_dark_ratio": round(very_dark, 3),
        "greenish_ratio": round(greenish, 3),
        "gray_ratio": round(gray, 3),
        "red_text_ratio": round(red_text, 3),
        "orange_text_ratio": round(orange_text, 3),
        "bright_text_ratio": round(bright_text, 3),
        "bottom_red_ratio": round(bottom_red, 3),
        "bottom_dark_ratio": round(bottom_dark, 3),
        "bottom_gray_ratio": round(bottom_gray, 3),
        "dominant_bucket": color_bucket.most_common(1)[0][0],
    }
    if red_text > 0.003 and very_dark > 0.035 and (bright_text > 0.006 or orange_text > 0.002):
        confidence = 0.82 if orange_text > 0.0006 else 0.76
        return VisualDetection(VisualState.LOGIN_PROMPT.value, confidence, objects_for_state(VisualState.LOGIN_PROMPT.value), [], [], evidence)
    if bottom_red > 0.006 and bottom_dark > 0.075 and bottom_gray > 0.09:
        return VisualDetection(VisualState.SURVIVAL_GAME.value, 0.8, objects_for_state(VisualState.SURVIVAL_GAME.value), [], [], evidence)
    if very_dark > 0.82:
        return VisualDetection(VisualState.LOADING.value, 0.76, [UIObject("dark_loading_screen", 0.76)], [], [], evidence)
    if greenish > 0.33 and gray > 0.08:
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
