from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from minecraft_guard.config import GuardConfig
from minecraft_guard.windows.discovery import WindowInfo
from minecraft_guard.windows.geometry import WindowGeometry
from minecraft_guard.windows.process_info import ProcessInfo


@pytest.fixture
def config(tmp_path: Path) -> GuardConfig:
    raw = {
        "observer": {"min_confidence": 0.75},
        "automation": {"enabled": False, "min_confidence": 0.9},
        "paths": {
            "screenshots": "data/screenshots",
            "reports": "data/reports",
            "replay": "data/replay",
            "labels": "data/labels",
        },
    }
    cfg = GuardConfig(tmp_path, raw, tmp_path / "config" / "default_config.json", tmp_path / "config" / "instances.json")
    cfg.ensure_dirs()
    return cfg


def make_window(hwnd: int, title: str = "Minecraft 1.20") -> WindowInfo:
    return WindowInfo(
        hwnd=hwnd,
        title=title,
        pid=1000 + hwnd,
        process=ProcessInfo(pid=1000 + hwnd, exe="C:/Java/bin/javaw.exe", name="javaw.exe", cwd=None, cmdline=["javaw", "--gameDir", f"C:/Instances/{hwnd}"]),
        geometry=WindowGeometry(0, 0, 1280, 720),
        visible=True,
        minimized=False,
        candidate_reason="test",
    )


def make_png(path: Path, color: tuple[int, int, int] = (20, 120, 20)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (128, 72), color).save(path)
    return path

