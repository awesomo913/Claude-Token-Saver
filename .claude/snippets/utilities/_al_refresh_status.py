# From: claude_backend/gui.py:2801
# Update auto-launch card status indicator + button states.

    def _al_refresh_status(self) -> None:
        """Update auto-launch card status indicator + button states.

        Reports combined state of BOTH SessionStart and UserPromptSubmit
        launcher hooks.
        """
        try:
            from . import auto_inject
            ss = auto_inject.check_launcher_status()
            ups = auto_inject.check_prompt_status()
        except Exception as e:
            self._al_status_lbl.configure(text=f"Module error: {e}",
                                          text_color=C["err"])
            return
        if not ss["settings_exists"]:
            self._al_status_lbl.configure(text="settings.json missing",
                                          text_color=C["err"])
            self._al_install_btn.configure(state="disabled")
            self._al_uninstall_btn.configure(state="disabled")
        elif not ss["settings_valid"]:
            self._al_status_lbl.configure(text="settings.json INVALID",
                                          text_color=C["err"])
            self._al_install_btn.configure(state="disabled")
            self._al_uninstall_btn.configure(state="disabled")
        elif ss["installed"] and ups["installed"]:
            self._al_status_lbl.configure(text="Hooks INSTALLED (new + existing sessions)",
                                          text_color=C["ok"])
            self._al_install_btn.configure(state="disabled")
            self._al_uninstall_btn.configure(state="normal")
        elif ss["installed"] or ups["installed"]:
            partial = "SessionStart only" if ss["installed"] else "UserPromptSubmit only"
            self._al_status_lbl.configure(text=f"PARTIAL ({partial})",
                                          text_color=C["warn"])
            self._al_install_btn.configure(state="normal")
            self._al_uninstall_btn.configure(state="normal")
        else:
            self._al_status_lbl.configure(text="Hooks not installed",
                                          text_color=C["fg3"])
            self._al_install_btn.configure(state="normal")
            self._al_uninstall_btn.configure(state="disabled")
        # Sub-toggle only meaningful when main toggle is on.
        if self._prefs.auto_launch_gui_on_session:
            self._set_auto_launch_min.configure(state="normal")
        else:
            self._set_auto_launch_min.configure(state="disabled")
        # Repair-shortcut card too.
        self._refresh_autostart_status()
