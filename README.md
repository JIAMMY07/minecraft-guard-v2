# Minecraft Guard V2

Minecraft Guard V2 e una riscrittura pulita, vision-first e prudente. La prima consegna abilita solo osservazione, diagnosi, report, replay e dataset. L'automazione attiva resta separata e intenzionalmente disabilitata.

## Cosa fa ora

- Enumera passivamente le finestre Minecraft candidate su Windows.
- Cattura screenshot della geometria finestra senza focus, click o cambio desktop.
- Prova a mappare finestra -> processo Java -> instance dir -> `logs/latest.log`.
- Classifica lo stato visivo in modo conservativo.
- Produce `PerceptionResult`, `Decision` e spiegazioni leggibili.
- Scrive report JSON/Markdown e runtime JSONL in `data/reports`.
- Supporta replay offline dei report.
- Supporta audit e labeling base del dataset.
- Offre una GUI Tkinter minima con pulsante "Osserva Minecraft".

## Installazione

Da PowerShell:

```powershell
cd "C:\Users\notar\Documents\Codex\2026-05-11\files-mentioned-by-the-user-whatsapp\minecraft_guard_v2"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Observer CLI

```powershell
python -m minecraft_guard.cli observe-once
```

Output atteso:

```text
Vedo 4 Minecraft
1 lobby
1 survival_game
1 login_prompt
1 incerto
```

Gli artefatti vengono creati qui:

- Screenshot: `data/screenshots/observer_<timestamp>_<hwnd>.png`
- Report JSON: `data/reports/observer_snapshot_<timestamp>.json`
- Report Markdown: `data/reports/observer_snapshot_<timestamp>.md`
- Eventi runtime: `data/reports/runtime_<session>.jsonl`

## GUI

```powershell
python -m minecraft_guard.cli gui
```

La GUI mostra stato guard, conteggi osservatore, percezione IA, decisione consigliata, report, replay e audit dataset. Il thread UI non viene bloccato durante l'osservazione.

## Replay offline

```powershell
python -m minecraft_guard.cli replay "data\reports\observer_snapshot_<timestamp>.json"
```

Il replay rilegge gli screenshot del report e riesegue il detector, confrontando stato vecchio e nuovo.

## Dataset

```powershell
python -m minecraft_guard.cli dataset label "data\screenshots\sample.png" lobby
python -m minecraft_guard.cli dataset audit
```

Stati iniziali da coprire: `pause_menu`, `survival_game`, `login_prompt`, `lobby`, `non_minecraft_desktop`, `loading`, `chat_open`.

Target iniziale: almeno 10 screenshot etichettati per stato, con dataset di taratura separato dal dataset di validazione quando si iniziera a misurare affidabilita reale.

## Config manuale istanze

Copia `config/instances.example.json` in `config/instances.json` e compila:

```json
[
  {
    "name": "nome istanza",
    "window_title_contains": "Minecraft",
    "process_path_contains": "javaw.exe",
    "instance_dir": "C:/path/to/instance",
    "latest_log": "C:/path/to/instance/logs/latest.log"
  }
]
```

Il mapping manuale ha priorita sul rilevamento automatico. Se il log manca, il report indica `log_missing` senza fallire.

## Test

```powershell
python -m pytest
```

I test coprono osservatore passivo, mapping log, redaction, detector prudente, planner, verifier, replay, report e simulazione sintetica da 1000 scenari con zero input insicuri.

## Prima di abilitare automazione attiva

- Raccogliere dataset reale con piu client: CurseForge, Prism Launcher, MultiMC, vanilla e altri launcher Java.
- Validare risoluzioni, scaling Windows, finestre coperte/minimizzate/fuori schermo e negative samples.
- Misurare falsi positivi, falsi negativi e casi `uncertain`.
- Separare dataset di taratura e validazione.
- Aggiungere OCR reale solo se migliora la prudenza.
- Abilitare `run-once`/`watch` solo dopo verifica see -> think -> act -> verify e state machine rigida.
