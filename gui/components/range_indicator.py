"""Small range meter for live soil and water input feedback."""

from __future__ import annotations

import math
import tkinter as tk

from gui.theme import (
    COLOR_CARD_BG,
    COLOR_CRITICAL,
    COLOR_DIVIDER,
    COLOR_OK,
    COLOR_TEXT_MUTED,
    COLOR_WARNING,
    OPTIMAL_RANGES,
)
from src.preprocess import PARAMETER_RANGES


class RangeIndicator(tk.Canvas):
    """Draw valid range, target band, and current value for one parameter."""

    def __init__(self, master: tk.Misc, parameter: str) -> None:
        """Initialize the meter for a parameter."""
        super().__init__(master, height=32, bg=COLOR_CARD_BG, highlightthickness=0)
        self.parameter = parameter
        self.value: float | None = None
        self.valid = False
        self.minimum, self.maximum = PARAMETER_RANGES[parameter]
        self.target_minimum, self.target_maximum = OPTIMAL_RANGES[parameter]
        self.bind("<Configure>", self._on_configure)
        self.redraw()

    def set_value(self, value: float | None, valid: bool) -> None:
        """Set the current parameter value and redraw the meter."""
        self.value = value
        self.valid = valid
        self.redraw()

    def redraw(self) -> None:
        """Render the meter."""
        self.delete("all")
        width = max(self.winfo_width(), 140)
        height = max(self.winfo_height(), 32)
        left = 4
        right = width - 4
        top = 5
        bottom = 12

        self.create_rectangle(left, top, right, bottom, fill=COLOR_DIVIDER, outline="")

        target_left = self._position(self.target_minimum, left, right)
        target_right = self._position(self.target_maximum, left, right)
        self.create_rectangle(target_left, top, target_right, bottom, fill=COLOR_OK, outline="")

        label_y = height - 5
        self.create_text(left, label_y, text="Low", fill=COLOR_TEXT_MUTED, font=("Arial", 7), anchor="sw")
        self.create_text(right, label_y, text="High", fill=COLOR_TEXT_MUTED, font=("Arial", 7), anchor="se")

        if self.value is None or not self.valid:
            return

        marker_x = self._position(self.value, left, right)
        marker_color = self._marker_color(self.value)
        self.create_line(marker_x, 3, marker_x, bottom + 3, fill=marker_color, width=2)
        self.create_polygon(
            marker_x,
            2,
            marker_x - 4,
            6,
            marker_x + 4,
            6,
            fill=marker_color,
            outline=marker_color,
        )

    def _position(self, value: float, left: int, right: int) -> float:
        if self.maximum == self.minimum:
            return float(left)
        fraction = (float(value) - self.minimum) / (self.maximum - self.minimum)
        fraction = max(0.0, min(1.0, fraction))
        return left + fraction * (right - left)

    def _marker_color(self, value: float) -> str:
        if not math.isfinite(value):
            return COLOR_CRITICAL
        if self.target_minimum <= value <= self.target_maximum:
            return COLOR_OK
        if self.minimum <= value <= self.maximum:
            return COLOR_WARNING
        return COLOR_CRITICAL

    def _on_configure(self, _event: tk.Event) -> None:
        self.redraw()
