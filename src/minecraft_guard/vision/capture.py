from __future__ import annotations

from pathlib import Path

from minecraft_guard.windows.discovery import WindowInfo


def capture_window_passive(window: WindowInfo, output_path: Path) -> tuple[Path | None, list[str]]:
    """Capture a window rectangle without focusing, clicking, or moving it."""
    reasons: list[str] = []
    if not window.visible:
        return None, ["window_not_visible"]
    if window.minimized:
        return None, ["window_minimized"]
    if not window.geometry.is_readable_size:
        return None, ["window_too_small"]

    try:
        from PIL import ImageGrab  # type: ignore
    except Exception:
        return None, ["pillow_imagegrab_unavailable"]

    bbox = (window.geometry.left, window.geometry.top, window.geometry.right, window.geometry.bottom)
    try:
        image = ImageGrab.grab(bbox=bbox)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        return output_path, reasons
    except Exception as exc:
        return None, [f"capture_failed:{type(exc).__name__}"]

