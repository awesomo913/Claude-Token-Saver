# From: claude_backend/gui.py:2849
# Main toggle: persist pref, install/uninstall BOTH hooks (SessionStart

    def _al_toggle_main(self) -> None:
        """Main toggle: persist pref, install/uninstall BOTH hooks (SessionStart
        + UserPromptSubmit) so existing AND new sessions pick up auto-launch.
        """
        on = bool(self._set_auto_launch.get())
        self._prefs.auto_launch_gui_on_session = on
        if not self._prefs.save():
            self._toast("Failed to save preference", "warning")
            return
        try:
            from . import auto_inject
            if on:
                ok1, msg1 = auto_inject.install_launcher_hook()
                ok2, msg2 = auto_inject.install_prompt_hook()
            else:
                ok1, msg1 = auto_inject.uninstall_launcher_hook()
                ok2, msg2 = auto_inject.uninstall_prompt_hook()
        except Exception as e:
            self._toast(f"Module error: {e}", "error")
            self._al_refresh_status()
            return
        # On uninstall, "not found" is fine (idempotent) — treat as success.
        if not on:
            ok1 = ok1 or "not found" in msg1.lower()
            ok2 = ok2 or "not found" in msg2.lower()
        if ok1 and ok2:
            self._toast(f"Auto-launch: {'ON' if on else 'OFF'}",
                        "success" if on else "info")
            self._log(f"SessionStart hook: {msg1}")
            self._log(f"UserPromptSubmit hook: {msg2}")
        else:
            self._toast(f"Partial update — SessionStart: {msg1}; Prompt: {msg2}",
                        "warning")
        self._al_refresh_status()
