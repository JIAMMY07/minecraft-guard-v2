from __future__ import annotations

from pathlib import Path

from minecraft_guard.observer.snapshot import observe_once
from minecraft_guard.observer.snapshot import critical_reliability_reasons

from .conftest import make_png, make_window


def test_observe_once_no_input_focus_or_reputation(monkeypatch, config, tmp_path: Path) -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("observer must not call active input or focus APIs")

    monkeypatch.setattr("minecraft_guard.automation.executor.send_input", forbidden)
    monkeypatch.setattr("minecraft_guard.automation.executor.run_once", forbidden)

    def fake_capture(window, _output_path):
        return make_png(tmp_path / f"survival_game_{window.hwnd}.png"), []

    monkeypatch.setattr("minecraft_guard.observer.snapshot.capture_window_passive", fake_capture)
    snapshot = observe_once(config, discover=lambda: [make_window(1)])
    assert snapshot["passive"] is True
    assert snapshot["summary"]["by_state"] == {"survival_game": 1}


def test_four_windows_simulated_counts_and_reports(monkeypatch, config, tmp_path: Path) -> None:
    state_by_hwnd = {1: "lobby", 2: "survival_game", 3: "login_prompt", 4: "ambiguous"}

    def fake_capture(window, _output_path):
        return make_png(tmp_path / f"{state_by_hwnd[window.hwnd]}_{window.hwnd}.png"), []

    monkeypatch.setattr("minecraft_guard.observer.snapshot.capture_window_passive", fake_capture)
    windows = [make_window(hwnd) for hwnd in state_by_hwnd]
    snapshot = observe_once(config, discover=lambda: windows)
    assert snapshot["summary"]["total_windows"] == 4
    assert snapshot["summary"]["by_state"] == {"lobby": 1, "login_prompt": 1, "survival_game": 1, "uncertain": 1}
    assert Path(snapshot["report_files"]["json"]).exists()
    assert Path(snapshot["report_files"]["markdown"]).exists()
    assert "instance_mapping" in snapshot["windows"][0]


def test_capture_method_metadata_does_not_force_uncertain() -> None:
    reasons = ["print_window_blank_or_black", "capture_method:image_grab"]
    assert critical_reliability_reasons(reasons) == []
    assert critical_reliability_reasons(["window_minimized"]) == ["window_minimized"]
