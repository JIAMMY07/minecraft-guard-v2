from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class GuardConfig:
    project_root: Path
    raw: dict[str, Any]
    config_path: Path
    instances_path: Path

    @property
    def min_confidence(self) -> float:
        return float(self.raw.get("observer", {}).get("min_confidence", 0.75))

    @property
    def screenshots_dir(self) -> Path:
        return self.resolve_path(self.raw.get("paths", {}).get("screenshots", "data/screenshots"))

    @property
    def reports_dir(self) -> Path:
        return self.resolve_path(self.raw.get("paths", {}).get("reports", "data/reports"))

    @property
    def replay_dir(self) -> Path:
        return self.resolve_path(self.raw.get("paths", {}).get("replay", "data/replay"))

    @property
    def labels_dir(self) -> Path:
        return self.resolve_path(self.raw.get("paths", {}).get("labels", "data/labels"))

    def resolve_path(self, value: str | Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.project_root / path

    def ensure_dirs(self) -> None:
        for path in (self.screenshots_dir, self.reports_dir, self.replay_dir, self.labels_dir):
            path.mkdir(parents=True, exist_ok=True)

    def digest(self) -> str:
        payload = json.dumps(self.raw, sort_keys=True, ensure_ascii=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]


def load_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config(config_path: str | Path | None = None) -> GuardConfig:
    project_root = PROJECT_ROOT
    config_file = Path(config_path) if config_path else project_root / "config" / "default_config.json"
    raw = load_json_file(config_file, {})
    instances_path = project_root / "config" / "instances.json"
    config = GuardConfig(
        project_root=project_root,
        raw=raw,
        config_path=config_file,
        instances_path=instances_path,
    )
    config.ensure_dirs()
    return config

