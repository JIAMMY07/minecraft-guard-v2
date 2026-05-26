from __future__ import annotations

import json
from pathlib import Path

from minecraft_guard.instances.log_parser import parse_latest_log_hint
from minecraft_guard.instances.resolver import resolve_instance
from minecraft_guard.redaction import redact_data

from .conftest import make_window


def test_manual_mapping_has_priority(config, tmp_path: Path) -> None:
    config.instances_path.parent.mkdir(parents=True, exist_ok=True)
    log = tmp_path / "Manual" / "logs" / "latest.log"
    log.parent.mkdir(parents=True)
    log.write_text("Please /login secret-password\n", encoding="utf-8")
    config.instances_path.write_text(
        json.dumps(
            [
                {
                    "name": "Manual",
                    "window_title_contains": "Minecraft",
                    "process_path_contains": "javaw.exe",
                    "instance_dir": str(log.parent.parent),
                    "latest_log": str(log),
                }
            ]
        ),
        encoding="utf-8",
    )
    mapping = resolve_instance(make_window(1), config)
    assert mapping.source == "manual"
    assert mapping.status == "ok"


def test_log_hint_redacts_login_password(tmp_path: Path) -> None:
    log = tmp_path / "latest.log"
    log.write_text("[CHAT] /login hunter2\n", encoding="utf-8")
    hint = parse_latest_log_hint(str(log))
    assert hint.hint == "login_prompt_recent"
    assert "hunter2" not in "\n".join(hint.evidence)


def test_redaction_redacts_command_line_token_values() -> None:
    redacted = redact_data(["javaw", "--uuid", "abc123", "--accessToken", "secret-token", "--gameDir", "C:/ok"])
    assert redacted == ["javaw", "--uuid", "[REDACTED]", "--accessToken", "[REDACTED]", "--gameDir", "C:/ok"]
