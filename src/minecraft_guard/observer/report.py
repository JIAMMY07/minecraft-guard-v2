from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minecraft_guard.redaction import redact_data, redact_text


def write_reports(snapshot: dict[str, Any], reports_dir: Path) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    snapshot_id = snapshot["snapshot_id"]
    json_path = reports_dir / f"observer_snapshot_{snapshot_id}.json"
    md_path = reports_dir / f"observer_snapshot_{snapshot_id}.md"
    snapshot["report_files"] = {"json": str(json_path), "markdown": str(md_path)}
    redacted = redact_data(snapshot)
    json_path.write_text(json.dumps(redacted, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_markdown(redacted), encoding="utf-8")
    return json_path, md_path


def render_markdown(snapshot: dict[str, Any]) -> str:
    summary = snapshot.get("summary", {})
    lines = [
        f"# Minecraft Guard V2 Observer {snapshot.get('snapshot_id')}",
        "",
        f"- Created at: `{snapshot.get('created_at')}`",
        f"- Passive: `{snapshot.get('passive')}`",
        f"- Windows: `{summary.get('total_windows', 0)}`",
        "",
        "## Summary",
        "",
    ]
    for state, count in sorted(summary.get("by_state", {}).items()):
        lines.append(f"- `{state}`: {count}")
    if not summary.get("by_state"):
        lines.append("- No Minecraft windows found.")
    lines.extend(["", "## Windows", ""])
    for window in snapshot.get("windows", []):
        perception = window.get("perception", {})
        decision = window.get("decision", {})
        lines.extend(
            [
                f"### HWND {window.get('hwnd')}",
                "",
                f"- Title: {redact_text(str(window.get('title', '')))}",
                f"- PID: `{window.get('pid')}`",
                f"- State: `{perception.get('visual_state')}`",
                f"- Confidence: `{perception.get('confidence')}`",
                f"- Decision: `{decision.get('action')}` allowed=`{decision.get('allowed')}`",
                f"- Explanation: {perception.get('final_explanation') or perception.get('explanation')}",
                f"- Screenshot: `{window.get('screenshot_path')}`",
                f"- Mapping: `{window.get('instance_mapping', {}).get('status')}` via `{window.get('instance_mapping', {}).get('source')}`",
                "",
            ]
        )
    return "\n".join(lines) + "\n"

