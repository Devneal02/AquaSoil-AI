"""Reusable classification summary card component."""

from __future__ import annotations

import tkinter as tk

import ttkbootstrap as ttk

from gui.theme import (
    CLASS_ACCENTS,
    CLASS_BACKGROUNDS,
    CLASS_BOOTSTYLES,
    COLOR_CARD_BG,
    COLOR_SHADOW,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_CARD_CLASS,
    FONT_CARD_LABEL,
    PADDING_MEDIUM,
)


class ClassificationCard(tk.Frame):
    """Display a soil or water quality class with confidence progress."""

    def __init__(self, master: tk.Misc, title: str, icon: str) -> None:
        """Initialize the card widget."""
        super().__init__(master, bg=COLOR_SHADOW, padx=3, pady=3)
        self.title = title
        self.icon = icon
        self.inner = tk.Frame(self, bg=COLOR_CARD_BG, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        self.inner.pack(fill="both", expand=True)

        self.title_label = tk.Label(
            self.inner,
            text=f"{self.icon} {self.title}",
            font=FONT_CARD_LABEL,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        self.title_label.pack(anchor="center")

        self.class_label = tk.Label(
            self.inner,
            text="--",
            font=FONT_CARD_CLASS,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        self.class_label.pack(pady=(PADDING_MEDIUM, 0))

        self.confidence_label = tk.Label(
            self.inner,
            text="Confidence: --%",
            font=FONT_BODY,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CARD_BG,
        )
        self.confidence_label.pack(pady=(0, PADDING_MEDIUM))

        self.progress = ttk.Progressbar(
            self.inner,
            orient="horizontal",
            mode="determinate",
            maximum=100,
            bootstyle="secondary-striped",
        )
        self.progress.pack(fill="x")

        self.progress_text = tk.Label(
            self.inner,
            text="░░░░░░░░░░ 0%",
            font=FONT_BODY,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CARD_BG,
        )
        self.progress_text.pack(pady=(PADDING_MEDIUM // 2, 0))

    def update_card(self, class_name: str, confidence: float) -> None:
        """Update the card content and class-specific styling."""
        normalized = self._normalize_class(class_name)
        safe_confidence = self._safe_confidence(confidence)
        background = CLASS_BACKGROUNDS.get(normalized, CLASS_BACKGROUNDS["UNKNOWN"])
        accent = CLASS_ACCENTS.get(normalized, CLASS_ACCENTS["UNKNOWN"])
        bootstyle = CLASS_BOOTSTYLES.get(normalized, CLASS_BOOTSTYLES["UNKNOWN"])

        self.inner.configure(bg=background)
        for label in (
            self.title_label,
            self.class_label,
            self.confidence_label,
            self.progress_text,
        ):
            label.configure(bg=background)

        self.title_label.configure(fg=COLOR_TEXT_PRIMARY)
        self.class_label.configure(text=normalized, fg=accent)
        self.confidence_label.configure(text=f"Confidence: {safe_confidence:.0f}%")
        self.progress.configure(value=safe_confidence, bootstyle=f"{bootstyle}-striped")
        self.progress_text.configure(text=self._progress_blocks(safe_confidence), fg=accent)

    def clear(self) -> None:
        """Reset the card to its empty state."""
        self.inner.configure(bg=COLOR_CARD_BG)
        for label in (
            self.title_label,
            self.class_label,
            self.confidence_label,
            self.progress_text,
        ):
            label.configure(bg=COLOR_CARD_BG)
        self.class_label.configure(text="--", fg=COLOR_TEXT_PRIMARY)
        self.confidence_label.configure(text="Confidence: --%")
        self.progress.configure(value=0, bootstyle="secondary-striped")
        self.progress_text.configure(text="░░░░░░░░░░ 0%", fg=COLOR_TEXT_MUTED)

    def _normalize_class(self, class_name: str) -> str:
        """Return a display-safe classification name."""
        if not class_name:
            return "UNKNOWN"
        return str(class_name).strip().upper()

    def _safe_confidence(self, confidence: float) -> float:
        """Clamp a confidence value into the visible progress range."""
        try:
            value = float(confidence)
        except (TypeError, ValueError):
            value = 0.0
        return max(0.0, min(100.0, value))

    def _progress_blocks(self, confidence: float) -> str:
        """Render a compact text progress indicator."""
        filled = int(round(confidence / 10.0))
        filled = max(0, min(10, filled))
        return f"{'█' * filled}{'░' * (10 - filled)} {confidence:.0f}%"
