from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from shutil import copy2
from typing import Any

from minecraft_guard.automation.executor import AutomationDisabledError, run_once
from minecraft_guard.config import load_config
from minecraft_guard.observer.snapshot import format_summary, observe_once
from minecraft_guard.replay.player import replay_report
from minecraft_guard.vision.detector import detect_visual_state
from minecraft_guard.vision.states import DIAGNOSTIC_STATES


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "observe-once":
        if args.restore_minimized:
            from minecraft_guard.windows.restore import restore_minimized_minecraft_windows

            results = restore_minimized_minecraft_windows()
            restored = [item for item in results if item.restored]
            print(f"Finestre Minecraft ripristinate: {len(restored)}")
            time.sleep(args.restore_wait)
        snapshot = observe_once(load_config(args.config))
        print(format_summary(snapshot))
        print(f"JSON: {snapshot['report_files']['json']}")
        print(f"Markdown: {snapshot['report_files']['markdown']}")
        return 0
    if args.command == "replay":
        result = replay_report(args.report)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["matches"] == result["total"] else 1
    if args.command == "dataset":
        return handle_dataset(args)
    if args.command in {"run-once", "watch"}:
        try:
            run_once()
        except AutomationDisabledError as exc:
            print(str(exc))
            return 2
    if args.command == "gui":
        from minecraft_guard.gui.app import main as gui_main

        gui_main()
        return 0
    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="minecraft_guard", description="Minecraft Guard V2")
    parser.add_argument("--config", help="Path to default_config.json", default=None)
    sub = parser.add_subparsers(dest="command")
    observe = sub.add_parser("observe-once", help="Passive one-shot observation.")
    observe.add_argument("--restore-minimized", action="store_true", help="Restore minimized Minecraft windows before observing.")
    observe.add_argument("--restore-wait", type=float, default=1.0, help="Seconds to wait after restoring windows.")
    replay = sub.add_parser("replay", help="Replay an observer JSON report offline.")
    replay.add_argument("report")
    dataset = sub.add_parser("dataset", help="Dataset utilities.")
    dataset_sub = dataset.add_subparsers(dest="dataset_command", required=True)
    dataset_sub.add_parser("audit", help="Audit labels and detector regression.")
    label = dataset_sub.add_parser("label", help="Label a screenshot.")
    label.add_argument("screenshot")
    label.add_argument("state", choices=DIAGNOSTIC_STATES + ["non_minecraft_desktop"])
    sub.add_parser("run-once", help="Active automation placeholder; disabled in first delivery.")
    sub.add_parser("watch", help="Active watch placeholder; disabled in first delivery.")
    sub.add_parser("gui", help="Open the Tkinter GUI.")
    return parser


def handle_dataset(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if args.dataset_command == "label":
        screenshot = Path(args.screenshot)
        if not screenshot.exists():
            print(f"Screenshot not found: {screenshot}")
            return 1
        state = args.state
        state_dir = config.labels_dir / state
        state_dir.mkdir(parents=True, exist_ok=True)
        target = state_dir / screenshot.name
        copy2(screenshot, target)
        metadata = {"source": str(screenshot), "state": state, "labeled_copy": str(target)}
        (target.with_suffix(target.suffix + ".json")).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"Labeled {target} as {state}")
        return 0
    if args.dataset_command == "audit":
        report = audit_dataset(config.labels_dir)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    return 1


def audit_dataset(labels_dir: Path) -> dict[str, Any]:
    expected = ["pause_menu", "survival_game", "login_prompt", "lobby", "non_minecraft_desktop", "loading", "chat_open"]
    counts: Counter[str] = Counter()
    regressions: list[dict[str, Any]] = []
    for state_dir in labels_dir.iterdir() if labels_dir.exists() else []:
        if not state_dir.is_dir():
            continue
        state = state_dir.name
        screenshots = [p for p in state_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
        counts[state] += len(screenshots)
        for screenshot in screenshots:
            detected = detect_visual_state(screenshot)
            expected_state = "uncertain" if state == "non_minecraft_desktop" else state
            if detected.state != expected_state:
                regressions.append(
                    {
                        "screenshot": str(screenshot),
                        "expected": expected_state,
                        "actual": detected.state,
                        "confidence": detected.confidence,
                    }
                )
    return {
        "total_screenshots": sum(counts.values()),
        "coverage_by_state": dict(sorted(counts.items())),
        "missing_states": [state for state in expected if counts[state] == 0],
        "states_below_initial_target_10": [state for state in expected if counts[state] < 10],
        "regressions": regressions,
        "false_positive_count": sum(1 for item in regressions if item["expected"] == "uncertain"),
        "false_negative_count": sum(1 for item in regressions if item["actual"] == "uncertain" and item["expected"] != "uncertain"),
    }


if __name__ == "__main__":
    raise SystemExit(main())
