from __future__ import annotations

from pathlib import Path


def read_text(_image_path: str | Path) -> list[str]:
    """OCR hook.

    The first delivery keeps OCR optional. Returning no text is safer than
    treating unavailable OCR as evidence.
    """
    return []

