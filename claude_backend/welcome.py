"""First-run welcome dialog — explains what Token Saver does, permissions, workflow.

Shown on every GUI launch until user disables it. Acts as the onboarding
guide. Accessible at any time via Help button in sidebar or Settings tab.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

import customtkinter as ctk

from .auto_inject import check_status, install as ai_install
from .prefs import Prefs

logger = logging.getLogger(__name__)

# Theme — keep in sync with gui.py C dict
_C = {
    "bg": "#1a1a1a", "bg2": "#2d2d2d", "card": "#212121", "input": "#1e1e1e",
    "fg": "#ffffff", "fg2": "#b0b0b0", "fg3": "#808080",
    "border": "#404040", "accent": "#0078d4", "ok": "#107c10",
    "warn": "#ff8c00", "err": "#e81123", "purple": "#8e44ad",
}
_F = "Segoe UI"
_M = "Consolas"


WELCOME_TITLE = "Welcome to Claude Token Saver"

WELCOME_INTRO = (
    "This tool reduces token spend in Claude Code by pre-staging your project "
    "context and giving you a quick way to attach targeted code snippets to any prompt."
)

WHAT_IT_DOES = [
    ("Layer 1 — Auto context",
     "Generates CLAUDE.md and memory files Claude Code auto-loads at session start. "
     "Saves ~5x on every session, no manual work."),
    ("Layer 2 — Targeted snippets",
     "Browse, fuzzy-search, and copy specific code blocks from your project to paste "
     "before any Claude Code prompt. Saves 10-40x on per-query context."),
    ("Local AI search assist (optional)",
     "Connects to Ollama on localhost:11434 if installed, to handle typos and sloppy "
     "search queries. Fully local — no data leaves your machine."),
]

PERMISSIONS = [
    ("Reads/writes files in YOUR project folder",
     "Generates CLAUDE.md, .claude/snippets/*, and reads source files to scan."),
    ("Reads/writes ~/.claude/settings.json",
     "Only when you click Install Auto-Inject or toggle 'Auto-launch on session'. "
     "Each install is a separate hook entry, removable independently. Always "
     "backed up first with timestamp; only the newest 3 backups are kept."),
    ("Reads/writes ~/.claude/projects/<slug>/memory/",
     "Memory files Claude Code auto-loads per project. Standard Claude Code path."),
    ("Reads/writes ~/.claude/token_saver_prefs.json",
     "Stores your GUI preferences (welcome toggle, auto-launch toggle, etc)."),
    ("Reads/writes ~/.claude/token_saver_tray.pid",
     "Single-instance lock file for the tray icon. Prevents duplicate icons."),
    ("Reads/writes ~/.claude/token_saver_crash.log",
     "Created only if the exe crashes — records traceback for diagnosis. "
     "Otherwise this file does not exist."),
    ("Network: localhost:11434 only (Ollama)",
     "Optional. Skipped if Ollama not running. Never connects to anything else "
     "unless you click Pull Model or use the GitHub scanner."),
    ("No telemetry, no cloud, no account",
     "Token Saver runs 100% locally. Nothing is ever uploaded."),
]

QUICK_START = [
    "1. Click Dashboard, browse to your project folder, hit Bootstrap.",
    "2. Tool scans your code, generates CLAUDE.md and memory files.",
    "3. Settings tab → click Install Auto-Inject (one-time, takes 1 second).",
    "4. From now on, every Claude Code session auto-refreshes context.",
    "5. (Optional) Settings tab → 'Auto-launch on Claude Code session' toggle. "
    "When ON, every Claude Code session opens Token Saver so you're reminded "
    "to grab targeted snippets. Installs TWO hooks: SessionStart (new sessions) "
    "and UserPromptSubmit (existing sessions on next prompt). Both idempotent.",
    "6. For specific questions, open Context Builder, search snippets, click Grab, "
    "Copy, paste before your Claude Code prompt.",
]

PRO_TIP = (
    "Keep the tray icon running (right-click tray → Open GUI). "
    "Whenever you switch focus to Claude Code, glance at the tray as a reminder "
    "to grab snippets first. That's where the 10-40x savings actually come from."
)


class WelcomeDialog(ctk.CTkToplevel):
    """Modal welcome window. Closes on dismiss; updates prefs."""

    def __init__(self, parent: ctk.CTk, prefs: Prefs,
                 on_install_callback: Optional[Callable[[], None]] = None) -> None:
        super().__init__(parent)
        self._prefs = prefs
        self._on_install = on_install_callback

        self.title(WELCOME_TITLE)
        self.geometry("780x680")
        self.minsize(680, 560)
        self.configure(fg_color=_C["bg"])
        self.transient(parent)

        # Center on parent
        self.after(50, self._center_on_parent)

        self._build()
        self._refresh_status()

        # Bump seen count immediately
        self._prefs.welcome_seen_count += 1
        self._prefs.save()

    def _center_on_parent(self) -> None:
        self.update_idletasks()
        try:
            px = self.master.winfo_x()
            py = self.master.winfo_y()
            pw = self.master.winfo_width()
            ph = self.master.winfo_height()
            w = self.winfo_width()
            h = self.winfo_height()
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception as e:
            logger.debug("center failed: %s", e)

    def _build(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color=_C["bg"])
        scroll.pack(fill="both", expand=True, padx=18, pady=(18, 0))

        # Header
        ctk.CTkLabel(scroll, text=WELCOME_TITLE, font=(_F, 22, "bold"),
                     text_color=_C["accent"]).pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(scroll, text=WELCOME_INTRO, font=(_F, 12),
                     text_color=_C["fg2"], wraplength=720, justify="left"
                     ).pack(anchor="w", pady=(0, 16))

        # Status card — Auto-Inject install state with quick action
        self._status_card = ctk.CTkFrame(scroll, fg_color=_C["card"], corner_radius=8,
                                         border_width=2, border_color=_C["ok"])
        self._status_card.pack(fill="x", pady=(0, 16))
        self._status_label = ctk.CTkLabel(
            self._status_card, text="Checking Auto-Inject...",
            font=(_F, 13, "bold"), text_color=_C["fg"],
        )
        self._status_label.pack(anchor="w", padx=14, pady=(12, 4))
        self._status_detail = ctk.CTkLabel(
            self._status_card, text="", font=(_F, 11),
            text_color=_C["fg2"], wraplength=700, justify="left",
        )
        self._status_detail.pack(anchor="w", padx=14, pady=(0, 8))
        self._status_btn = ctk.CTkButton(
            self._status_card, text="Install Auto-Inject", width=180, height=32,
            font=(_F, 12, "bold"), fg_color=_C["ok"],
            command=self._do_install,
        )
        self._status_btn.pack(anchor="w", padx=14, pady=(0, 12))

        # What it does
        self._section(scroll, "What it does")
        for title, body in WHAT_IT_DOES:
            self._bullet(scroll, title, body)

        # Permissions
        self._section(scroll, "Permissions used")
        ctk.CTkLabel(scroll,
                     text="Full transparency on what this tool reads and writes:",
                     font=(_F, 11), text_color=_C["fg3"], wraplength=720, justify="left",
                     ).pack(anchor="w", pady=(0, 8))
        for title, body in PERMISSIONS:
            self._bullet(scroll, title, body)

        # Quick start
        self._section(scroll, "Quick start")
        for step in QUICK_START:
            ctk.CTkLabel(scroll, text=step, font=(_F, 11),
                         text_color=_C["fg2"], wraplength=720, justify="left",
                         ).pack(anchor="w", padx=14, pady=2)

        # Pro tip
        tip_card = ctk.CTkFrame(scroll, fg_color=_C["card"], corner_radius=8,
                                border_width=1, border_color=_C["purple"])
        tip_card.pack(fill="x", pady=(16, 8))
        ctk.CTkLabel(tip_card, text="Pro tip", font=(_F, 12, "bold"),
                     text_color=_C["purple"]).pack(anchor="w", padx=14, pady=(10, 2))
        ctk.CTkLabel(tip_card, text=PRO_TIP, font=(_F, 11),
                     text_color=_C["fg2"], wraplength=700, justify="left",
                     ).pack(anchor="w", padx=14, pady=(0, 12))

        # Footer — fixed below scroll area
        footer = ctk.CTkFrame(self, fg_color=_C["bg2"], corner_radius=0, height=64)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        self._dont_show = ctk.CTkCheckBox(
            footer, text="Don't show this on launch (always available via Help button)",
            font=(_F, 11), text_color=_C["fg2"],
            command=self._toggle_dont_show,
        )
        self._dont_show.pack(side="left", padx=18, pady=18)
        if not self._prefs.show_welcome_on_launch:
            self._dont_show.select()

        ctk.CTkButton(
            footer, text="Got it — close", width=140, height=32,
            font=(_F, 12, "bold"), fg_color=_C["accent"],
            command=self._dismiss,
        ).pack(side="right", padx=18, pady=16)

    def _section(self, parent, title: str) -> None:
        ctk.CTkLabel(parent, text=title, font=(_F, 15, "bold"),
                     text_color=_C["fg"]).pack(anchor="w", pady=(12, 6))

    def _bullet(self, parent, title: str, body: str) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=f"• {title}", font=(_F, 12, "bold"),
                     text_color=_C["fg"]).pack(anchor="w", padx=8)
        ctk.CTkLabel(row, text=f"    {body}", font=(_F, 11),
                     text_color=_C["fg2"], wraplength=700, justify="left",
                     ).pack(anchor="w", padx=8, pady=(0, 4))

    def _refresh_status(self) -> None:
        """Update the status card based on Auto-Inject state."""
        s = check_status()
        if s["installed"]:
            self._status_label.configure(
                text="Auto-Inject is INSTALLED", text_color=_C["ok"],
            )
            self._status_detail.configure(
                text="Every Claude Code session auto-refreshes your project context. "
                     "You're all set on Layer 1 — the silent compression."
            )
            self._status_btn.configure(
                text="Already installed", state="disabled",
                fg_color=_C["bg2"], text_color=_C["fg3"],
            )
            self._status_card.configure(border_color=_C["ok"])
        elif not s["settings_valid"]:
            self._status_label.configure(
                text="settings.json invalid — needs manual fix",
                text_color=_C["err"],
            )
            self._status_detail.configure(text=s.get("error", "Unknown error"))
            self._status_btn.configure(
                text="Cannot install", state="disabled",
                fg_color=_C["bg2"], text_color=_C["fg3"],
            )
            self._status_card.configure(border_color=_C["err"])
        else:
            self._status_label.configure(
                text="Auto-Inject is NOT installed", text_color=_C["warn"],
            )
            self._status_detail.configure(
                text="Click Install to enable session-start context refresh. "
                     "Backs up your settings.json first. Reversible anytime."
            )
            self._status_btn.configure(
                text="Install Auto-Inject", state="normal",
                fg_color=_C["ok"], text_color="#ffffff",
            )
            self._status_card.configure(border_color=_C["warn"])

    def _do_install(self) -> None:
        """One-click install button inside welcome."""
        ok, msg = ai_install()
        if ok:
            self._refresh_status()
            if self._on_install:
                try:
                    self._on_install()
                except Exception as e:
                    logger.debug("install callback failed: %s", e)
        else:
            self._status_detail.configure(text=f"Install failed: {msg}",
                                          text_color=_C["err"])

    def _toggle_dont_show(self) -> None:
        # Checkbox checked => suppress on launch
        suppress = bool(self._dont_show.get())
        self._prefs.show_welcome_on_launch = not suppress
        self._prefs.save()

    def _dismiss(self) -> None:
        self.destroy()


def show_welcome(parent: ctk.CTk, prefs: Prefs,
                 on_install_callback: Optional[Callable[[], None]] = None) -> WelcomeDialog:
    """Open welcome window. Returns dialog instance (caller can grab focus etc)."""
    dlg = WelcomeDialog(parent, prefs, on_install_callback=on_install_callback)
    dlg.lift()
    dlg.focus_force()
    return dlg
