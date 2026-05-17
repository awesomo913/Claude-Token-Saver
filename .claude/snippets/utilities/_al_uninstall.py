# From: claude_backend/gui.py:2914
# Manual uninstall button — removes BOTH hooks.

    def _al_uninstall(self) -> None:
        """Manual uninstall button — removes BOTH hooks."""
        try:
            from . import auto_inject
            ok1, msg1 = auto_inject.uninstall_launcher_hook()
            ok2, msg2 = auto_inject.uninstall_prompt_hook()
        except Exception as e:
            self._toast(f"Module error: {e}", "error")
            return
        # "not found" is fine on uninstall.
        ok1 = ok1 or "not found" in msg1.lower()
        ok2 = ok2 or "not found" in msg2.lower()
        if ok1 and ok2:
            self._toast("Launcher hooks removed", "info")
            self._log(f"SessionStart: {msg1}")
            self._log(f"UserPromptSubmit: {msg2}")
            if self._prefs.auto_launch_gui_on_session:
                self._prefs.auto_launch_gui_on_session = False
                self._prefs.save()
                self._set_auto_launch.deselect()
        else:
            self._toast(f"Uninstall partial: SS={msg1}; UPS={msg2}", "warning")
        self._al_refresh_status()
