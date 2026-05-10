"""Reusable advisory recommendation card component."""

from __future__ import annotations

import tkinter as tk

from gui.theme import (
    COLOR_CARD_BG,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    PADDING_MEDIUM,
    SEVERITY_STYLES,
)


class RecommendationCard(tk.Frame):
    """Display one advisory recommendation with severity styling."""

    def __init__(self, master: tk.Misc, recommendation: str, wraplength: int = 680) -> None:
        """Initialize the recommendation card."""
        self.recommendation = recommendation
        self.severity = self._severity_from_text(recommendation)
        self.style_data = SEVERITY_STYLES[self.severity]
        self.target_bg = self.style_data["background"]
        self.wraplength = wraplength

        super().__init__(master, bg=COLOR_CARD_BG, padx=0, pady=0)
        self.configure(highlightthickness=0)
        self._build_widgets()

    def _build_widgets(self) -> None:
        """Create the inner severity stripe and text labels."""
        self.left_bar = tk.Frame(self, bg=self.style_data["accent"], width=7)
        self.left_bar.pack(side="left", fill="y")
        self.left_bar.pack_propagate(False)

        self.body = tk.Frame(self, bg=COLOR_CARD_BG, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        self.body.pack(side="left", fill="both", expand=True)

        tag, text = self._split_recommendation(self.recommendation)

        self.header = tk.Label(
            self.body,
            text=f"{self.style_data['icon']} {tag}",
            font=FONT_BODY_BOLD,
            fg=self.style_data["accent"],
            bg=COLOR_CARD_BG,
        )
        self.header.pack(anchor="w")

        self.message = tk.Label(
            self.body,
            text=text,
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
            justify="left",
            wraplength=self.wraplength,
        )
        self.message.pack(anchor="w", fill="x", pady=(4, 0))

    def fade_in(self, step: int = 0, steps: int = 8) -> None:
        """Animate the card from neutral white into its severity background."""
        if step > steps:
            self._set_background(self.target_bg)
            return
        color = self._blend_colors(COLOR_CARD_BG, self.target_bg, step / steps)
        self._set_background(color)
        self.after(25, self.fade_in, step + 1, steps)

    def set_wraplength(self, wraplength: int) -> None:
        """Update the message wrap length after container resize."""
        self.wraplength = max(220, wraplength)
        self.message.configure(wraplength=self.wraplength)

    def _set_background(self, color: str) -> None:
        """Apply one background color to the body and labels."""
        self.body.configure(bg=color)
        self.header.configure(bg=color)
        self.message.configure(bg=color)

    def _severity_from_text(self, text: str) -> str:
        """Extract a severity token from the recommendation text."""
        upper_text = text.upper()
        if "[CRITICAL]" in upper_text:
            return "CRITICAL"
        if "[WARNING]" in upper_text:
            return "WARNING"
        return "OK"

    def _split_recommendation(self, text: str) -> tuple[str, str]:
        """Separate a leading severity tag from the recommendation body."""
        if text.startswith("[") and "]" in text:
            tag, _, body = text.partition("]")
            return f"{tag}]", body.strip()
        return f"[{self.severity}]", text.strip()

    def _blend_colors(self, start: str, end: str, fraction: float) -> str:
        """Blend two Tk color strings and return a hex color."""
        fraction = max(0.0, min(1.0, fraction))
        start_rgb = self._rgb_8bit(start)
        end_rgb = self._rgb_8bit(end)
        blended = tuple(
            int(start_rgb[index] + (end_rgb[index] - start_rgb[index]) * fraction)
            for index in range(3)
        )
        return self._hex_from_rgb(blended)

    def _rgb_8bit(self, color: str) -> tuple[int, int, int]:
        """Convert a Tk color string to an 8-bit RGB tuple."""
        red, green, blue = self.winfo_rgb(color)
        return red // 256, green // 256, blue // 256

    def _hex_from_rgb(self, rgb: tuple[int, int, int]) -> str:
        """Convert an 8-bit RGB tuple into a Tk hex color string."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
