# From: claude_backend/welcome.py:251
# Update the status card based on Auto-Inject state.

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
