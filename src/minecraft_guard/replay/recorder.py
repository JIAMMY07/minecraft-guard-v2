from __future__ import annotations

from pathlib import Path
from shutil import copy2


def copy_replay_artifact(source: str | Path, replay_dir: str | Path) -> Path:
    source_path = Path(source)
    target_dir = Path(replay_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source_path.name
    copy2(source_path, target)
    return target

