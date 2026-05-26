from __future__ import annotations

from minecraft_guard.config import GuardConfig
from minecraft_guard.instances.resolver import InstanceMapping, resolve_instance
from minecraft_guard.windows.discovery import WindowInfo


def map_window_to_log(window: WindowInfo, config: GuardConfig) -> InstanceMapping:
    return resolve_instance(window, config)

