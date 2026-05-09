"""About tab for AquaSoil-AI project information and usage guidance."""

from __future__ import annotations

import tkinter as tk

import ttkbootstrap as ttk

from gui.theme import (
    COLOR_DIVIDER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SECTION,
    FONT_SUBTITLE,
    FONT_TITLE,
    PADDING_LARGE,
    PADDING_MEDIUM,
    PADDING_SMALL,
    TEAM_MEMBERS,
)


class AboutTab(ttk.Frame):
    """Show application, course, team, and technology information."""

    def __init__(self, master: tk.Misc) -> None:
        """Initialize the about tab."""
        super().__init__(master, padding=PADDING_LARGE)
        self._build_layout()

    def _build_layout(self) -> None:
        """Build the about screen content."""
        self.columnconfigure(0, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, PADDING_MEDIUM))
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text="🌿", font=("Arial", 40)).grid(row=0, column=0, rowspan=2, padx=(0, PADDING_MEDIUM))
        ttk.Label(header, text="AquaSoil-AI", font=FONT_TITLE, foreground=COLOR_TEXT_PRIMARY).grid(
            row=0,
            column=1,
            sticky="w",
        )
        ttk.Label(
            header,
            text="v1.0 · Intelligent Soil and Water Quality Monitoring and Advisory System",
            font=FONT_SUBTITLE,
            foreground=COLOR_TEXT_MUTED,
        ).grid(row=1, column=1, sticky="w")

        divider = tk.Frame(self, height=2, bg=COLOR_DIVIDER)
        divider.grid(row=1, column=0, sticky="ew", pady=(0, PADDING_LARGE))

        self._add_section(
            row=2,
            title="Project Context",
            lines=[
                "Built for farmers in Kabacan, North Cotabato.",
                "Course: CS 17A – Introduction to Artificial Intelligence, 3-BSCS-A, A.Y. 2025-2026",
                "Institution: Kabacan, North Cotabato",
                "Instructor: Joseph C. Lorilla",
            ],
        )
        self._add_section(row=3, title="Team Members", lines=TEAM_MEMBERS)
        self._add_section(
            row=4,
            title="Technology Stack",
            lines=["Python 3.9+ | Scikit-Learn | ttkbootstrap | Matplotlib"],
        )
        self._add_section(
            row=5,
            title="How to Use",
            lines=[
                "1. Enter soil and water parameter values",
                "2. Click Analyze Sample",
                "3. View classification and recommendations",
                "4. Save report for your records",
            ],
        )

    def _add_section(self, row: int, title: str, lines: list[str]) -> None:
        """Add one labeled about section."""
        section = ttk.Frame(self, padding=(0, 0, 0, PADDING_LARGE))
        section.grid(row=row, column=0, sticky="ew")
        section.columnconfigure(0, weight=1)

        ttk.Label(section, text=title, font=FONT_SECTION, foreground=COLOR_TEXT_PRIMARY).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, PADDING_SMALL),
        )

        for index, line in enumerate(lines, start=1):
            ttk.Label(
                section,
                text=line,
                font=FONT_BODY_BOLD if title == "Team Members" else FONT_BODY,
                foreground=COLOR_TEXT_PRIMARY,
                wraplength=780,
                justify="left",
            ).grid(row=index, column=0, sticky="w", pady=2)
