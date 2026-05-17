# From: universal_client.py:235
# Directly assign a window handle (from capture mode).

    def configure_with_hwnd(self, hwnd: int) -> bool:
        """Directly assign a window handle (from capture mode).

        Also tries to find a matching CDP target for this window.
        """
        import ctypes
        if not ctypes.windll.user32.IsWindow(hwnd):
            return False

        # Reject if another session already claimed this hwnd
        with self._claimed_lock:
            if hwnd in self._claimed_hwnds and hwnd != self._hwnd:
                logger.warning("hwnd=%d already claimed by another session", hwnd)
                return False

        # Release old hwnd if any
        if self._hwnd:
            self._release_hwnd(self._hwnd)

        self._hwnd = hwnd
        with self._claimed_lock:
            self._claimed_hwnds.add(hwnd)
        position_existing_window(hwnd, self._corner)
        self._configured = True

        # Try CDP connection for this window
        self._try_configure_cdp()

        logger.info("Captured window hwnd=%d for %s at %s (cdp=%s)",
                     hwnd, self._profile.name, self._corner, self._cdp_available)
        return True
