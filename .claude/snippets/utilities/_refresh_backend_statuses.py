# From: claude_backend/gui.py:3085
# Kick off authoritative probes off the Tk main thread.

    def _refresh_backend_statuses(self) -> None:
        """Kick off authoritative probes off the Tk main thread.

        Uses HTTP /health for backend and psutil cmdline scan for
        overlay (avoids Windows SO_REUSEADDR false-positives and
        cross-process pidfile races). Runs in a daemon thread so the
        worst-case 0.4s probe timeout cannot freeze the UI; results
        are posted back via `after(0, ...)`.

        Hotkey label is updated synchronously here because it only
        reads prefs (no I/O).
        """
        # Hotkey is in-process; trust pref (no probe).
        if hasattr(self, "_hk_status_lbl"):
            if self._prefs.enable_hotkey:
                self._hk_status_lbl.configure(
                    text=f"Bound: {self._prefs.hotkey_combo}",
                    text_color=C["ok"],
                )
            else:
                self._hk_status_lbl.configure(
                    text="Disabled", text_color=C["fg3"],
                )

        if not (hasattr(self, "_bk_status_lbl")
                or hasattr(self, "_ov_status_lbl")):
            return

        port = self._prefs.http_port
        show_overlay = self._prefs.show_overlay

        def _probe() -> None:
            try:
                from .http_server import is_backend_alive
                from .single_instance import (is_locked,
                                              is_process_alive_by_cmdline)
                backend_up = is_backend_alive(port)
                overlay_up = (is_locked("ClaudeTokenSaverOverlay")
                              or is_process_alive_by_cmdline("--overlay"))
                self.after(0, self._apply_backend_status,
                           backend_up, overlay_up, port, show_overlay, None)
            except Exception as e:
                self.after(0, self._apply_backend_status,
                           False, False, port, show_overlay, str(e))

        threading.Thread(target=_probe, daemon=True,
                         name="ts_status_probe").start()
