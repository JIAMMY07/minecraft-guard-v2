from __future__ import annotations

import json
import shlex
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from minecraft_guard.config import GuardConfig
from minecraft_guard.windows.discovery import WindowInfo
from minecraft_guard.windows.process_info import ProcessInfo


@dataclass(frozen=True)
class InstanceMapping:
    name: str | None
    instance_dir: str | None
    latest_log: str | None
    source: str
    status: str
    launcher_hint: str | None = None
    reasons: list[str] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_manual_mappings(config: GuardConfig) -> list[dict[str, Any]]:
    if not config.instances_path.exists():
        return []
    with config.instances_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def resolve_instance(window: WindowInfo, config: GuardConfig) -> InstanceMapping:
    manual = match_manual_mapping(window, load_manual_mappings(config))
    if manual:
        return manual
    return resolve_from_process(window.process)


def match_manual_mapping(window: WindowInfo, mappings: list[dict[str, Any]]) -> InstanceMapping | None:
    for item in mappings:
        title_ok = contains_if_present(window.title, item.get("window_title_contains"))
        process_path = window.process.exe or ""
        path_ok = contains_if_present(process_path, item.get("process_path_contains"))
        if title_ok and path_ok:
            instance_dir = item.get("instance_dir")
            latest_log = item.get("latest_log") or latest_log_from_dir(instance_dir)
            return InstanceMapping(
                name=item.get("name"),
                instance_dir=instance_dir,
                latest_log=latest_log,
                source="manual",
                status=log_status(instance_dir, latest_log),
                launcher_hint=guess_launcher(window.process),
                reasons=["manual_mapping_matched"],
            )
    return None


def contains_if_present(value: str, needle: str | None) -> bool:
    if not needle:
        return True
    return needle.lower() in value.lower()


def resolve_from_process(process: ProcessInfo) -> InstanceMapping:
    reasons: list[str] = []
    instance_dir = parse_instance_dir(process)
    if instance_dir:
        reasons.append("process_command_line_instance_dir")
    elif process.cwd:
        cwd = Path(process.cwd)
        if (cwd / "logs").exists() or cwd.name == ".minecraft":
            instance_dir = str(cwd)
            reasons.append("process_cwd_instance_dir")

    latest_log = latest_log_from_dir(instance_dir)
    return InstanceMapping(
        name=Path(instance_dir).name if instance_dir else None,
        instance_dir=instance_dir,
        latest_log=latest_log,
        source="auto" if instance_dir else "none",
        status=log_status(instance_dir, latest_log),
        launcher_hint=guess_launcher(process),
        reasons=reasons or ["mapping_missing"],
    )


def parse_instance_dir(process: ProcessInfo) -> str | None:
    tokens = process.cmdline or shlex.split(process.command_line_text)
    for index, token in enumerate(tokens):
        if token == "--gameDir" and index + 1 < len(tokens):
            return normalize_path(tokens[index + 1])
        if token.startswith("--gameDir="):
            return normalize_path(token.split("=", 1)[1])
        if token.startswith("-Duser.dir="):
            return normalize_path(token.split("=", 1)[1])
    return infer_known_launcher_dir(tokens)


def infer_known_launcher_dir(tokens: list[str]) -> str | None:
    joined = " ".join(tokens)
    lower = joined.lower()
    markers = ["curseforge\\minecraft\\instances", "multimc\\instances", "prismlauncher\\instances"]
    for marker in markers:
        position = lower.find(marker)
        if position >= 0:
            tail = joined[position:]
            parts = Path(tail).parts
            if len(parts) >= 3:
                return str(Path(*parts[:3]))
    return None


def normalize_path(value: str) -> str:
    return str(Path(value.strip("\"'")).expanduser())


def latest_log_from_dir(instance_dir: str | None) -> str | None:
    if not instance_dir:
        return None
    return str(Path(instance_dir) / "logs" / "latest.log")


def log_status(instance_dir: str | None, latest_log: str | None) -> str:
    if not instance_dir:
        return "mapping_missing"
    if not latest_log:
        return "log_missing"
    if Path(latest_log).exists():
        return "ok"
    return "log_missing"


def guess_launcher(process: ProcessInfo) -> str | None:
    text = " ".join([process.exe or "", process.cwd or "", process.command_line_text]).lower()
    if "curseforge" in text:
        return "CurseForge"
    if "prismlauncher" in text or "prismlauncher" in text.replace(" ", ""):
        return "Prism Launcher"
    if "multimc" in text:
        return "MultiMC"
    if ".minecraft" in text:
        return "Vanilla/Java"
    if "java" in (process.name or "").lower() or "java" in (process.exe or "").lower():
        return "Java launcher"
    return None

