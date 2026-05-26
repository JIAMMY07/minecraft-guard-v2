from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from minecraft_guard.vision.detector import detect_visual_state


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    expected_state: str | None
    actual_state: str
    confidence: float
    failure_reason: str | None
    screenshot_path: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class Verifier:
    def verify_screenshot(self, screenshot_path: str | Path, expected_state: str | None) -> VerificationResult:
        detection = detect_visual_state(screenshot_path)
        ok = bool(expected_state and detection.state == expected_state)
        return VerificationResult(
            ok=ok,
            expected_state=expected_state,
            actual_state=detection.state,
            confidence=detection.confidence,
            failure_reason=None if ok else "state_after_action_mismatch",
            screenshot_path=str(screenshot_path),
        )
