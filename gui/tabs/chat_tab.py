"""Offline AquaBot helper tab for farmer-facing guidance."""

from __future__ import annotations

from typing import Any

import tkinter as tk

import ttkbootstrap as ttk

from gui.farmer_helper import generate_chat_response
from gui.theme import (
    COLOR_CARD_BG,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SECTION,
    PADDING_LARGE,
    PADDING_MEDIUM,
    PADDING_SMALL,
)


class ChatTab(ttk.Frame):
    """A lightweight offline assistant for app and field-result questions."""

    def __init__(self, master: tk.Misc, app_controller: Any) -> None:
        """Initialize the chatbot tab."""
        super().__init__(master, padding=PADDING_MEDIUM)
        self.app = app_controller
        self.question_var = tk.StringVar()
        self._build_layout()
        self._add_message(
            "AquaBot",
            "Hello. I can explain the latest result, suggest what to do first, and help with app steps.",
            "bot",
        )

    def _build_layout(self) -> None:
        """Build the assistant header, conversation, quick prompts, and input row."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(0, 0, 0, PADDING_MEDIUM))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="AquaBot Helper", font=FONT_SECTION, foreground=COLOR_TEXT_PRIMARY).grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            header,
            text="Offline farmer assistant",
            font=FONT_BODY,
            foreground=COLOR_TEXT_MUTED,
        ).grid(row=1, column=0, sticky="w")

        chat_shell = tk.Frame(self, bg=COLOR_CARD_BG, padx=PADDING_SMALL, pady=PADDING_SMALL)
        chat_shell.grid(row=1, column=0, sticky="nsew", pady=(0, PADDING_MEDIUM))
        chat_shell.columnconfigure(0, weight=1)
        chat_shell.rowconfigure(0, weight=1)

        self.chat_text = tk.Text(
            chat_shell,
            wrap="word",
            bg=COLOR_CARD_BG,
            fg=COLOR_TEXT_PRIMARY,
            font=FONT_BODY,
            relief="flat",
            padx=PADDING_MEDIUM,
            pady=PADDING_MEDIUM,
            state="disabled",
            height=18,
        )
        self.chat_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(chat_shell, orient="vertical", command=self.chat_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        self._configure_chat_tags()

        self._build_quick_prompts()
        self._build_input_row()

    def _configure_chat_tags(self) -> None:
        """Configure chat text styles."""
        self.chat_text.tag_configure("user_name", foreground=COLOR_PRIMARY, font=FONT_BODY_BOLD)
        self.chat_text.tag_configure("bot_name", foreground=COLOR_TEXT_PRIMARY, font=FONT_BODY_BOLD)
        self.chat_text.tag_configure("user", lmargin1=12, lmargin2=12, spacing3=8)
        self.chat_text.tag_configure("bot", lmargin1=12, lmargin2=12, spacing3=10)

    def _build_quick_prompts(self) -> None:
        """Build shortcut buttons for common farmer questions."""
        prompt_row = ttk.Frame(self)
        prompt_row.grid(row=2, column=0, sticky="ew", pady=(0, PADDING_MEDIUM))
        prompt_row.columnconfigure(5, weight=1)

        prompts = [
            "Explain latest result",
            "Explain crop suitability",
            "What should I do first?",
            "How do I use CSV?",
            "Explain pH",
        ]
        for index, prompt in enumerate(prompts):
            ttk.Button(
                prompt_row,
                text=prompt,
                bootstyle="secondary-outline",
                command=lambda value=prompt: self.send_question(value),
                padding=(PADDING_SMALL, PADDING_SMALL),
            ).grid(row=0, column=index, padx=(0, PADDING_SMALL), sticky="w")

    def _build_input_row(self) -> None:
        """Build the typed question field and send button."""
        input_row = ttk.Frame(self)
        input_row.grid(row=3, column=0, sticky="ew")
        input_row.columnconfigure(0, weight=1)

        self.question_entry = ttk.Entry(input_row, textvariable=self.question_var, bootstyle="secondary")
        self.question_entry.grid(row=0, column=0, sticky="ew", padx=(0, PADDING_SMALL))
        self.question_entry.bind("<Return>", self._handle_enter_key)

        ttk.Button(
            input_row,
            text="Send",
            bootstyle="primary",
            command=self.send_question,
            padding=(PADDING_LARGE, PADDING_SMALL),
        ).grid(row=0, column=1)

    def _handle_enter_key(self, _event: tk.Event) -> str:
        """Send the question when Enter is pressed."""
        self.send_question()
        return "break"

    def send_question(self, question: str | None = None) -> None:
        """Append a question and generated AquaBot response to the conversation."""
        text = question if question is not None else self.question_var.get()
        text = text.strip()
        if not text:
            self.question_entry.focus_set()
            return

        self.question_var.set("")
        self._add_message("You", text, "user")
        latest_result = self.app.get_latest_result()
        response = generate_chat_response(text, latest_result=latest_result, history=self.app.history)
        self._add_message("AquaBot", response, "bot")
        self.question_entry.focus_set()

    def refresh_context(self) -> None:
        """Let the user know a new analysis can be discussed."""
        latest_result = self.app.get_latest_result()
        if latest_result:
            sample = latest_result.get("sample", "latest sample")
            self._add_message("AquaBot", f"New result loaded for {sample}. Ask me what to do first.", "bot")

    def _add_message(self, sender: str, message: str, tag: str) -> None:
        """Append one formatted chat message."""
        name_tag = "user_name" if tag == "user" else "bot_name"
        self.chat_text.configure(state="normal")
        if self.chat_text.index("end-1c") != "1.0":
            self.chat_text.insert("end", "\n")
        self.chat_text.insert("end", f"{sender}\n", name_tag)
        self.chat_text.insert("end", f"{message}\n", tag)
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")
