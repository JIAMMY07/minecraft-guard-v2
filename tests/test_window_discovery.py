from __future__ import annotations

from minecraft_guard.windows.discovery import minecraft_candidate_reason
from minecraft_guard.windows.process_info import ProcessInfo


def test_window_discovery_candidate_by_title() -> None:
    process = ProcessInfo(pid=1, exe="C:/Java/bin/javaw.exe", name="javaw.exe", cmdline=["javaw"])
    assert minecraft_candidate_reason("Minecraft 1.20", process) == "title_contains_minecraft"


def test_window_discovery_rejects_browser_negative_sample() -> None:
    process = ProcessInfo(pid=2, exe="C:/Browser/browser.exe", name="browser.exe", cmdline=["browser"])
    assert minecraft_candidate_reason("News", process) is None
