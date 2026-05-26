from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from minecraft_guard.redaction import redact_data


@dataclass(frozen=True)
class ProcessInfo:
    pid: int | None
    exe: str | None = None
    name: str | None = None
    cwd: str | None = None
    cmdline: list[str] | None = None
    status: str | None = None
    error: str | None = None

    @property
    def command_line_text(self) -> str:
        return " ".join(self.cmdline or [])

    def as_dict(self) -> dict[str, Any]:
        return redact_data(asdict(self))


def get_pid_for_hwnd(hwnd: int) -> int | None:
    try:
        import win32process  # type: ignore

        _thread_id, pid = win32process.GetWindowThreadProcessId(hwnd)
        return int(pid)
    except Exception:
        return None


def get_process_info(pid: int | None) -> ProcessInfo:
    if not pid:
        return ProcessInfo(pid=None, error="pid_missing")
    try:
        import psutil  # type: ignore

        proc = psutil.Process(pid)
        return ProcessInfo(
            pid=pid,
            exe=proc.exe(),
            name=proc.name(),
            cwd=safe_cwd(proc),
            cmdline=proc.cmdline(),
            status=proc.status(),
        )
    except Exception as exc:
        return ProcessInfo(pid=pid, error=f"process_info_unavailable:{type(exc).__name__}")


def safe_cwd(proc: Any) -> str | None:
    try:
        cwd = proc.cwd()
    except Exception:
        return None
    if cwd and Path(cwd).exists():
        return cwd
    return cwd or None

