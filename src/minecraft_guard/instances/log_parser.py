from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from minecraft_guard.redaction import redact_text


@dataclass(frozen=True)
class LogHint:
    hint: str | None
    confidence: float
    evidence: list[str]
    status: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def parse_latest_log_hint(latest_log: str | None, max_lines: int = 120) -> LogHint:
    if not latest_log:
        return LogHint(None, 0.0, [], "log_missing")
    path = Path(latest_log)
    if not path.exists():
        return LogHint(None, 0.0, [], "log_missing")
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]
    except Exception as exc:
        return LogHint(None, 0.0, [], f"log_unreadable:{type(exc).__name__}")

    joined = "\n".join(lines).lower()
    evidence: list[str] = []
    hint: str | None = None
    confidence = 0.0
    if "/login" in joined or "please login" in joined or "login with" in joined:
        hint = "login_prompt_recent"
        confidence = 0.55
    elif "joined the game" in joined or "logged in" in joined:
        hint = "login_success_recent"
        confidence = 0.45
    elif "disconnect" in joined or "timed out" in joined:
        hint = "disconnect_recent"
        confidence = 0.45

    for line in lines[-12:]:
        clean = redact_text(line)
        lowered = clean.lower()
        if any(word in lowered for word in ("login", "joined", "disconnect", "timed out")):
            evidence.append(clean)
    return LogHint(hint, confidence, evidence[-5:], "ok")
