"""Farmer dashboard tab for at-a-glance field status."""

from __future__ import annotations

from typing import Any

import tkinter as tk

import ttkbootstrap as ttk

from gui.farmer_helper import ACTION_GROUPS, build_action_plan, clean_recommendation, severity_from_recommendation
from gui.theme import (
    COLOR_CARD_BG,
    COLOR_CRITICAL,
    COLOR_DIVIDER,
    COLOR_OK,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SECTION,
    FONT_TITLE,
    PADDING_LARGE,
    PADDING_MEDIUM,
    PADDING_SMALL,
    ROW_BACKGROUNDS,
)


class DashboardTab(ttk.Frame):
    """Show current farm status, priorities, and recent analyses."""

    def __init__(self, master: tk.Misc, app_controller: Any) -> None:
        """Initialize the dashboard."""
        super().__init__(master, padding=PADDING_MEDIUM)
        self.app = app_controller
        self.metric_labels: dict[str, tk.Label] = {}
        self.plan_labels: dict[str, tk.Label] = {}
        self.latest_labels: dict[str, ttk.Label] = {}
        self._build_layout()

    def _build_layout(self) -> None:
        """Build the dashboard surface."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        self._build_header()
        self._build_metrics()
        self._build_latest_panel()
        self._build_action_plan()
        self._build_recent_table()

    def _build_header(self) -> None:
        header = ttk.Frame(self, padding=(0, 0, 0, PADDING_MEDIUM))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Farmer Dashboard", font=FONT_TITLE, foreground=COLOR_TEXT_PRIMARY).grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            header,
            text="Field status, urgent items, and recent AquaSoil-AI analyses",
            font=FONT_BODY,
            foreground=COLOR_TEXT_MUTED,
        ).grid(row=1, column=0, sticky="w")

        button_row = ttk.Frame(header)
        button_row.grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Button(
            button_row,
            text="Analyze New Sample",
            bootstyle="success",
            command=self.app.show_input,
            padding=(PADDING_MEDIUM, PADDING_SMALL),
        ).grid(row=0, column=0, padx=(0, PADDING_SMALL))
        ttk.Button(
            button_row,
            text="Ask AquaBot",
            bootstyle="primary-outline",
            command=self.app.show_chat,
            padding=(PADDING_MEDIUM, PADDING_SMALL),
        ).grid(row=0, column=1)

    def _build_metrics(self) -> None:
        metrics = ttk.Frame(self)
        metrics.grid(row=1, column=0, sticky="ew", pady=(0, PADDING_MEDIUM))
        for column in range(4):
            metrics.columnconfigure(column, weight=1, uniform="metrics")

        self._add_metric(metrics, 0, "Total Analyses", "0", COLOR_TEXT_PRIMARY)
        self._add_metric(metrics, 1, "Urgent Fields", "0", COLOR_CRITICAL)
        self._add_metric(metrics, 2, "Good Fields", "0", COLOR_OK)
        self._add_metric(metrics, 3, "Latest Crop", "None", COLOR_WARNING)

    def _add_metric(self, parent: ttk.Frame, column: int, title: str, value: str, accent: str) -> None:
        card = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_DIVIDER,
            highlightthickness=1,
            padx=PADDING_MEDIUM,
            pady=PADDING_MEDIUM,
        )
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else PADDING_SMALL, 0))
        tk.Frame(card, bg=accent, height=3).pack(fill="x", pady=(0, PADDING_SMALL))
        tk.Label(card, text=title, font=FONT_BODY_BOLD, fg=COLOR_TEXT_MUTED, bg=COLOR_CARD_BG).pack(anchor="w")
        value_label = tk.Label(card, text=value, font=FONT_SECTION, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        value_label.pack(anchor="w", pady=(PADDING_SMALL, 0))
        self.metric_labels[title] = value_label

    def _build_latest_panel(self) -> None:
        panel = ttk.Frame(self, padding=PADDING_MEDIUM)
        panel.grid(row=2, column=0, sticky="ew", pady=(0, PADDING_MEDIUM))
        panel.columnconfigure(1, weight=1)

        ttk.Label(panel, text="Latest Field Reading", font=FONT_SECTION, foreground=COLOR_TEXT_PRIMARY).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, PADDING_SMALL),
        )

        fields = ("Sample", "Crop", "Timestamp", "Soil", "Water", "Crop Fit", "Main Priority")
        for row, label in enumerate(fields, start=1):
            ttk.Label(panel, text=f"{label}:", font=FONT_BODY_BOLD, foreground=COLOR_TEXT_MUTED).grid(
                row=row,
                column=0,
                sticky="w",
                padx=(0, PADDING_MEDIUM),
                pady=2,
            )
            value_label = ttk.Label(panel, text="--", font=FONT_BODY, foreground=COLOR_TEXT_PRIMARY)
            value_label.grid(row=row, column=1, sticky="w", pady=2)
            self.latest_labels[label] = value_label

    def _build_action_plan(self) -> None:
        section = ttk.Frame(self)
        section.grid(row=3, column=0, sticky="ew", pady=(0, PADDING_MEDIUM))
        section.columnconfigure(0, weight=1)

        ttk.Label(section, text="Today Action Focus", font=FONT_SECTION, foreground=COLOR_TEXT_PRIMARY).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, PADDING_SMALL),
        )

        plan_row = ttk.Frame(section)
        plan_row.grid(row=1, column=0, sticky="ew")
        for column in range(len(ACTION_GROUPS)):
            plan_row.columnconfigure(column, weight=1, uniform="dashboard_plan")

        colors = {"Urgent": COLOR_CRITICAL, "This Week": COLOR_WARNING, "Monitor": COLOR_OK}
        for column, group in enumerate(ACTION_GROUPS):
            card = tk.Frame(
                plan_row,
                bg=COLOR_CARD_BG,
                highlightbackground=colors[group],
                highlightthickness=1,
                padx=PADDING_MEDIUM,
                pady=PADDING_SMALL,
            )
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else PADDING_SMALL, 0))
            tk.Label(card, text=group, font=FONT_BODY_BOLD, fg=colors[group], bg=COLOR_CARD_BG).pack(anchor="w")
            body = tk.Label(
                card,
                text="Run an analysis to create a plan.",
                font=FONT_BODY,
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_CARD_BG,
                justify="left",
                wraplength=250,
            )
            body.pack(anchor="w", fill="x", pady=(PADDING_SMALL, 0))
            self.plan_labels[group] = body

    def _build_recent_table(self) -> None:
        section = ttk.Frame(self)
        section.grid(row=4, column=0, sticky="nsew")
        section.columnconfigure(0, weight=1)
        section.rowconfigure(1, weight=1)

        ttk.Label(section, text="Recent Fields", font=FONT_SECTION, foreground=COLOR_TEXT_PRIMARY).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, PADDING_SMALL),
        )

        columns = ("timestamp", "sample", "crop", "fit", "soil", "water", "priority")
        self.recent_tree = ttk.Treeview(section, columns=columns, show="headings", height=6, bootstyle="primary")
        self.recent_tree.heading("timestamp", text="Timestamp")
        self.recent_tree.heading("sample", text="Sample")
        self.recent_tree.heading("crop", text="Crop")
        self.recent_tree.heading("fit", text="Fit")
        self.recent_tree.heading("soil", text="Soil")
        self.recent_tree.heading("water", text="Water")
        self.recent_tree.heading("priority", text="Priority")
        self.recent_tree.column("timestamp", width=155, anchor="w", stretch=False)
        self.recent_tree.column("sample", width=220, anchor="w")
        self.recent_tree.column("crop", width=105, anchor="center", stretch=False)
        self.recent_tree.column("fit", width=70, anchor="center", stretch=False)
        self.recent_tree.column("soil", width=90, anchor="center", stretch=False)
        self.recent_tree.column("water", width=90, anchor="center", stretch=False)
        self.recent_tree.column("priority", width=120, anchor="center", stretch=False)
        self.recent_tree.grid(row=1, column=0, sticky="nsew")
        self.recent_tree.bind("<<TreeviewSelect>>", self._on_recent_selected)

        scrollbar = ttk.Scrollbar(section, orient="vertical", command=self.recent_tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.recent_tree.configure(yscrollcommand=scrollbar.set)

        self.recent_tree.tag_configure("poor", background=ROW_BACKGROUNDS["poor"])
        self.recent_tree.tag_configure("good", background=ROW_BACKGROUNDS["good"])
        self.recent_tree.tag_configure("mixed", background=ROW_BACKGROUNDS["mixed"])

    def refresh(self, history: list[dict[str, Any]]) -> None:
        """Refresh dashboard values from persisted history."""
        latest = history[0] if history else None
        urgent_count = sum(1 for result in history if self._priority(result) == "Urgent")
        good_count = sum(1 for result in history if self._is_good(result))

        self.metric_labels["Total Analyses"].configure(text=str(len(history)))
        self.metric_labels["Urgent Fields"].configure(text=str(urgent_count))
        self.metric_labels["Good Fields"].configure(text=str(good_count))
        self.metric_labels["Latest Crop"].configure(text=latest.get("crop", "None") if latest else "None")
        self._refresh_latest(latest)
        self._refresh_plan(latest)
        self._refresh_recent(history)

    def _refresh_latest(self, latest: dict[str, Any] | None) -> None:
        if latest is None:
            for label in self.latest_labels.values():
                label.configure(text="--")
            return

        self.latest_labels["Sample"].configure(text=latest.get("sample", "Unknown Field"))
        self.latest_labels["Crop"].configure(text=latest.get("crop", "General Field"))
        self.latest_labels["Timestamp"].configure(text=latest.get("timestamp", ""))
        self.latest_labels["Soil"].configure(text=str(latest.get("soil_class", "")).upper())
        self.latest_labels["Water"].configure(text=str(latest.get("water_class", "")).upper())
        self.latest_labels["Crop Fit"].configure(text=self._crop_fit_text(latest))
        self.latest_labels["Main Priority"].configure(text=self._main_priority_text(latest))

    def _refresh_plan(self, latest: dict[str, Any] | None) -> None:
        plan = build_action_plan(latest)
        for group in ACTION_GROUPS:
            items = plan[group]
            text = "\n".join(f"- {item}" for item in items[:2])
            self.plan_labels[group].configure(text=text)

    def _refresh_recent(self, history: list[dict[str, Any]]) -> None:
        self.recent_tree.delete(*self.recent_tree.get_children())
        for index, result in enumerate(history[:8]):
            self.recent_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    result.get("timestamp", ""),
                    result.get("sample", "Unknown Field"),
                    result.get("crop", "General Field"),
                    self._crop_fit_text(result),
                    str(result.get("soil_class", "")).upper(),
                    str(result.get("water_class", "")).upper(),
                    self._priority(result),
                ),
                tags=(self._row_tag(result),),
            )

    def _on_recent_selected(self, _event: tk.Event) -> None:
        selected = self.recent_tree.selection()
        if selected:
            self.app.load_history_result(int(selected[0]))

    def _main_priority_text(self, result: dict[str, Any]) -> str:
        for recommendation in result.get("recommendations", []):
            severity = severity_from_recommendation(str(recommendation))
            if severity in {"CRITICAL", "WARNING"}:
                return clean_recommendation(str(recommendation))
        return "No urgent issue detected."

    def _crop_fit_text(self, result: dict[str, Any]) -> str:
        crop_advisory = result.get("crop_advisory", {})
        if not isinstance(crop_advisory, dict):
            return "--"
        score = crop_advisory.get("score")
        status = crop_advisory.get("status", "")
        if score is None:
            return "--"
        return f"{float(score):.0f}% {status}"

    def _priority(self, result: dict[str, Any]) -> str:
        severities = {severity_from_recommendation(str(item)) for item in result.get("recommendations", [])}
        if "CRITICAL" in severities:
            return "Urgent"
        if "WARNING" in severities:
            return "Watch"
        return "OK"

    def _is_good(self, result: dict[str, Any]) -> bool:
        return (
            str(result.get("soil_class", "")).upper() == "GOOD"
            and str(result.get("water_class", "")).upper() == "GOOD"
        )

    def _row_tag(self, result: dict[str, Any]) -> str:
        soil = str(result.get("soil_class", "")).upper()
        water = str(result.get("water_class", "")).upper()
        if soil == "POOR" or water == "POOR":
            return "poor"
        if soil == "GOOD" and water == "GOOD":
            return "good"
        return "mixed"
