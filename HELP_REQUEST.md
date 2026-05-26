# Help Wanted: Minecraft Guard V2

I am looking for help improving Minecraft Guard V2, a Windows/Python project that passively observes multiple Minecraft windows and classifies their visual state before allowing any automation.

The safety rule is strict: perception first, automation later. If a window is minimized, covered, unreadable, or visually uncertain, the program must not send input.

## Current state

- Python 3.11+ project with package layout under `src/minecraft_guard`.
- Passive observer CLI: `python -m minecraft_guard.cli observe-once`.
- Optional explicit pre-step to restore minimized Minecraft windows: `--restore-minimized`.
- Tkinter GUI for basic observer workflows.
- Window discovery and process/instance/log mapping for Java-based launchers.
- Conservative visual detector for states like `login_prompt`, `survival_game`, `loading`, and `uncertain`.
- `PerceptionResult`, `Planner`, `ConfidenceEngine`, `ExplanationEngine`, `Verifier`.
- Offline replay of observer reports.
- Dataset label/audit commands.
- Pytest suite currently passing.

## Areas where help is useful

- More robust computer vision for Minecraft UI states across resolutions, texture packs, shaders, and launchers.
- Safer handling of minimized, off-screen, covered, and multi-monitor windows.
- Better redaction of command lines, logs, UUIDs, access tokens, usernames, and server-specific data.
- A real dataset workflow with separate calibration and validation sets.
- OCR integration that improves confidence without turning log hints into unsafe actions.
- Code review of the state machine before any active automation is enabled.
- Windows capture reliability without changing focus in observer mode.

## Non-goals

- No anti-cheat bypass.
- No ban evasion.
- No hidden automation.
- No hardcoded passwords or tokens.
- No active input unless visual state, process, geometry, and verification are all safe.

## How to run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest
python -m minecraft_guard.cli observe-once
```

## Review focus

Please prioritize bugs and safety risks over feature ideas:

- False positives that could allow input in the wrong state.
- Reports or logs leaking secrets.
- Window discovery matching helper windows instead of real game windows.
- Replay/dataset gaps that make detector quality look better than it is.
- Places where the planner trusts history or logs more than current visual evidence.

