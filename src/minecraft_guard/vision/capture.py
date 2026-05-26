from __future__ import annotations

import ctypes
from pathlib import Path

from minecraft_guard.windows.discovery import WindowInfo


def capture_window_passive(window: WindowInfo, output_path: Path) -> tuple[Path | None, list[str]]:
    """Capture a window without focusing, clicking, or moving it.

    PrintWindow is attempted first because it can capture many visible but
    covered windows. ImageGrab remains the fallback for OpenGL windows where
    PrintWindow often returns a black or stale frame.
    """
    reasons: list[str] = []
    if not window.visible:
        return None, ["window_not_visible"]
    if window.minimized:
        return None, ["window_minimized"]
    if not window.geometry.is_readable_size:
        return None, ["window_too_small"]

    print_window_path, print_window_reasons = capture_with_print_window(window.hwnd, output_path)
    if print_window_path:
        return print_window_path, ["capture_method:print_window"]
    reasons.extend(print_window_reasons)

    try:
        from PIL import ImageGrab  # type: ignore
    except Exception:
        return None, reasons + ["pillow_imagegrab_unavailable"]

    bbox = (window.geometry.left, window.geometry.top, window.geometry.right, window.geometry.bottom)
    try:
        image = ImageGrab.grab(bbox=bbox)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        return output_path, reasons + ["capture_method:image_grab"]
    except Exception as exc:
        return None, reasons + [f"capture_failed:{type(exc).__name__}"]


def capture_with_print_window(hwnd: int, output_path: Path) -> tuple[Path | None, list[str]]:
    try:
        import win32con  # type: ignore
        import win32gui  # type: ignore
        import win32ui  # type: ignore
        from PIL import Image  # type: ignore
    except Exception as exc:
        return None, [f"print_window_unavailable:{type(exc).__name__}"]

    hwnd_dc = None
    src_dc = None
    mem_dc = None
    bitmap = None
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = max(0, right - left)
        height = max(0, bottom - top)
        if width < 1 or height < 1:
            return None, ["print_window_empty_geometry"]
        if width < 320 or height < 240:
            return None, ["print_window_too_small"]

        hwnd_dc = win32gui.GetWindowDC(hwnd)
        src_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        mem_dc = src_dc.CreateCompatibleDC()
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(src_dc, width, height)
        mem_dc.SelectObject(bitmap)

        result = ctypes.windll.user32.PrintWindow(hwnd, mem_dc.GetSafeHdc(), 2)
        if result != 1:
            result = ctypes.windll.user32.PrintWindow(hwnd, mem_dc.GetSafeHdc(), 0)
        if result != 1:
            return None, ["print_window_failed"]

        info = bitmap.GetInfo()
        bits = bitmap.GetBitmapBits(True)
        image = Image.frombuffer(
            "RGB",
            (info["bmWidth"], info["bmHeight"]),
            bits,
            "raw",
            "BGRX",
            0,
            1,
        )
        if is_blank_capture(image):
            return None, ["print_window_blank_or_black"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        return output_path, []
    except Exception as exc:
        return None, [f"print_window_failed:{type(exc).__name__}"]
    finally:
        if bitmap is not None:
            try:
                win32gui.DeleteObject(bitmap.GetHandle())
            except Exception:
                pass
        if mem_dc is not None:
            try:
                mem_dc.DeleteDC()
            except Exception:
                pass
        if src_dc is not None:
            try:
                src_dc.DeleteDC()
            except Exception:
                pass
        if hwnd_dc is not None:
            try:
                win32gui.ReleaseDC(hwnd, hwnd_dc)
            except Exception:
                pass


def is_blank_capture(image: object) -> bool:
    try:
        small = image.convert("RGB").resize((32, 18))  # type: ignore[attr-defined]
        pixels = list(small.getdata())
    except Exception:
        return False
    if not pixels:
        return True
    brightness = [sum(pixel) / 3 for pixel in pixels]
    avg = sum(brightness) / len(brightness)
    spread = max(brightness) - min(brightness)
    return (avg < 3 or avg > 252) and spread < 4
