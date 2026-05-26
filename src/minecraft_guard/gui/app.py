from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, X, Button, Frame, Label, Text, Tk

from minecraft_guard.config import load_config
from minecraft_guard.observer.snapshot import format_summary, observe_once
from minecraft_guard.replay.player import replay_report


class GuardApp:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("Minecraft Guard V2")
        self.config = load_config()
        self.last_report: str | None = None
        self.status = Label(self.root, text="Stato guard: osservatore pronto", anchor="w")
        self.status.pack(fill=X, padx=12, pady=(12, 4))
        button_bar = Frame(self.root)
        button_bar.pack(fill=X, padx=12, pady=4)
        Button(button_bar, text="Osserva Minecraft", command=self.observe).pack(side=LEFT, padx=(0, 6))
        Button(button_bar, text="Apri ultimo report osservatore", command=self.open_last_report).pack(side=LEFT, padx=6)
        Button(button_bar, text="Replay ultimo report", command=self.replay_last_report).pack(side=LEFT, padx=6)
        Button(button_bar, text="Audit dataset", command=self.audit_dataset).pack(side=LEFT, padx=6)
        Button(button_bar, text="Avvia guard", command=lambda: self.write("Automazione attiva disabilitata nella prima V2.")).pack(side=LEFT, padx=6)
        Button(button_bar, text="Ferma guard", command=lambda: self.write("Guard fermo.")).pack(side=LEFT, padx=6)
        self.output = Text(self.root, height=24, width=110)
        self.output.pack(fill=BOTH, expand=True, padx=12, pady=(4, 12))
        self.write("Sezioni: Stato guard, Osservatore, Percezione IA, Automazione, Dataset, Report, Impostazioni.")

    def write(self, text: str) -> None:
        self.output.insert(END, text + "\n")
        self.output.see(END)

    def observe(self) -> None:
        self.status.config(text="Stato guard: osservazione in corso")
        threading.Thread(target=self._observe_worker, daemon=True).start()

    def _observe_worker(self) -> None:
        try:
            snapshot = observe_once(self.config)
            self.last_report = snapshot["report_files"]["json"]
            self.root.after(0, lambda: self.write(format_summary(snapshot)))
            self.root.after(0, lambda: self.write(f"Ultimo report: {self.last_report}"))
        except Exception as exc:
            self.root.after(0, lambda: self.write(f"Errore osservatore: {type(exc).__name__}: {exc}"))
        finally:
            self.root.after(0, lambda: self.status.config(text="Stato guard: osservatore pronto"))

    def open_last_report(self) -> None:
        if not self.last_report:
            self.write("Nessun report ancora disponibile.")
            return
        path = Path(self.last_report).with_suffix(".md")
        if not path.exists():
            path = Path(self.last_report)
        if sys.platform.startswith("win"):
            subprocess.Popen(["cmd", "/c", "start", "", str(path)])
        else:
            self.write(str(path))

    def replay_last_report(self) -> None:
        if not self.last_report:
            self.write("Nessun report ancora disponibile.")
            return
        result = replay_report(self.last_report)
        self.write(f"Replay: {result['matches']}/{result['total']} stati invariati.")

    def audit_dataset(self) -> None:
        from minecraft_guard.cli import audit_dataset

        report = audit_dataset(self.config.labels_dir)
        self.write(f"Dataset: {report['total_screenshots']} screenshot, mancanti: {', '.join(report['missing_states'])}")

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    GuardApp().run()


if __name__ == "__main__":
    main()
