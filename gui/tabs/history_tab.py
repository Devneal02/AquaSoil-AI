"""History tab for current-session AquaSoil-AI analyses."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk

from gui.database import export_csv
from gui.farmer_helper import clean_recommendation, severity_from_recommendation
from gui.theme import (
    COLOR_CARD_BG,
    COLOR_CRITICAL,
    COLOR_OK,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SECTION,
    PADDING_LARGE,
    PADDING_MEDIUM,
    PADDING_SMALL,
    ROW_BACKGROUNDS,
)


class HistoryTab(ttk.Frame):
    """Display clickable analyses created during the current session."""

    def __init__(self, master: tk.Misc, app_controller: Any) -> None:
        """Initialize the history tab."""
        super().__init__(master, padding=PADDING_MEDIUM)
        self.app = app_controller
        self.full_history: list[dict[str, Any]] = []
        self.filtered_indices: list[int] = []
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="All")
        self._build_layout()

    def _build_layout(self) -> None:
        """Build the history table and action buttons."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        ttk.Label(self, text="📋 Session History", font=FONT_SECTION, foreground=COLOR_TEXT_PRIMARY).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, PADDING_MEDIUM),
        )

        self._build_filter_row()
        self._build_summary_row()
        self.table_frame = ttk.Frame(self)
        self.table_frame.grid(row=3, column=0, sticky="nsew")
        self.table_frame.columnconfigure(0, weight=1)
        self.table_frame.rowconfigure(0, weight=1)

        columns = ("number", "timestamp", "sample", "soil", "water", "priority", "recs")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", bootstyle="primary")
        self.tree.heading("number", text="#")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("sample", text="Sample Label")
        self.tree.heading("soil", text="Soil")
        self.tree.heading("water", text="Water")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("recs", text="Recs")
        self.tree.column("number", width=48, anchor="center", stretch=False)
        self.tree.column("timestamp", width=160, anchor="w", stretch=False)
        self.tree.column("sample", width=250, anchor="w")
        self.tree.column("soil", width=95, anchor="center", stretch=False)
        self.tree.column("water", width=95, anchor="center", stretch=False)
        self.tree.column("priority", width=95, anchor="center", stretch=False)
        self.tree.column("recs", width=70, anchor="center", stretch=False)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)
        self.tree.bind("<Double-1>", self._open_selected_result)

        self.tree.tag_configure("poor", background=ROW_BACKGROUNDS["poor"])
        self.tree.tag_configure("good", background=ROW_BACKGROUNDS["good"])
        self.tree.tag_configure("mixed", background=ROW_BACKGROUNDS["mixed"])

        self.placeholder = ttk.Label(
            self.table_frame,
            text="No analyses yet",
            font=FONT_BODY_BOLD,
            foreground=COLOR_TEXT_MUTED,
        )
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self._build_detail_panel()
        self._build_button_row()

    def _build_filter_row(self) -> None:
        """Build search and priority filter controls."""
        filters = ttk.Frame(self)
        filters.grid(row=1, column=0, sticky="ew", pady=(0, PADDING_MEDIUM))
        filters.columnconfigure(1, weight=1)

        ttk.Label(filters, text="Search", font=FONT_BODY_BOLD, foreground=COLOR_TEXT_PRIMARY).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, PADDING_SMALL),
        )
        search_entry = ttk.Entry(filters, textvariable=self.search_var, bootstyle="secondary")
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, PADDING_MEDIUM))
        self.search_var.trace_add("write", lambda *_args: self._apply_filters())

        ttk.Label(filters, text="Filter", font=FONT_BODY_BOLD, foreground=COLOR_TEXT_PRIMARY).grid(
            row=0,
            column=2,
            sticky="w",
            padx=(0, PADDING_SMALL),
        )
        self.filter_combo = ttk.Combobox(
            filters,
            textvariable=self.filter_var,
            values=("All", "Urgent", "Watch", "OK", "Good", "Poor"),
            state="readonly",
            width=12,
        )
        self.filter_combo.grid(row=0, column=3, sticky="e")
        self.filter_combo.bind("<<ComboboxSelected>>", lambda _event: self._apply_filters())

    def _build_summary_row(self) -> None:
        """Build compact history summary counters."""
        summary = ttk.Frame(self)
        summary.grid(row=2, column=0, sticky="ew", pady=(0, PADDING_MEDIUM))
        for column in range(4):
            summary.columnconfigure(column, weight=1, uniform="history_summary")

        self.summary_labels: dict[str, tk.Label] = {}
        self._add_summary_card(summary, 0, "Showing", "0 / 0", COLOR_TEXT_PRIMARY)
        self._add_summary_card(summary, 1, "Urgent", "0", COLOR_CRITICAL)
        self._add_summary_card(summary, 2, "Watch", "0", COLOR_WARNING)
        self._add_summary_card(summary, 3, "OK", "0", COLOR_OK)

    def _add_summary_card(self, parent: ttk.Frame, column: int, title: str, value: str, accent: str) -> None:
        card = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=accent,
            highlightthickness=1,
            padx=PADDING_MEDIUM,
            pady=PADDING_SMALL,
        )
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else PADDING_SMALL, 0))
        tk.Label(card, text=title, font=FONT_BODY_BOLD, fg=COLOR_TEXT_MUTED, bg=COLOR_CARD_BG).pack(anchor="w")
        value_label = tk.Label(card, text=value, font=FONT_SECTION, fg=accent, bg=COLOR_CARD_BG)
        value_label.pack(anchor="w")
        self.summary_labels[title] = value_label

    def _build_detail_panel(self) -> None:
        """Build the selected-result preview panel."""
        detail = tk.Frame(
            self,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_TEXT_MUTED,
            highlightthickness=1,
            padx=PADDING_MEDIUM,
            pady=PADDING_MEDIUM,
        )
        detail.grid(row=4, column=0, sticky="ew", pady=(PADDING_MEDIUM, 0))
        detail.columnconfigure(0, weight=1)

        tk.Label(detail, text="Selected Field Preview", font=FONT_BODY_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG).grid(
            row=0,
            column=0,
            sticky="w",
        )
        self.detail_label = tk.Label(
            detail,
            text="Select a history row to preview its main issue and first recommendation.",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
            justify="left",
            anchor="w",
            wraplength=860,
        )
        self.detail_label.grid(row=1, column=0, sticky="ew", pady=(PADDING_SMALL, 0))

    def _build_button_row(self) -> None:
        """Build Clear History and Export History buttons."""
        buttons = ttk.Frame(self)
        buttons.grid(row=5, column=0, sticky="ew", pady=(PADDING_LARGE, 0))
        buttons.columnconfigure(3, weight=1)

        ttk.Button(
            buttons,
            text="🗑️ Clear History",
            bootstyle="danger-outline",
            command=self.clear_history,
            padding=(PADDING_MEDIUM, PADDING_SMALL),
        ).grid(row=0, column=0, padx=(0, PADDING_SMALL))

        ttk.Button(
            buttons,
            text="💾 Export History as CSV",
            bootstyle="primary-outline",
            command=self.export_history,
            padding=(PADDING_MEDIUM, PADDING_SMALL),
        ).grid(row=0, column=1, padx=PADDING_SMALL)

        ttk.Button(
            buttons,
            text="Open Selected Result",
            bootstyle="info-outline",
            command=self._open_selected_result,
            padding=(PADDING_MEDIUM, PADDING_SMALL),
        ).grid(row=0, column=2, padx=PADDING_SMALL)

    def refresh(self, history: list[dict[str, Any]]) -> None:
        """Refresh the table rows from the application history list."""
        self.full_history = list(history)
        self._apply_filters()

    def _apply_filters(self) -> None:
        """Filter history rows and refresh visible state."""
        search_text = self.search_var.get().strip().lower()
        filter_value = self.filter_var.get()
        self.filtered_indices = [
            index
            for index, result in enumerate(self.full_history)
            if self._matches_search(result, search_text) and self._matches_filter(result, filter_value)
        ]
        self._refresh_summary()
        self._refresh_table()
        self._clear_detail()

    def _refresh_table(self) -> None:
        """Refresh the table rows from filtered history indices."""
        self.tree.delete(*self.tree.get_children())
        for visible_index, history_index in enumerate(self.filtered_indices, start=1):
            result = self.full_history[history_index]
            rec_count = len(result.get("recommendations", []))
            tag = self._row_tag(result)
            self.tree.insert(
                "",
                "end",
                iid=str(history_index),
                values=(
                    visible_index,
                    result.get("timestamp", ""),
                    result.get("sample", "Unknown Field"),
                    str(result.get("soil_class", "")).upper(),
                    str(result.get("water_class", "")).upper(),
                    self._priority(result),
                    rec_count,
                ),
                tags=(tag,),
            )

        if self.filtered_indices:
            self.placeholder.place_forget()
        else:
            self.placeholder.configure(text="No matching analyses" if self.full_history else "No analyses yet")
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")

    def _refresh_summary(self) -> None:
        """Refresh summary cards for all saved history plus current filter size."""
        urgent = sum(1 for result in self.full_history if self._priority(result) == "Urgent")
        watch = sum(1 for result in self.full_history if self._priority(result) == "Watch")
        ok = sum(1 for result in self.full_history if self._priority(result) == "OK")
        self.summary_labels["Showing"].configure(text=f"{len(self.filtered_indices)} / {len(self.full_history)}")
        self.summary_labels["Urgent"].configure(text=str(urgent))
        self.summary_labels["Watch"].configure(text=str(watch))
        self.summary_labels["OK"].configure(text=str(ok))

    def clear_history(self) -> None:
        """Ask for confirmation and clear the current session history."""
        if not self.app.history:
            messagebox.showinfo("History empty", "There are no analyses to clear.", parent=self.winfo_toplevel())
            return
        confirmed = messagebox.askyesno(
            "Clear history",
            "Clear all saved analyses from history?",
            parent=self.winfo_toplevel(),
        )
        if confirmed:
            self.app.clear_history()

    def export_history(self) -> None:
        """Export persistent history as a CSV file."""
        if not self.app.history:
            messagebox.showinfo("History empty", "There are no analyses to export.", parent=self.winfo_toplevel())
            return

        path = filedialog.asksaveasfilename(
            title="Export AquaSoil-AI History",
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            parent=self.winfo_toplevel(),
        )
        if not path:
            return

        export_csv(Path(path))
        messagebox.showinfo("History exported", "The saved history was exported.", parent=self.winfo_toplevel())

    def _on_row_selected(self, _event: tk.Event) -> None:
        """Preview the selected history row."""
        index = self._selected_history_index()
        if index is None:
            self._clear_detail()
            return
        self._show_detail(self.app.history[index])

    def _open_selected_result(self, _event: tk.Event | None = None) -> None:
        """Open the selected history result in the Results tab."""
        index = self._selected_history_index()
        if index is None:
            messagebox.showinfo("No row selected", "Select a history row first.", parent=self.winfo_toplevel())
            return
        self.app.load_history_result(index)

    def _selected_history_index(self) -> int | None:
        selected = self.tree.selection()
        if not selected:
            return None
        return int(selected[0])

    def _show_detail(self, result: dict[str, Any]) -> None:
        """Show a compact preview for the selected history row."""
        recommendations = [str(item) for item in result.get("recommendations", [])]
        first_recommendation = clean_recommendation(recommendations[0]) if recommendations else "No recommendation."
        text = (
            f"{result.get('sample', 'Unknown Field')} | "
            f"Soil: {str(result.get('soil_class', '')).upper()} | "
            f"Water: {str(result.get('water_class', '')).upper()} | "
            f"Priority: {self._priority(result)}\n"
            f"{first_recommendation}"
        )
        self.detail_label.configure(text=text)

    def _clear_detail(self) -> None:
        self.detail_label.configure(text="Select a history row to preview its main issue and first recommendation.")

    def _matches_search(self, result: dict[str, Any], search_text: str) -> bool:
        if not search_text:
            return True
        haystack = " ".join(
            [
                str(result.get("timestamp", "")),
                str(result.get("sample", "")),
                str(result.get("soil_class", "")),
                str(result.get("water_class", "")),
                " ".join(str(item) for item in result.get("recommendations", [])),
            ]
        ).lower()
        return search_text in haystack

    def _matches_filter(self, result: dict[str, Any], filter_value: str) -> bool:
        if filter_value == "All":
            return True
        if filter_value in {"Urgent", "Watch", "OK"}:
            return self._priority(result) == filter_value
        soil = str(result.get("soil_class", "")).upper()
        water = str(result.get("water_class", "")).upper()
        if filter_value == "Good":
            return soil == "GOOD" and water == "GOOD"
        if filter_value == "Poor":
            return soil == "POOR" or water == "POOR"
        return True

    def _priority(self, result: dict[str, Any]) -> str:
        severities = {severity_from_recommendation(str(item)) for item in result.get("recommendations", [])}
        if "CRITICAL" in severities:
            return "Urgent"
        if "WARNING" in severities:
            return "Watch"
        return "OK"

    def _row_tag(self, result: dict[str, Any]) -> str:
        """Return the row color tag based on soil and water classes."""
        soil = str(result.get("soil_class", "")).upper()
        water = str(result.get("water_class", "")).upper()
        if soil == "POOR" or water == "POOR":
            return "poor"
        if soil == "GOOD" and water == "GOOD":
            return "good"
        return "mixed"
