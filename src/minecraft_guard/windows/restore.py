from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RestoreResult:
    hwnd: int
    title: str
    was_minimized: bool
    restored: bool
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def restore_minimized_minecraft_windows() -> list[RestoreResult]:
    """Restore minimized Minecraft windows as an explicit active pre-step."""
    try:
        import win32con  # type: ignore
        import win32gui  # type: ignore
    except Exception as exc:
        return [RestoreResult(0, "", False, False, f"win32_unavailable:{type(exc).__name__}")]

    results: list[RestoreResult] = []

    def callback(hwnd: int, _extra: object) -> None:
        title = win32gui.GetWindowText(hwnd) or ""
        if "minecraft" not in title.lower():
            return
        minimized = bool(win32gui.IsIconic(hwnd))
        if not minimized:
            results.append(RestoreResult(int(hwnd), title, False, False))
            return
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            results.append(RestoreResult(int(hwnd), title, True, True))
        except Exception as exc:
            results.append(RestoreResult(int(hwnd), title, True, False, type(exc).__name__))

    win32gui.EnumWindows(callback, None)
    return results

