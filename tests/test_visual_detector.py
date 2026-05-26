from __future__ import annotations

from pathlib import Path

from minecraft_guard.vision.detector import detect_visual_state

from .conftest import make_png


def test_screenshot_login_prompt_confident(tmp_path: Path) -> None:
    image = make_png(tmp_path / "sample_login_prompt.png")
    result = detect_visual_state(image)
    assert result.state == "login_prompt"
    assert result.confidence >= 0.9


def test_screenshot_lobby_confident(tmp_path: Path) -> None:
    image = make_png(tmp_path / "sample_lobby.png")
    assert detect_visual_state(image).state == "lobby"


def test_screenshot_survival_game_confident(tmp_path: Path) -> None:
    image = make_png(tmp_path / "sample_survival_game.png")
    assert detect_visual_state(image).state == "survival_game"


def test_screenshot_ambiguous_uncertain(tmp_path: Path) -> None:
    image = make_png(tmp_path / "sample_ambiguous.png")
    result = detect_visual_state(image)
    assert result.state == "uncertain"
    assert "filename_marks_uncertain_or_negative" in result.uncertainty_reasons


def test_desktop_non_minecraft_uncertain(tmp_path: Path) -> None:
    image = make_png(tmp_path / "non_minecraft_desktop.png")
    assert detect_visual_state(image).state == "uncertain"


def test_visual_login_prompt_colors_detected(tmp_path: Path) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (640, 360), (120, 120, 110))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 210, 640, 300), fill=(20, 20, 20))
    for idx in range(18):
        x = 20 + idx * 18
        draw.rectangle((x, 230, x + 10, 242), fill=(230, 30, 30))
        draw.rectangle((x, 255, x + 12, 267), fill=(235, 235, 235))
    draw.rectangle((240, 150, 390, 180), fill=(230, 110, 20))
    path = tmp_path / "visual_prompt.png"
    image.save(path)
    result = detect_visual_state(path)
    assert result.state == "login_prompt"
    assert result.confidence >= 0.75


def test_visual_hotbar_detects_survival_game(tmp_path: Path) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (640, 360), (90, 120, 80))
    draw = ImageDraw.Draw(image)
    draw.rectangle((180, 305, 460, 350), fill=(25, 25, 25))
    for idx in range(9):
        x = 190 + idx * 29
        draw.rectangle((x, 315, x + 22, 342), fill=(90, 90, 90))
    for idx in range(10):
        x = 190 + idx * 16
        draw.rectangle((x, 285, x + 10, 296), fill=(210, 20, 20))
    path = tmp_path / "visual_hotbar.png"
    image.save(path)
    result = detect_visual_state(path)
    assert result.state == "survival_game"
