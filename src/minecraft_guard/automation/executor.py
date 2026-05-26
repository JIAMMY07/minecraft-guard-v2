from __future__ import annotations


class AutomationDisabledError(RuntimeError):
    pass


def send_input(*_args: object, **_kwargs: object) -> None:
    raise AutomationDisabledError("Active input is not implemented in the first V2 delivery.")


def run_once() -> None:
    raise AutomationDisabledError("Use observe-once first. Active automation is intentionally disabled.")

