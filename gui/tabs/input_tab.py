"""Input tab for collecting soil and water sample measurements."""

from __future__ import annotations

import math
import threading
import traceback
from functools import partial
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk

from gui.theme import (
    COLOR_DIVIDER,
    COLOR_SOIL,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WATER,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HINT,
    FONT_SECTION,
    FONT_SUBTITLE,
    FONT_TITLE,
    PADDING_LARGE,
    PADDING_MEDIUM,
    PADDING_SMALL,
    PARAMETER_LABELS,
    PARAMETER_ORDER,
    STATUS_ANALYZING,
)
from src.preprocess import PARAMETER_RANGES, validate_inputs


class InputTab(ttk.Frame):
    """Collect and validate sample measurements before analysis."""

    def __init__(self, master: tk.Misc, app_controller: Any) -> None:
        """Initialize the input tab."""
        super().__init__(master, padding=PADDING_MEDIUM)
        self.app = app_controller
        self.entries: dict[str, ttk.Entry] = {}
        self.value_vars: dict[str, tk.StringVar] = {}
        self.hint_labels: dict[str, ttk.Label] = {}
        self.sample_placeholder = "e.g. Field A – Barangay Pisan"
        self.sample_placeholder_active = True
        self._syncing_moisture = False
        self.batch_dialog: Optional[tk.Toplevel] = None
        self.batch_progress: Optional[ttk.Progressbar] = None
        self.batch_label: Optional[ttk.Label] = None
        self._build_layout()

    def _build_layout(self) -> None:
        """Build the header, form columns, and action buttons."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self._build_header()
        self._build_sample_field()
        self._build_parameter_columns()
        self._build_button_row()

    def _build_header(self) -> None:
        """Build the application title area."""
        header = ttk.Frame(self, padding=(0, 0, 0, PADDING_MEDIUM))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text="🌿", font=("Arial", 34)).grid(row=0, column=0, rowspan=2, padx=(0, PADDING_MEDIUM))
        ttk.Label(header, text="AquaSoil-AI", font=FONT_TITLE, foreground=COLOR_TEXT_PRIMARY).grid(
            row=0, column=1, sticky="w"
        )
        ttk.Label(
            header,
            text="Soil & Water Quality Advisor — Kabacan, North Cotabato",
            font=FONT_SUBTITLE,
            foreground=COLOR_TEXT_MUTED,
        ).grid(row=1, column=1, sticky="w")

        divider = tk.Frame(self, height=2, bg=COLOR_DIVIDER)
        divider.grid(row=1, column=0, sticky="ew", pady=(0, PADDING_MEDIUM))

    def _build_sample_field(self) -> None:
        """Build the optional sample label field."""
        sample_frame = ttk.Frame(self)
        sample_frame.grid(row=2, column=0, sticky="ew", pady=(0, PADDING_MEDIUM))
        sample_frame.columnconfigure(0, weight=1)

        ttk.Label(
            sample_frame,
            text="Sample / Field Name (optional)",
            font=FONT_BODY_BOLD,
            foreground=COLOR_TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        self.sample_var = tk.StringVar(value=self.sample_placeholder)
        self.sample_entry = ttk.Entry(sample_frame, textvariable=self.sample_var, bootstyle="secondary")
        self.sample_entry.grid(row=1, column=0, sticky="ew", pady=(PADDING_SMALL, 0))
        self.sample_entry.configure(foreground=COLOR_TEXT_MUTED)
        self.sample_entry.bind("<FocusIn>", self._clear_sample_placeholder)
        self.sample_entry.bind("<FocusOut>", self._restore_sample_placeholder)

    def _build_parameter_columns(self) -> None:
        """Build soil and water parameter form panels."""
        columns = ttk.Frame(self)
        columns.grid(row=3, column=0, sticky="nsew")
        columns.columnconfigure(0, weight=1, uniform="forms")
        columns.columnconfigure(1, weight=1, uniform="forms")
        columns.rowconfigure(0, weight=1)

        soil_panel = ttk.Labelframe(columns, text=" 🟤 SOIL PARAMETERS ", bootstyle="success", padding=PADDING_MEDIUM)
        soil_panel.grid(row=0, column=0, sticky="nsew", padx=(0, PADDING_MEDIUM // 2))
        water_panel = ttk.Labelframe(columns, text=" 💧 WATER PARAMETERS ", bootstyle="info", padding=PADDING_MEDIUM)
        water_panel.grid(row=0, column=1, sticky="nsew", padx=(PADDING_MEDIUM // 2, 0))

        soil_params = PARAMETER_ORDER[:6]
        water_params = PARAMETER_ORDER[6:]
        for index, parameter in enumerate(soil_params):
            self._create_parameter_field(soil_panel, parameter, index, accent=COLOR_SOIL)
        for index, parameter in enumerate(water_params):
            self._create_parameter_field(water_panel, parameter, index, accent=COLOR_WATER)

    def _create_parameter_field(self, parent: ttk.Frame, parameter: str, row: int, accent: str) -> None:
        """Create one labeled parameter control with validation hint."""
        parent.columnconfigure(1, weight=1)
        minimum, maximum = PARAMETER_RANGES[parameter]
        label_text = PARAMETER_LABELS[parameter]

        label = ttk.Label(parent, text=label_text, font=FONT_BODY, foreground=COLOR_TEXT_PRIMARY)
        label.grid(row=row * 2, column=0, sticky="w", padx=(0, PADDING_MEDIUM), pady=(PADDING_SMALL, 0))

        control_frame = ttk.Frame(parent)
        control_frame.grid(row=row * 2, column=1, sticky="ew", pady=(PADDING_SMALL, 0))
        control_frame.columnconfigure(0, weight=1)

        value_var = tk.StringVar()
        self.value_vars[parameter] = value_var

        if parameter == "Soil Moisture":
            self._create_moisture_controls(control_frame, parameter, value_var)
        else:
            entry = ttk.Entry(control_frame, textvariable=value_var, bootstyle="secondary", width=12)
            entry.grid(row=0, column=0, sticky="ew")
            entry.bind("<FocusOut>", partial(self._on_parameter_focus_out, parameter))
            self.entries[parameter] = entry

        hint = ttk.Label(
            parent,
            text=f"Valid range: {minimum:g} – {maximum:g}",
            font=FONT_HINT,
            foreground=COLOR_TEXT_MUTED,
        )
        hint.grid(row=row * 2 + 1, column=1, sticky="w", pady=(0, PADDING_SMALL))
        self.hint_labels[parameter] = hint

        accent_marker = tk.Frame(parent, width=3, height=1, bg=accent)
        accent_marker.grid(row=row * 2, column=2, rowspan=2, sticky="ns", padx=(PADDING_SMALL, 0))

    def _create_moisture_controls(self, parent: ttk.Frame, parameter: str, value_var: tk.StringVar) -> None:
        """Create the paired moisture slider and numeric entry."""
        parent.columnconfigure(0, weight=1)
        self.moisture_slider_var = tk.DoubleVar(value=0.0)
        self.moisture_slider = ttk.Scale(
            parent,
            from_=0,
            to=100,
            variable=self.moisture_slider_var,
            command=self._on_moisture_slider,
            bootstyle="success",
        )
        self.moisture_slider.grid(row=0, column=0, sticky="ew", padx=(0, PADDING_SMALL))

        entry = ttk.Entry(parent, textvariable=value_var, bootstyle="secondary", width=8)
        entry.grid(row=0, column=1, sticky="e")
        entry.bind("<KeyRelease>", partial(self._on_moisture_entry_keyrelease, parameter))
        entry.bind("<FocusOut>", partial(self._on_parameter_focus_out, parameter))
        self.entries[parameter] = entry

    def _build_button_row(self) -> None:
        """Build the Analyze, Load CSV, Clear, and loading controls."""
        button_row = ttk.Frame(self)
        button_row.grid(row=4, column=0, sticky="ew", pady=(PADDING_LARGE, 0))
        button_row.columnconfigure(4, weight=1)

        self.analyze_button = ttk.Button(
            button_row,
            text="🔍 Analyze Sample",
            bootstyle="success",
            command=self._handle_analyze_click,
            padding=(PADDING_MEDIUM, PADDING_SMALL),
        )
        self.analyze_button.grid(row=0, column=0, padx=(0, PADDING_SMALL))

        self.load_csv_button = ttk.Button(
            button_row,
            text="📂 Load CSV",
            bootstyle="info-outline",
            command=self._handle_load_csv_click,
            padding=(PADDING_MEDIUM, PADDING_SMALL),
        )
        self.load_csv_button.grid(row=0, column=1, padx=PADDING_SMALL)

        self.clear_button = ttk.Button(
            button_row,
            text="🔄 Clear Form",
            bootstyle="secondary-outline",
            command=self.clear_form,
            padding=(PADDING_MEDIUM, PADDING_SMALL),
        )
        self.clear_button.grid(row=0, column=2, padx=PADDING_SMALL)

        self.loading_frame = ttk.Frame(button_row)
        self.loading_frame.grid(row=0, column=3, sticky="w", padx=(PADDING_MEDIUM, 0))
        self.loading_progress = ttk.Progressbar(
            self.loading_frame,
            mode="indeterminate",
            length=120,
            bootstyle="success-striped",
        )
        self.loading_label = ttk.Label(self.loading_frame, text="Analyzing sample...", font=FONT_BODY)
        self._set_loading(False)

    def _clear_sample_placeholder(self, _event: tk.Event) -> None:
        """Remove sample placeholder text when the field gains focus."""
        if self.sample_placeholder_active:
            self.sample_var.set("")
            self.sample_entry.configure(foreground=COLOR_TEXT_PRIMARY)
            self.sample_placeholder_active = False

    def _restore_sample_placeholder(self, _event: tk.Event) -> None:
        """Restore sample placeholder text when the field is left blank."""
        if not self.sample_var.get().strip():
            self.sample_var.set(self.sample_placeholder)
            self.sample_entry.configure(foreground=COLOR_TEXT_MUTED)
            self.sample_placeholder_active = True

    def _on_parameter_focus_out(self, parameter: str, _event: tk.Event) -> None:
        """Validate a parameter when its entry loses focus."""
        if self.validate_field(parameter, require_value=False) and parameter == "Soil Moisture":
            self._sync_slider_from_moisture_entry()

    def _on_moisture_entry_keyrelease(self, parameter: str, _event: tk.Event) -> None:
        """Sync the moisture slider while the numeric entry changes."""
        if parameter != "Soil Moisture" or self._syncing_moisture:
            return
        text = self.value_vars[parameter].get().strip()
        try:
            value = float(text)
        except ValueError:
            return
        if 0.0 <= value <= 100.0:
            self._syncing_moisture = True
            self.moisture_slider_var.set(value)
            self._syncing_moisture = False

    def _on_moisture_slider(self, value: str) -> None:
        """Sync the numeric moisture entry when the slider moves."""
        if self._syncing_moisture:
            return
        self._syncing_moisture = True
        numeric_value = float(value)
        formatted = f"{numeric_value:.0f}" if numeric_value.is_integer() else f"{numeric_value:.1f}"
        self.value_vars["Soil Moisture"].set(formatted)
        self.validate_field("Soil Moisture", require_value=False)
        self._syncing_moisture = False

    def _sync_slider_from_moisture_entry(self) -> None:
        """Move the moisture slider to match the entry value."""
        try:
            value = float(self.value_vars["Soil Moisture"].get())
        except ValueError:
            return
        self._syncing_moisture = True
        self.moisture_slider_var.set(value)
        self._syncing_moisture = False

    def validate_field(self, parameter: str, require_value: bool = False) -> bool:
        """Validate one numeric parameter and update its entry border style."""
        entry = self.entries[parameter]
        text = self.value_vars[parameter].get().strip()
        minimum, maximum = PARAMETER_RANGES[parameter]

        if not text:
            entry.configure(bootstyle="danger" if require_value else "secondary")
            return not require_value

        try:
            value = float(text)
        except ValueError:
            entry.configure(bootstyle="danger")
            return False

        if not math.isfinite(value) or not (minimum <= value <= maximum):
            entry.configure(bootstyle="danger")
            return False

        entry.configure(bootstyle="success")
        return True

    def validate_all_fields(self, require_complete: bool) -> bool:
        """Validate every parameter field."""
        valid = True
        for parameter in PARAMETER_ORDER:
            if not self.validate_field(parameter, require_value=require_complete):
                valid = False
        return valid

    def all_parameter_fields_empty(self) -> bool:
        """Return True when all numeric parameter fields are blank."""
        return all(not self.value_vars[parameter].get().strip() for parameter in PARAMETER_ORDER)

    def get_sample_label(self) -> str:
        """Return the entered sample label or a default label."""
        if self.sample_placeholder_active:
            return "Unknown Field"
        label = self.sample_var.get().strip()
        return label or "Unknown Field"

    def get_input_values(self) -> dict[str, float]:
        """Return validated input values as backend parameter names."""
        values = {parameter: float(self.value_vars[parameter].get().strip()) for parameter in PARAMETER_ORDER}
        validate_inputs(values)
        return values

    def clear_form(self) -> None:
        """Reset the full input form to its initial state."""
        for parameter, value_var in self.value_vars.items():
            value_var.set("")
            self.entries[parameter].configure(bootstyle="secondary")
        self._syncing_moisture = True
        self.moisture_slider_var.set(0.0)
        self._syncing_moisture = False
        self.sample_var.set(self.sample_placeholder)
        self.sample_entry.configure(foreground=COLOR_TEXT_MUTED)
        self.sample_placeholder_active = True
        self.app.set_status_ready()

    def _handle_analyze_click(self) -> None:
        """Validate the form and start single-sample analysis."""
        if self.all_parameter_fields_empty():
            messagebox.showwarning(
                "Missing measurements",
                "Please enter at least the required soil and water parameters before analyzing.",
                parent=self.winfo_toplevel(),
            )
            return

        if not self.validate_all_fields(require_complete=True):
            messagebox.showwarning(
                "Invalid measurements",
                "Please fix the highlighted fields before analyzing.",
                parent=self.winfo_toplevel(),
            )
            return

        try:
            values = self.get_input_values()
        except ValueError:
            messagebox.showwarning(
                "Invalid measurements",
                "Please fix the highlighted fields before analyzing.",
                parent=self.winfo_toplevel(),
            )
            return

        sample_label = self.get_sample_label()
        self._set_loading(True)
        self.app.set_status(STATUS_ANALYZING)

        worker = threading.Thread(target=self._run_single_analysis, args=(sample_label, values), daemon=True)
        worker.start()

    def _run_single_analysis(self, sample_label: str, values: dict[str, float]) -> None:
        """Run backend analysis for one sample in a background thread."""
        try:
            result = self.app.process_sample(sample_label, values)
        except FileNotFoundError as exc:
            self.after(0, partial(self._finish_model_error, exc))
        except Exception as exc:
            details = traceback.format_exc()
            self.after(0, partial(self._finish_backend_error, exc, details))
        else:
            self.after(0, partial(self._finish_single_success, result))

    def _finish_single_success(self, result: dict[str, Any]) -> None:
        """Finish the single-sample workflow after a successful backend result."""
        self._set_loading(False)
        self.app.add_history_result(result)
        self.app.show_results(result)
        self.app.set_status_complete()

    def _finish_model_error(self, exc: FileNotFoundError) -> None:
        """Finish a workflow that failed because model files are missing."""
        self._set_loading(False)
        self.app.show_model_error(exc)
        self.app.set_status_ready()

    def _finish_backend_error(self, exc: Exception, details: str) -> None:
        """Finish a workflow that failed unexpectedly in the backend."""
        self._set_loading(False)
        self.app.show_backend_error(exc, details)
        self.app.set_status_ready()

    def _handle_load_csv_click(self) -> None:
        """Open a CSV file and begin batch processing."""
        path = filedialog.askopenfilename(
            title="Load AquaSoil-AI CSV",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            parent=self.winfo_toplevel(),
        )
        if not path:
            return

        try:
            dataframe = pd.read_csv(path)
        except Exception as exc:
            self.app.show_backend_error(exc, traceback.format_exc())
            return

        missing = [parameter for parameter in PARAMETER_ORDER if parameter not in dataframe.columns]
        if missing:
            missing_text = "\n".join(f"- {column}" for column in missing)
            messagebox.showerror(
                "CSV columns missing",
                f"The CSV file is missing these required columns:\n\n{missing_text}",
                parent=self.winfo_toplevel(),
            )
            return

        if dataframe.empty:
            messagebox.showwarning("Empty CSV", "The selected CSV file has no rows to process.", parent=self.winfo_toplevel())
            return

        self._start_batch_processing(Path(path), dataframe)

    def _start_batch_processing(self, path: Path, dataframe: pd.DataFrame) -> None:
        """Show the progress dialog and run batch processing in the background."""
        self._create_batch_dialog(path.name, len(dataframe))
        self.analyze_button.configure(state="disabled")
        self.load_csv_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")
        self.app.set_status("Analyzing...")

        worker = threading.Thread(target=self._run_batch_analysis, args=(dataframe,), daemon=True)
        worker.start()

    def _create_batch_dialog(self, filename: str, total_rows: int) -> None:
        """Create the batch progress dialog."""
        self.batch_dialog = tk.Toplevel(self.winfo_toplevel())
        self.batch_dialog.title("Batch Processing")
        self.batch_dialog.transient(self.winfo_toplevel())
        self.batch_dialog.resizable(False, False)
        self.batch_dialog.protocol("WM_DELETE_WINDOW", self._ignore_batch_close)

        container = ttk.Frame(self.batch_dialog, padding=PADDING_LARGE)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text=f"Processing {filename}", font=FONT_SECTION).pack(anchor="w")
        self.batch_label = ttk.Label(container, text=f"Processing 0/{total_rows} samples...", font=FONT_BODY)
        self.batch_label.pack(anchor="w", pady=(PADDING_MEDIUM, PADDING_SMALL))
        self.batch_progress = ttk.Progressbar(
            container,
            maximum=total_rows,
            value=0,
            length=360,
            bootstyle="success-striped",
        )
        self.batch_progress.pack(fill="x")
        self.app.center_child_window(self.batch_dialog, width=430, height=150)

    def _ignore_batch_close(self) -> None:
        """Ignore manual close attempts while batch processing is active."""
        return

    def _run_batch_analysis(self, dataframe: pd.DataFrame) -> None:
        """Process valid CSV rows through the backend pipeline."""
        results: list[dict[str, Any]] = []
        skipped: list[str] = []
        total_rows = len(dataframe)

        for position, (_, row) in enumerate(dataframe.iterrows(), start=1):
            self.after(0, partial(self._update_batch_progress, position - 1, total_rows))
            try:
                sample_label = str(row.get("Sample", f"Sample_{position}")).strip() or f"Sample_{position}"
                values = self._values_from_csv_row(row)
                validate_inputs(values)
            except Exception as exc:
                skipped.append(f"Row {position}: {exc}")
                self.after(0, partial(self._update_batch_progress, position, total_rows))
                continue

            try:
                result = self.app.process_sample(sample_label, values)
                self.app.save_automatic_report(result)
                results.append(result)
            except FileNotFoundError as exc:
                self.after(0, partial(self._finish_batch_model_error, exc))
                return
            except Exception as exc:
                details = traceback.format_exc()
                self.after(0, partial(self._finish_batch_backend_error, exc, details))
                return

            self.after(0, partial(self._update_batch_progress, position, total_rows))

        self.after(0, partial(self._finish_batch_success, results, skipped))

    def _values_from_csv_row(self, row: pd.Series) -> dict[str, float]:
        """Convert one CSV row into backend input values."""
        values: dict[str, float] = {}
        for parameter in PARAMETER_ORDER:
            value = row[parameter]
            if pd.isna(value):
                raise ValueError(f"Missing value for {parameter}")
            values[parameter] = float(value)
        return values

    def _update_batch_progress(self, current: int, total: int) -> None:
        """Update the batch progress dialog text and bar value."""
        if self.batch_label is not None:
            self.batch_label.configure(text=f"Processing {current}/{total} samples...")
        if self.batch_progress is not None:
            self.batch_progress.configure(value=current)

    def _finish_batch_success(self, results: list[dict[str, Any]], skipped: list[str]) -> None:
        """Finish batch mode after all rows have been attempted."""
        self._close_batch_dialog()
        self._restore_buttons_after_processing()

        for result in results:
            self.app.add_history_result(result)

        if results:
            self.app.show_history()
            self.app.set_status_complete()
            message = f"Processed {len(results)} sample(s)."
            if skipped:
                message += f"\nSkipped {len(skipped)} invalid row(s)."
            message += "\nIndividual reports were saved in the reports folder."
            messagebox.showinfo("Batch complete", message, parent=self.winfo_toplevel())
        else:
            self.app.set_status_ready()
            messagebox.showwarning(
                "No valid rows",
                "No valid rows were processed. Please review the CSV values.",
                parent=self.winfo_toplevel(),
            )

        if skipped:
            self._show_skipped_rows(skipped)

    def _finish_batch_model_error(self, exc: FileNotFoundError) -> None:
        """Finish batch mode when model files are missing."""
        self._close_batch_dialog()
        self._restore_buttons_after_processing()
        self.app.show_model_error(exc)
        self.app.set_status_ready()

    def _finish_batch_backend_error(self, exc: Exception, details: str) -> None:
        """Finish batch mode after an unexpected backend error."""
        self._close_batch_dialog()
        self._restore_buttons_after_processing()
        self.app.show_backend_error(exc, details)
        self.app.set_status_ready()

    def _show_skipped_rows(self, skipped: list[str]) -> None:
        """Show a warning dialog with a concise list of skipped rows."""
        preview = "\n".join(skipped[:8])
        if len(skipped) > 8:
            preview += f"\n...and {len(skipped) - 8} more."
        messagebox.showwarning(
            "Invalid rows skipped",
            f"The following rows were skipped:\n\n{preview}",
            parent=self.winfo_toplevel(),
        )

    def _close_batch_dialog(self) -> None:
        """Destroy the batch progress dialog if it exists."""
        if self.batch_dialog is not None and self.batch_dialog.winfo_exists():
            self.batch_dialog.destroy()
        self.batch_dialog = None
        self.batch_progress = None
        self.batch_label = None

    def _restore_buttons_after_processing(self) -> None:
        """Restore input tab buttons after background processing."""
        self.analyze_button.configure(state="normal")
        self.load_csv_button.configure(state="normal")
        self.clear_button.configure(state="normal")

    def _set_loading(self, active: bool) -> None:
        """Toggle the single-sample loading indicator and action buttons."""
        if active:
            self.analyze_button.configure(state="disabled")
            self.loading_progress.pack(side="left")
            self.loading_label.pack(side="left", padx=(PADDING_SMALL, 0))
            self.loading_progress.start(12)
        else:
            self.analyze_button.configure(state="normal")
            self.loading_progress.stop()
            self.loading_progress.pack_forget()
            self.loading_label.pack_forget()
