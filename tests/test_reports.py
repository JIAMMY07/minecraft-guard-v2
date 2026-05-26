from __future__ import annotations

import json
from pathlib import Path

from minecraft_guard.observer.snapshot import observe_once
from minecraft_guard.replay.player import replay_report

from .conftest import make_png, make_window


def test_json_markdown_created_and_readable_offline(monkeypatch, config, tmp_path: Path) -> None:
    def fake_capture(window, _output_path):
        return make_png(tmp_path / f"login_prompt_{window.hwnd}.png"), []

    monkeypatch.setattr("minecraft_guard.observer.snapshot.capture_window_passive", fake_capture)
    snapshot = observe_once(config, discover=lambda: [make_window(7)])
    json_path = Path(snapshot["report_files"]["json"])
    markdown_path = Path(snapshot["report_files"]["markdown"])
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    assert loaded["summary"]["by_state"] == {"login_prompt": 1}
    assert "Minecraft Guard V2 Observer" in markdown
    assert "login_prompt" in markdown


def test_replay_reproduces_detector_result(monkeypatch, config, tmp_path: Path) -> None:
    def fake_capture(window, _output_path):
        return make_png(tmp_path / f"survival_game_{window.hwnd}.png"), []

    monkeypatch.setattr("minecraft_guard.observer.snapshot.capture_window_passive", fake_capture)
    snapshot = observe_once(config, discover=lambda: [make_window(8)])
    replay = replay_report(snapshot["report_files"]["json"])
    assert replay["matches"] == 1
    assert replay["total"] == 1

