"""Matplotlib chart component embedded in the Tkinter results tab."""

from __future__ import annotations

import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from gui.theme import (
    COLOR_BACKGROUND,
    COLOR_CARD_BG,
    COLOR_CRITICAL,
    COLOR_OK,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    OPTIMAL_RANGES,
    PARAMETER_ORDER,
    PARAMETER_SHORT_LABELS,
)


class ParameterChart(tk.Frame):
    """Render normalized parameter bars against optimal thresholds."""

    def __init__(self, master: tk.Misc) -> None:
        """Initialize the embedded Matplotlib chart."""
        super().__init__(master, bg=COLOR_CARD_BG)
        self.figure = Figure(figsize=(7.2, 3.4), dpi=100)
        self.figure.patch.set_facecolor(COLOR_CARD_BG)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.configure(bg=COLOR_CARD_BG, highlightthickness=0)
        self.canvas_widget.pack(fill="both", expand=True)
        self.clear()

    def update_chart(self, input_values: dict[str, float], parameter_ranges: dict[str, tuple[float, float]]) -> None:
        """Update the chart with the latest parameter values."""
        labels: list[str] = []
        scaled_values: list[float] = []
        colors: list[str] = []
        threshold_values: list[float] = []
        actual_values: list[float] = []

        for parameter in PARAMETER_ORDER:
            if parameter not in input_values or parameter not in parameter_ranges:
                continue
            value = float(input_values[parameter])
            minimum, maximum = parameter_ranges[parameter]
            optimal_minimum, optimal_maximum = OPTIMAL_RANGES[parameter]
            optimal_midpoint = (optimal_minimum + optimal_maximum) / 2.0

            labels.append(PARAMETER_SHORT_LABELS[parameter])
            actual_values.append(value)
            scaled_values.append(self._scale_value(value, minimum, maximum))
            threshold_values.append(self._scale_value(optimal_midpoint, minimum, maximum))
            colors.append(COLOR_OK if optimal_minimum <= value <= optimal_maximum else COLOR_CRITICAL)

        self.axes.clear()
        self.axes.set_facecolor(COLOR_CARD_BG)
        self.axes.barh(labels, scaled_values, color=colors, alpha=0.9, height=0.62)

        for index, threshold in enumerate(threshold_values):
            self.axes.vlines(
                threshold,
                index - 0.34,
                index + 0.34,
                colors=COLOR_TEXT_MUTED,
                linestyles="dotted",
                linewidth=1.8,
            )

        for index, value in enumerate(actual_values):
            label_x = min(104.0, scaled_values[index] + 2.0)
            self.axes.text(
                label_x,
                index,
                self._format_value(value),
                va="center",
                ha="left",
                fontsize=9,
                color=COLOR_TEXT_PRIMARY,
            )

        self.axes.set_xlim(0, 110)
        self.axes.set_xlabel("Percent of valid measurement range", fontsize=9, color=COLOR_TEXT_MUTED)
        self.axes.tick_params(axis="both", labelsize=9, colors=COLOR_TEXT_PRIMARY)
        self.axes.grid(axis="x", linestyle=":", alpha=0.25)
        self.axes.invert_yaxis()

        for spine in self.axes.spines.values():
            spine.set_visible(False)

        self.figure.tight_layout()
        self.canvas.draw_idle()

    def clear(self) -> None:
        """Show an empty chart state."""
        self.axes.clear()
        self.axes.set_facecolor(COLOR_CARD_BG)
        self.axes.text(
            0.5,
            0.5,
            "Run an analysis to view parameter bars.",
            ha="center",
            va="center",
            transform=self.axes.transAxes,
            fontsize=FONT_BODY[1],
            color=COLOR_TEXT_MUTED,
        )
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        for spine in self.axes.spines.values():
            spine.set_visible(False)
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def save_chart(self, filepath: str) -> None:
        """Save the current chart figure to a PNG file."""
        self.figure.savefig(filepath, facecolor=COLOR_BACKGROUND, bbox_inches="tight")

    def _scale_value(self, value: float, minimum: float, maximum: float) -> float:
        """Scale a raw value to a 0-100 valid-range percentage."""
        if maximum == minimum:
            return 0.0
        scaled = ((value - minimum) / (maximum - minimum)) * 100.0
        return max(0.0, min(100.0, scaled))

    def _format_value(self, value: float) -> str:
        """Format chart data labels without distracting decimals."""
        if value == int(value):
            return str(int(value))
        return f"{value:.1f}"
