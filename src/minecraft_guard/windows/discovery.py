from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from minecraft_guard.windows.geometry import WindowGeometry
from minecraft_guard.windows.process_info import ProcessInfo, get_pid_for_hwnd, get_process_info


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    title: str
    pid: int | None
    process: ProcessInfo
    geometry: WindowGeometry
    visible: bool
    minimized: bool
    candidate_reason: str

    @property
    def window_id(self) -> str:
        return str(self.hwnd)

    @property
    def is_capture_candidate(self) -> bool:
        return self.visible and not self.minimized and self.geometry.is_readable_size

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["process"] = self.process.as_dict()
        data["geometry"] = self.geometry.as_dict()
        data["is_capture_candidate"] = self.is_capture_candidate
        return data


def discover_minecraft_windows() -> list[WindowInfo]:
    """Enumerate windows passively without focusing or changing desktops."""
    try:
        import win32gui  # type: ignore
    except Exception:
        return []

    windows: list[WindowInfo] = []

    def callback(hwnd: int, _extra: object) -> None:
        try:
            title = win32gui.GetWindowText(hwnd) or ""
            visible = bool(win32gui.IsWindowVisible(hwnd))
            minimized = bool(win32gui.IsIconic(hwnd))
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        except Exception:
            return

        pid = get_pid_for_hwnd(hwnd)
        process = get_process_info(pid)
        reason = minecraft_candidate_reason(title, process, visible=visible)
        if not reason:
            return
        windows.append(
            WindowInfo(
                hwnd=int(hwnd),
                title=title,
                pid=pid,
                process=process,
                geometry=WindowGeometry(int(left), int(top), int(right), int(bottom)),
                visible=visible,
                minimized=minimized,
                candidate_reason=reason,
            )
        )

    win32gui.EnumWindows(callback, None)
    return sorted(windows, key=lambda item: item.hwnd)


def minecraft_candidate_reason(title: str, process: ProcessInfo, visible: bool = True) -> str | None:
    lower_title = title.lower()
    cmd = process.command_line_text.lower()
    exe = (process.exe or "").lower()
    name = (process.name or "").lower()
    if "minecraft" in lower_title and visible:
        return "title_contains_minecraft"
    if (
        visible
        and title.strip()
        and not is_known_helper_window_title(title)
        and ("java" in exe or "java" in name)
        and ("minecraft" in cmd or "--gamedir" in cmd)
    ):
        return "java_process_mentions_minecraft"
    return None


def is_known_helper_window_title(title: str) -> bool:
    lowered = title.lower()
    helper_fragments = [
        "default ime",
        "msctfime ui",
        "wgl",
        "nvogldc",
        "glfw message window",
        "awttoolkitwindow",
    ]
    return any(fragment in lowered for fragment in helper_fragments)
