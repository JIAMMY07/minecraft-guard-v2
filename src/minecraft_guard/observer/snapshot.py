from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Callable

from minecraft_guard.config import GuardConfig, load_config
from minecraft_guard.instances.log_mapper import map_window_to_log
from minecraft_guard.instances.log_parser import parse_latest_log_hint
from minecraft_guard.intelligence.confidence import ConfidenceEngine
from minecraft_guard.intelligence.explanations import ExplanationEngine
from minecraft_guard.intelligence.perception import build_perception
from minecraft_guard.intelligence.planner import Planner
from minecraft_guard.intelligence.world_model import WorldModel
from minecraft_guard.logging_utils import new_session_id, utc_now_iso, write_jsonl_event
from minecraft_guard.observer.report import write_reports
from minecraft_guard.vision.capture import capture_window_passive
from minecraft_guard.vision.detector import detect_visual_state
from minecraft_guard.windows.discovery import WindowInfo, discover_minecraft_windows


WindowDiscovery = Callable[[], list[WindowInfo]]


def observe_once(config: GuardConfig | None = None, discover: WindowDiscovery | None = None) -> dict[str, Any]:
    config = config or load_config()
    config.ensure_dirs()
    session_id = new_session_id("observer")
    snapshot_id = session_id.replace("observer_", "")
    event_log = config.reports_dir / f"runtime_{session_id}.jsonl"
    windows = (discover or discover_minecraft_windows)()
    world = WorldModel()
    planner = Planner(passive_only=True)
    confidence_engine = ConfidenceEngine()
    explanation_engine = ExplanationEngine()
    observations: list[dict[str, Any]] = []

    for window in windows:
        screenshot_path = config.screenshots_dir / f"observer_{snapshot_id}_{window.hwnd}.png"
        captured_path, capture_reasons = capture_window_passive(window, screenshot_path)
        mapping = map_window_to_log(window, config)
        log_hint = parse_latest_log_hint(mapping.latest_log)
        detection = detect_visual_state(captured_path)
        if capture_reasons:
            detection = detection_with_capture_reasons(detection, capture_reasons)
        perception = build_perception(
            window.window_id,
            str(captured_path) if captured_path else None,
            detection,
            log_hint,
            min_confidence=config.min_confidence,
        )
        perception = confidence_engine.refine(perception)
        world.update_observation(window.window_id, perception.visual_state, str(captured_path) if captured_path else None, perception.log_hint)
        decision = planner.decide(perception, world)
        final_explanation = explanation_engine.explain(perception, decision)
        perception_data = perception.as_dict()
        perception_data["final_explanation"] = final_explanation
        observation = {
            **window.as_dict(),
            "screenshot_path": str(captured_path) if captured_path else None,
            "capture_reasons": capture_reasons,
            "diagnostic_state": perception.visual_state,
            "instance_mapping": mapping.as_dict(),
            "log_hint": log_hint.as_dict(),
            "perception": perception_data,
            "decision": decision.as_dict(),
        }
        observations.append(observation)
        write_jsonl_event(event_log, session_id, "window_observed", observation)

    by_state = Counter(item["diagnostic_state"] for item in observations)
    snapshot = {
        "snapshot_id": snapshot_id,
        "created_at": utc_now_iso(),
        "session_id": session_id,
        "passive": True,
        "summary": {
            "total_windows": len(observations),
            "by_state": dict(sorted(by_state.items())),
            "uncertain_windows": by_state.get("uncertain", 0),
        },
        "windows": observations,
        "world_model": world.as_dict(),
        "config_digest": config.digest(),
        "runtime_events": str(event_log),
        "report_files": {},
    }
    json_path, md_path = write_reports(snapshot, config.reports_dir)
    snapshot["report_files"] = {"json": str(json_path), "markdown": str(md_path)}
    write_jsonl_event(event_log, session_id, "observer_snapshot_written", {"report_files": snapshot["report_files"]})
    return snapshot


def detection_with_capture_reasons(detection: Any, capture_reasons: list[str]) -> Any:
    if not capture_reasons:
        return detection
    from minecraft_guard.vision.detector import VisualDetection
    from minecraft_guard.vision.states import VisualState

    return VisualDetection(
        state=VisualState.UNCERTAIN.value,
        confidence=min(getattr(detection, "confidence", 0.0), 0.2),
        ui_objects=[],
        risk_flags=sorted(set(list(getattr(detection, "risk_flags", [])) + ["capture_not_reliable"])),
        uncertainty_reasons=sorted(set(list(getattr(detection, "uncertainty_reasons", [])) + capture_reasons)),
        evidence=getattr(detection, "evidence", {}),
    )


def format_summary(snapshot: dict[str, Any]) -> str:
    summary = snapshot.get("summary", {})
    total = summary.get("total_windows", 0)
    lines = [f"Vedo {total} Minecraft"]
    for state, count in sorted(summary.get("by_state", {}).items()):
        label = "incerto" if state == "uncertain" else state
        lines.append(f"{count} {label}")
    if total == 0:
        lines.append("Nessuna finestra Minecraft candidata trovata.")
    return "\n".join(lines)
