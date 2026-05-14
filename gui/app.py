"""Main entry point for the AquaSoil-AI Tkinter desktop application."""

from __future__ import annotations

import sys
import textwrap
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import tkinter as tk
    from tkinter import messagebox

    import ttkbootstrap as ttk
except ModuleNotFoundError as exc:
    print("ttkbootstrap is required for the desktop GUI.")
    print("Install it with: pip install ttkbootstrap")
    raise SystemExit(1) from exc

from gui.tabs.about_tab import AboutTab
from gui.tabs.chat_tab import ChatTab
from gui.tabs.history_tab import HistoryTab
from gui.tabs.input_tab import InputTab
from gui.tabs.results_tab import ResultsTab
from gui.database import delete_all, init_db, load_all, save_analysis
from gui.theme import (
    COLOR_BACKGROUND,
    COLOR_CARD_BG,
    COLOR_ENTRY_BG,
    COLOR_PRIMARY,
    COLOR_SOIL,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_TAB,
    PADDING_MEDIUM,
    STATUS_COMPLETE,
    STATUS_READY,
    THEME_NAME,
)
from src.classifier import classify
from src.knowledge_base import RULES
from src.output import print_advisory
from src.preprocess import validate_inputs
from src.reasoning_engine import get_recommendations

try:
    from src.output import save_report as backend_save_report
except ImportError:
    backend_save_report = None


