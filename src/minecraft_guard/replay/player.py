from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from minecraft_guard.vision.detector import detect_visual_state


@dataclass(frozen=True)
class ReplayComparison:
    hwnd: int | None
    screenshot_path: str | None
    old_state: str | None
    new_state: str
    old_confidence: float | None
    new_confidence: float
    matches: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def replay_report(report_path: str | Path) -> dict[str, Any]:
    path = Path(report_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    comparisons: list[ReplayComparison] = []
    for window in data.get("windows", []):
        screenshot = window.get("screenshot_path")
        detection = detect_visual_state(screenshot)
        old_state = window.get("perception", {}).get("visual_state") or window.get("diagnostic_state")
        old_conf = window.get("perception", {}).get("confidence")
        comparisons.append(
            ReplayComparison(
                hwnd=window.get("hwnd"),
                screenshot_path=screenshot,
                old_state=old_state,
                new_state=detection.state,
                old_confidence=old_conf,
                new_confidence=detection.confidence,
                matches=old_state == detection.state,
            )
        )
    return {
        "report_path": str(path),
        "windows": [item.as_dict() for item in comparisons],
        "matches": sum(1 for item in comparisons if item.matches),
        "total": len(comparisons),
    }
