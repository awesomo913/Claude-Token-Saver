# From: claude_backend/gui.py:2893
# Manual install button — installs BOTH SessionStart + UserPromptSubmit.

    def _al_install(self) -> None:
        """Manual install button — installs BOTH SessionStart + UserPromptSubmit."""
        try:
            from . import auto_inject
            ok1, msg1 = auto_inject.install_launcher_hook()
            ok2, msg2 = auto_inject.install_prompt_hook()
        except Exception as e:
            self._toast(f"Module error: {e}", "error")
            return
        if ok1 and ok2:
            self._toast("Launcher hooks installed", "success")
            self._log(f"SessionStart: {msg1}")
            self._log(f"UserPromptSubmit: {msg2}")
            if not self._prefs.auto_launch_gui_on_session:
                self._prefs.auto_launch_gui_on_session = True
                self._prefs.save()
                self._set_auto_launch.select()
        else:
            self._toast(f"Install partial: SS={msg1}; UPS={msg2}", "error")
        self._al_refresh_status()