class AquaSoilApp(ttk.Window):
    """Main AquaSoil-AI desktop application window."""

    def __init__(self) -> None:
        """Initialize the window, notebook tabs, and shared state."""
        super().__init__(themename=THEME_NAME)
        init_db()
        self.history: list[dict[str, Any]] = load_all()
        self.rule_count = len(RULES)
        self.title("AquaSoil-AI — Soil & Water Advisor")
        self.geometry("960x720")
        self.minsize(800, 600)
        self.configure(bg=COLOR_BACKGROUND)
        self._setup_styles()
        self._set_window_icon()
        self._build_layout()
        self.center_window()

    def _setup_styles(self) -> None:
        """Configure ttkbootstrap styles used by the application."""
        style = self.style
        style.configure("TFrame", background=COLOR_BACKGROUND)
        style.configure("TNotebook", background=COLOR_BACKGROUND, borderwidth=0)
        style.configure("TNotebook.Tab", font=FONT_TAB, padding=(14, 8))
        style.configure("TLabel", background=COLOR_BACKGROUND, foreground=COLOR_TEXT_PRIMARY, font=FONT_BODY)
        style.configure("Card.TFrame", background=COLOR_CARD_BG)
        style.configure("Muted.TLabel", foreground=COLOR_TEXT_MUTED, background=COLOR_BACKGROUND)
        style.configure("Status.TLabel", background=COLOR_PRIMARY, foreground=COLOR_ENTRY_BG, font=FONT_BODY)

    def _build_layout(self) -> None:
        """Build the notebook and status bar."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self, bootstyle="primary")
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.input_tab = InputTab(self.notebook, self)
        self.results_tab = ResultsTab(self.notebook, self)
        self.chat_tab = ChatTab(self.notebook, self)
        self.history_tab = HistoryTab(self.notebook, self)
        self.about_tab = AboutTab(self.notebook)

        self.notebook.add(self.input_tab, text="🌱 Input")
        self.notebook.add(self.results_tab, text="📊 Results")
        self.notebook.add(self.chat_tab, text="AquaBot")
        self.notebook.add(self.history_tab, text="📋 History")
        self.notebook.add(self.about_tab, text="ℹ️ About")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.history_tab.refresh(self.history)

        self.status_var = tk.StringVar(value=STATUS_READY)
        self.status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            style="Status.TLabel",
            anchor="w",
            padding=(PADDING_MEDIUM, 5),
        )
        self.status_bar.grid(row=1, column=0, sticky="ew")

    def _set_window_icon(self) -> None:
        """Create and apply a simple in-memory leaf-like window icon."""
        icon = tk.PhotoImage(width=32, height=32)
        icon.put(COLOR_ENTRY_BG, to=(0, 0, 32, 32))
        for y_coord in range(5, 27):
            for x_coord in range(5, 27):
                leaf_value = ((x_coord - 16) ** 2) / 70 + ((y_coord - 14) ** 2) / 38
                if leaf_value <= 1.0 and x_coord + y_coord < 42:
                    icon.put(COLOR_SOIL, (x_coord, y_coord))
        for offset in range(9):
            icon.put(COLOR_PRIMARY, (15 + offset, 21 - offset))
        self.iconphoto(True, icon)
        self._window_icon = icon

    def center_window(self) -> None:
        """Center the main window on the current screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x_coord = (self.winfo_screenwidth() - width) // 2
        y_coord = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x_coord}+{y_coord}")

    def center_child_window(self, child: tk.Toplevel, width: int, height: int) -> None:
        """Center a child window over the main app window."""
        self.update_idletasks()
        x_coord = self.winfo_x() + (self.winfo_width() - width) // 2
        y_coord = self.winfo_y() + (self.winfo_height() - height) // 2
        child.geometry(f"{width}x{height}+{x_coord}+{y_coord}")

    def set_status(self, text: str) -> None:
        """Set the bottom status bar text."""
        self.status_var.set(text)

    def set_status_ready(self) -> None:
        """Set the status bar to the idle message."""
        self.status_var.set(STATUS_READY)

    def set_status_complete(self) -> None:
        """Set the status bar to the completed analysis message."""
        self.status_var.set(STATUS_COMPLETE)

    def process_sample(self, sample_label: str, input_values: dict[str, float]) -> dict[str, Any]:
        """Run one sample through validation, classification, and reasoning."""
        validate_inputs(input_values)
        classification_result = classify(input_values)
        facts = input_values.copy()
        facts.update(
            {
                "soil_class": classification_result["soil_class"],
                "water_class": classification_result["water_class"],
            }
        )
        recommendations = get_recommendations(facts)

        return {
            "sample": sample_label,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input_values": input_values.copy(),
            "soil_class": classification_result["soil_class"],
            "soil_confidence": classification_result["soil_confidence"],
            "water_class": classification_result["water_class"],
            "water_confidence": classification_result["water_confidence"],
            "recommendations": recommendations,
        }

    def add_history_result(self, result: dict[str, Any]) -> None:
        """Persist one analysis result and refresh the history table."""
        save_analysis(result)
        self.reload_history()

    def reload_history(self) -> None:
        """Load persisted analyses and refresh the history table."""
        self.history = load_all()
        self.history_tab.refresh(self.history)

    def clear_history(self) -> None:
        """Clear all persisted history rows."""
        delete_all()
        self.history = []
        self.history_tab.refresh(self.history)
        self.set_status_ready()

    def show_results(self, result: dict[str, Any]) -> None:
        """Populate and select the Results tab."""
        self.results_tab.show_result(result)
        self.chat_tab.refresh_context()
        self.notebook.select(self.results_tab)

    def get_latest_result(self) -> Optional[dict[str, Any]]:
        """Return the visible result or the newest saved history row."""
        if self.results_tab.current_result is not None:
            return self.results_tab.current_result
        if self.history:
            return self.history[0]
        return None

    def show_history(self) -> None:
        """Refresh and select the History tab."""
        self.reload_history()
        self.notebook.select(self.history_tab)

    def load_history_result(self, index: int) -> None:
        """Load a selected history result into the Results tab."""
        if 0 <= index < len(self.history):
            self.show_results(self.history[index])

    def _on_tab_changed(self, _event: tk.Event) -> None:
        """Reload persistent history whenever the History tab is opened."""
        selected_widget = self.notebook.nametowidget(self.notebook.select())
        if selected_widget is self.history_tab:
            self.reload_history()

    def safe_report_filename(self, sample_label: str) -> str:
        """Return a safe default report filename for a sample."""
        safe_label = "".join(character if character.isalnum() else "_" for character in sample_label).strip("_")
        if not safe_label:
            safe_label = "Unknown_Field"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"report_{safe_label}_{timestamp}.txt"

    def write_report_file(self, path: Path, result: dict[str, Any]) -> None:
        """Write a formatted advisory report to the selected path."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.format_report_text(result), encoding="utf-8")

    def save_automatic_report(self, result: dict[str, Any]) -> None:
        """Save an automatic report through the available backend output module."""
        if backend_save_report is not None:
            backend_save_report(result["sample"], result, result["recommendations"])
            return
        print_advisory(result["sample"], result, result["recommendations"])

    def format_report_text(self, result: dict[str, Any]) -> str:
        """Format one analysis result as a readable advisory report."""
        lines = [
            "=== AquaSoil-AI Advisory Report ===",
            f"Timestamp   : {result.get('timestamp', '')}",
            f"Sample      : {result.get('sample', 'Unknown Field')}",
            f"Soil Quality: {str(result.get('soil_class', '')).upper():<8} "
            f"(Confidence: {float(result.get('soil_confidence', 0)):.0f}%)",
            f"Water Quality: {str(result.get('water_class', '')).upper():<6} "
            f"(Confidence: {float(result.get('water_confidence', 0)):.0f}%)",
            "",
            "--- Input Parameters ---",
        ]

        for parameter, value in result.get("input_values", {}).items():
            lines.append(f"{parameter}: {value:g}")

        lines.append("")
        lines.append("--- Recommendations ---")
        for recommendation in result.get("recommendations", []):
            lines.append(self._wrap_recommendation(recommendation))

        return "\n".join(lines)

    def _wrap_recommendation(self, recommendation: str) -> str:
        """Wrap one recommendation while preserving its severity tag."""
        tag_end = recommendation.find("]") + 1
        if tag_end > 0:
            prefix = recommendation[:tag_end] + "  "
            body = recommendation[tag_end:].strip()
            wrapper = textwrap.TextWrapper(initial_indent=prefix, subsequent_indent=" " * len(prefix), width=78)
            return wrapper.fill(body)
        return textwrap.fill(recommendation, width=78)

    def show_model_error(self, _exc: FileNotFoundError) -> None:
        """Show a model-missing error dialog with training instructions."""
        dialog = tk.Toplevel(self)
        dialog.title("Model files not found")
        dialog.transient(self)
        dialog.resizable(False, False)

        container = ttk.Frame(dialog, padding=PADDING_MEDIUM)
        container.pack(fill="both", expand=True)
        ttk.Label(
            container,
            text="Model files not found. Please run train_model.py first to generate the model.",
            font=FONT_BODY,
            wraplength=420,
        ).pack(anchor="w", pady=(0, PADDING_MEDIUM))

        buttons = ttk.Frame(container)
        buttons.pack(fill="x")
        ttk.Button(
            buttons,
            text="Open Terminal Instructions",
            bootstyle="primary",
            command=self.show_terminal_instructions,
        ).pack(side="left")
        ttk.Button(buttons, text="Close", bootstyle="secondary-outline", command=dialog.destroy).pack(side="right")
        self.center_child_window(dialog, width=500, height=155)

    def show_terminal_instructions(self) -> None:
        """Show the command needed to regenerate model files."""
        instructions = (
            "Open a terminal in the AquaSoil-AI project folder and run:\n\n"
            "python src/train_model.py\n\n"
            "After training completes, launch the GUI again with:\n\n"
            "python gui/app.py"
        )
        messagebox.showinfo("Terminal Instructions", instructions, parent=self)

    def show_backend_error(self, exc: Exception, details: Optional[str] = None) -> None:
        """Log an unexpected backend error and show a friendly dialog."""
        error_details = details or "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        self.log_exception(error_details)
        messagebox.showerror(
            "AquaSoil-AI error",
            "Something went wrong while processing the sample. The details were saved to logs/error_log.txt.",
            parent=self,
        )

    def log_exception(self, details: str) -> None:
        """Append an exception traceback to the GUI error log."""
        logs_dir = PROJECT_ROOT / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / "error_log.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with log_path.open("a", encoding="utf-8") as file:
            file.write(f"\n[{timestamp}] AquaSoil-AI GUI error\n")
            file.write(details)
            if not details.endswith("\n"):
                file.write("\n")


def main() -> None:
    """Launch the AquaSoil-AI desktop application."""
    try:
        app = AquaSoilApp()
    except tk.TclError as exc:
        print("AquaSoil-AI could not open the desktop window.")
        print("")
        print("This usually means Python's Tk/Tcl desktop GUI files are missing or broken.")
        print("Check Tkinter with this command:")
        print("")
        print("    python -m tkinter")
        print("")
        print("If that does not open a small test window, repair or reinstall Python")
        print("and make sure the 'tcl/tk and IDLE' option is installed.")
        print("")
        print(f"Tk error: {exc}")
        raise SystemExit(1) from exc
    app.mainloop()


if __name__ == "__main__":
    main()
