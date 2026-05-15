"""No-console launcher for the AquaSoil-AI desktop GUI."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_PATH = LOG_DIR / "launcher_error.log"


def _show_error(message: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("AquaSoil-AI Launcher", message)
        root.destroy()
    except Exception:
        return


def main() -> None:
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from gui.app import main as run_app

        run_app()
    except SystemExit as exc:
        if exc.code in (0, None):
            return
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        LOG_PATH.write_text(f"AquaSoil-AI exited during startup with code {exc.code}.\n", encoding="utf-8")
        _show_error(
            "AquaSoil-AI could not start.\n\n"
            "Check logs\\launcher_error.log for details, or install dependencies with:\n"
            "pip install -r requirements.txt"
        )
    except Exception:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        details = traceback.format_exc()
        LOG_PATH.write_text(details, encoding="utf-8")
        _show_error(
            "AquaSoil-AI could not start.\n\n"
            "Check logs\\launcher_error.log for details, or install dependencies with:\n"
            "pip install -r requirements.txt"
        )


if __name__ == "__main__":
    main()
