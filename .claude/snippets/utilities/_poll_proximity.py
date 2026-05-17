# From: claude_backend/overlay.py:247
# Tick: restore alpha when cursor near, fade out after idle.

    def _poll_proximity(self) -> None:
        """Tick: restore alpha when cursor near, fade out after idle.
        Also tracks the foreground HWND so a subsequent click can
        restore focus to the right window before firing Ctrl+A+Ctrl+C.
        """
        now_ms = int(time.time() * 1000)
        if self._cursor_near():
            self._last_proximity_ms = now_ms
            self._set_alpha(_FADE_ACTIVE_ALPHA)
        elif now_ms - self._last_proximity_ms >= _FADE_DELAY_MS:
            self._set_alpha(_FADE_IDLE_ALPHA)

        # Track foreground HWND. Skip our own root + any picker we
        # might own so we don't save the overlay/picker as the
        # "external" window the user was typing in.
        if _WIN32_OK:
            try:
                fg = int(_user32.GetForegroundWindow())
                # GA_ROOT = 2; resolve our Toplevel root because
                # winfo_id() returns the inner Tk drawable handle.
                my_root = int(_user32.GetAncestor(int(self.winfo_id()), 2))
                if fg and fg != my_root:
                    self._last_external_hwnd = fg
            except Exception as e:
                # Log but keep the poll alive — repeated user32
                # failures point to a broken environment (DLL unloaded
                # at session shutdown, etc.). Stale _last_external_hwnd
                # would otherwise silently misroute Ctrl+A+Ctrl+C.
                logger.debug("Foreground-HWND poll failed: %s", e)

        # Always reschedule — cancellation happens on widget destroy
        # via Tk's own cleanup of pending after() callbacks.
        try:
            self._fade_job = self.after(
                _FOREGROUND_POLL_MS, self._poll_proximity,
            )
        except tk.TclError:
            self._fade_job = None
