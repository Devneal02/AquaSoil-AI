"""Results tab for classifications, recommendations, charts, and exports."""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, Optional

import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk

from gui.components.card import ClassificationCard
from gui.components.chart import ParameterChart
from gui.components.rec_card import RecommendationCard
from gui.theme import (
    COLOR_BACKGROUND,
    COLOR_CARD_BG,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_MONO,
    FONT_SECTION,
    PADDING_LARGE,
    PADDING_MEDIUM,
    PADDING_SMALL,
)
from src.preprocess import PARAMETER_RANGES


class ResultsTab(ttk.Frame):
    """Display backend analysis output and report export tools."""

    def __init__(self, master: tk.Misc, app_controller: Any) -> None:
        """Initialize the results tab."""
        super().__init__(master)
        self.app = app_controller
        self.current_result: Optional[dict[str, Any]] = None
        self.recommendation_cards: list[RecommendationCard] = []
        self._build_layout()

    def _build_layout(self) -> None:
        """Build the scrollable results layout."""
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, bg=COLOR_BACKGROUND, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.content = ttk.Frame(self.canvas, padding=PADDING_MEDIUM)
        self.content_window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

        self.content.columnconfigure(0, weight=1)
        self._build_summary_section()
        self._build_recommendations_section()
        self._build_chart_section()
        self._build_export_row()

    def _build_summary_section(self) -> None:
        """Build the classification summary cards."""
        section = self._section_frame("Classification Summary")
        section.grid(row=0, column=0, sticky="ew", pady=(0, PADDING_MEDIUM))
        section.columnconfigure(0, weight=1)
        section.columnconfigure(1, weight=1)

        self.soil_card = ClassificationCard(section, "SOIL QUALITY", "🟤")
        self.soil_card.grid(row=1, column=0, sticky="nsew", padx=(0, PADDING_MEDIUM // 2), pady=(PADDING_SMALL, 0))

        self.water_card = ClassificationCard(section, "WATER QUALITY", "💧")
        self.water_card.grid(row=1, column=1, sticky="nsew", padx=(PADDING_MEDIUM // 2, 0), pady=(PADDING_SMALL, 0))

    def _build_recommendations_section(self) -> None:
        """Build the scrollable recommendations panel."""
        section = self._section_frame("📋 Advisory Recommendations")
        section.grid(row=1, column=0, sticky="ew", pady=(0, PADDING_MEDIUM))
        section.columnconfigure(0, weight=1)

        panel = ttk.Frame(section)
        panel.grid(row=1, column=0, sticky="ew", pady=(PADDING_SMALL, 0))
        panel.columnconfigure(0, weight=1)

        self.rec_canvas = tk.Canvas(panel, height=210, bg=COLOR_CARD_BG, highlightthickness=0)
        self.rec_scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.rec_canvas.yview)
        self.rec_canvas.configure(yscrollcommand=self.rec_scrollbar.set)
        self.rec_canvas.grid(row=0, column=0, sticky="ew")
        self.rec_scrollbar.grid(row=0, column=1, sticky="ns")

        self.rec_content = ttk.Frame(self.rec_canvas, padding=PADDING_SMALL)
        self.rec_window = self.rec_canvas.create_window((0, 0), window=self.rec_content, anchor="nw")
        self.rec_content.bind("<Configure>", self._on_rec_content_configure)
        self.rec_canvas.bind("<Configure>", self._on_rec_canvas_configure)

        self.empty_recommendations: Optional[ttk.Label] = None
        self._show_empty_recommendations()

    def _build_chart_section(self) -> None:
        """Build the parameter analysis chart section."""
        section = self._section_frame("📈 Parameter Analysis")
        section.grid(row=2, column=0, sticky="ew", pady=(0, PADDING_MEDIUM))
        section.columnconfigure(0, weight=1)

        chart_shell = tk.Frame(section, bg=COLOR_CARD_BG, padx=PADDING_SMALL, pady=PADDING_SMALL)
        chart_shell.grid(row=1, column=0, sticky="ew", pady=(PADDING_SMALL, 0))
        chart_shell.columnconfigure(0, weight=1)

        self.chart = ParameterChart(chart_shell)
        self.chart.grid(row=0, column=0, sticky="ew")

    def _build_export_row(self) -> None:
        """Build report, chart, and print-preview buttons."""
        row = ttk.Frame(self.content)
        row.grid(row=3, column=0, sticky="ew", pady=(0, PADDING_LARGE))
        row.columnconfigure(3, weight=1)

        self.save_report_button = ttk.Button(
            row,
            text="💾 Save Report (.txt)",
            bootstyle="primary",
            command=self.save_report,
            padding=(PADDING_MEDIUM, PADDING_SMALL),
        )
        self.save_report_button.grid(row=0, column=0, padx=(0, PADDING_SMALL))

        self.export_chart_button = ttk.Button(
            row,
            text="📊 Export Chart (.png)",
            bootstyle="info-outline",
            command=self.export_chart,
            padding=(PADDING_MEDIUM, PADDING_SMALL),
        )
        self.export_chart_button.grid(row=0, column=1, padx=PADDING_SMALL)

        self.print_preview_button = ttk.Button(
            row,
            text="🖨️ Print Preview",
            bootstyle="secondary-outline",
            command=self.show_print_preview,
            padding=(PADDING_MEDIUM, PADDING_SMALL),
        )
        self.print_preview_button.grid(row=0, column=2, padx=PADDING_SMALL)

    def _section_frame(self, title: str) -> ttk.Frame:
        """Create a standard section frame with a heading label."""
        frame = ttk.Frame(self.content, padding=PADDING_MEDIUM)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=title, font=FONT_SECTION, foreground=COLOR_TEXT_PRIMARY).grid(
            row=0,
            column=0,
            sticky="w",
        )
        return frame

    def show_result(self, result: dict[str, Any]) -> None:
        """Populate all results sections from one analysis record."""
        self.current_result = result
        self.soil_card.update_card(result["soil_class"], result["soil_confidence"])
        self.water_card.update_card(result["water_class"], result["water_confidence"])
        self._show_recommendations(result["recommendations"])
        self.chart.update_chart(result["input_values"], PARAMETER_RANGES)
        self.canvas.yview_moveto(0)

    def clear(self) -> None:
        """Reset the results tab to its empty state."""
        self.current_result = None
        self.soil_card.clear()
        self.water_card.clear()
        self._clear_recommendations()
        self._show_empty_recommendations()
        self.chart.clear()

    def save_report(self) -> None:
        """Open a save dialog and write the current report as a text file."""
        if not self._has_result():
            return
        sample = self.current_result["sample"]
        default_name = self.app.safe_report_filename(sample)
        path = filedialog.asksaveasfilename(
            title="Save AquaSoil-AI Report",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
            parent=self.winfo_toplevel(),
        )
        if not path:
            return
        self.app.write_report_file(Path(path), self.current_result)
        messagebox.showinfo("Report saved", "The advisory report was saved successfully.", parent=self.winfo_toplevel())

    def export_chart(self) -> None:
        """Export the current Matplotlib chart as a PNG image."""
        if not self._has_result():
            return
        path = filedialog.asksaveasfilename(
            title="Export Parameter Chart",
            defaultextension=".png",
            filetypes=(("PNG image", "*.png"), ("All files", "*.*")),
            parent=self.winfo_toplevel(),
        )
        if not path:
            return
        self.chart.save_chart(path)
        messagebox.showinfo("Chart exported", "The parameter chart was exported successfully.", parent=self.winfo_toplevel())

    def show_print_preview(self) -> None:
        """Open a read-only print preview window for the current report."""
        if not self._has_result():
            return

        preview = tk.Toplevel(self.winfo_toplevel())
        preview.title("Print Preview")
        preview.transient(self.winfo_toplevel())
        preview.columnconfigure(0, weight=1)
        preview.rowconfigure(0, weight=1)

        text = tk.Text(
            preview,
            wrap="word",
            font=FONT_MONO,
            bg=COLOR_CARD_BG,
            fg=COLOR_TEXT_PRIMARY,
            padx=PADDING_MEDIUM,
            pady=PADDING_MEDIUM,
        )
        text.grid(row=0, column=0, sticky="nsew")
        text.insert("1.0", self.app.format_report_text(self.current_result))
        text.configure(state="disabled")

        close_button = ttk.Button(preview, text="Close", bootstyle="primary", command=preview.destroy)
        close_button.grid(row=1, column=0, sticky="e", padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        self.app.center_child_window(preview, width=640, height=520)

    def _show_recommendations(self, recommendations: list[str]) -> None:
        """Display recommendation cards one by one."""
        self._clear_recommendations()
        wraplength = max(320, self.rec_canvas.winfo_width() - 60)
        for index, recommendation in enumerate(recommendations):
            self.after(index * 90, partial(self._add_recommendation_card, recommendation, wraplength))

    def _add_recommendation_card(self, recommendation: str, wraplength: int) -> None:
        """Create and animate one recommendation card."""
        card = RecommendationCard(self.rec_content, recommendation, wraplength=wraplength)
        card.pack(fill="x", padx=PADDING_SMALL, pady=(0, PADDING_SMALL))
        card.fade_in()
        self.recommendation_cards.append(card)

    def _clear_recommendations(self) -> None:
        """Remove all recommendation cards from the scrollable panel."""
        for child in self.rec_content.winfo_children():
            child.destroy()
        self.empty_recommendations = None
        self.recommendation_cards.clear()

    def _show_empty_recommendations(self) -> None:
        """Show the empty-state message in the recommendation panel."""
        self.empty_recommendations = ttk.Label(
            self.rec_content,
            text="Run an analysis to view advisory recommendations.",
            font=FONT_BODY,
            foreground=COLOR_TEXT_MUTED,
        )
        self.empty_recommendations.pack(anchor="center", pady=PADDING_LARGE)

    def _has_result(self) -> bool:
        """Return True if a result is available, otherwise show a notice."""
        if self.current_result is not None:
            return True
        messagebox.showinfo("No results yet", "Run an analysis first to create a report.", parent=self.winfo_toplevel())
        return False

    def _on_content_configure(self, _event: tk.Event) -> None:
        """Update the outer scroll region when result content changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        """Keep the scrollable content width aligned with the canvas."""
        self.canvas.itemconfigure(self.content_window, width=event.width)

    def _on_rec_content_configure(self, _event: tk.Event) -> None:
        """Update the recommendation panel scroll region."""
        self.rec_canvas.configure(scrollregion=self.rec_canvas.bbox("all"))

    def _on_rec_canvas_configure(self, event: tk.Event) -> None:
        """Keep recommendation cards aligned to the panel width."""
        self.rec_canvas.itemconfigure(self.rec_window, width=event.width)
        wraplength = max(320, event.width - 70)
        for card in self.recommendation_cards:
            card.set_wraplength(wraplength)

    def _bind_mousewheel(self, _event: tk.Event) -> None:
        """Bind mousewheel scrolling while the pointer is over the results tab."""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event: tk.Event) -> None:
        """Remove the mousewheel binding when the pointer leaves the results tab."""
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        """Scroll the results page with the mousewheel."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
