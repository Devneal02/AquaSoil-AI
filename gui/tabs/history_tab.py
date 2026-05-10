"""History tab for current-session AquaSoil-AI analyses."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk

from gui.database import export_csv
from gui.theme import (
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
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
        self._build_layout()

    def _build_layout(self) -> None:
        """Build the history table and action buttons."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="📋 Session History", font=FONT_SECTION, foreground=COLOR_TEXT_PRIMARY).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, PADDING_MEDIUM),
        )

        self.table_frame = ttk.Frame(self)
        self.table_frame.grid(row=1, column=0, sticky="nsew")
        self.table_frame.columnconfigure(0, weight=1)
        self.table_frame.rowconfigure(0, weight=1)

        columns = ("number", "timestamp", "sample", "soil", "water", "recs")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", bootstyle="primary")
        self.tree.heading("number", text="#")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("sample", text="Sample Label")
        self.tree.heading("soil", text="Soil")
        self.tree.heading("water", text="Water")
        self.tree.heading("recs", text="Recs")
        self.tree.column("number", width=48, anchor="center", stretch=False)
        self.tree.column("timestamp", width=160, anchor="w", stretch=False)
        self.tree.column("sample", width=310, anchor="w")
        self.tree.column("soil", width=95, anchor="center", stretch=False)
        self.tree.column("water", width=95, anchor="center", stretch=False)
        self.tree.column("recs", width=70, anchor="center", stretch=False)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)

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

        self._build_button_row()

    def _build_button_row(self) -> None:
        """Build Clear History and Export History buttons."""
        buttons = ttk.Frame(self)
        buttons.grid(row=2, column=0, sticky="ew", pady=(PADDING_LARGE, 0))
        buttons.columnconfigure(2, weight=1)

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

    def refresh(self, history: list[dict[str, Any]]) -> None:
        """Refresh the table rows from the application history list."""
        self.tree.delete(*self.tree.get_children())
        for index, result in enumerate(history, start=1):
            rec_count = len(result.get("recommendations", []))
            tag = self._row_tag(result)
            self.tree.insert(
                "",
                "end",
                iid=str(index - 1),
                values=(
                    index,
                    result.get("timestamp", ""),
                    result.get("sample", "Unknown Field"),
                    str(result.get("soil_class", "")).upper(),
                    str(result.get("water_class", "")).upper(),
                    rec_count,
                ),
                tags=(tag,),
            )

        if history:
            self.placeholder.place_forget()
        else:
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")

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
        """Reload clicked history results into the Results tab."""
        selected = self.tree.selection()
        if not selected:
            return
        index = int(selected[0])
        self.app.load_history_result(index)

    def _row_tag(self, result: dict[str, Any]) -> str:
        """Return the row color tag based on soil and water classes."""
        soil = str(result.get("soil_class", "")).upper()
        water = str(result.get("water_class", "")).upper()
        if soil == "POOR" or water == "POOR":
            return "poor"
        if soil == "GOOD" and water == "GOOD":
            return "good"
        return "mixed"
