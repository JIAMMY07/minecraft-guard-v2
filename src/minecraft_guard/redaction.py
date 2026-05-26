from __future__ import annotations

import re
from typing import Any


SENSITIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)(/login\s+)(\S+)"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(password\s*[=:]\s*)(\S+)"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(token\s*[=:]\s*)(\S+)"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(accessToken\s+)(\S+)"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(--accessToken\s+)(\S+)"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(--uuid\s+)([0-9a-f-]{16,})"), r"\1[REDACTED]"),
]


def redact_text(value: str) -> str:
    redacted = value
    for pattern, replacement in SENSITIVE_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_data(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return redact_sequence(value)
    if isinstance(value, tuple):
        return tuple(redact_data(item) for item in value)
    if isinstance(value, dict):
        return {key: redact_data(item) for key, item in value.items()}
    return value


def redact_sequence(values: list[Any]) -> list[Any]:
    redacted: list[Any] = []
    redact_next = False
    sensitive_flags = {"--accesstoken", "--uuid", "--xuid", "--clientid", "accesstoken", "token", "password"}
    for item in values:
        if redact_next:
            redacted.append("[REDACTED]")
            redact_next = False
            continue
        if isinstance(item, str) and item.lower() in sensitive_flags:
            redacted.append(item)
            redact_next = True
            continue
        redacted.append(redact_data(item))
    return redacted
