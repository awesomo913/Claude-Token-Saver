# From: universal_client.py:267
# Release the claimed hwnd when session is removed.

    def release_hwnd(self) -> None:
        """Release the claimed hwnd when session is removed."""
        if self._hwnd:
            self._release_hwnd(self._hwnd)
            self._hwnd = None
        if self._cdp:
            self._cdp.connection.disconnect()
            self._cdp = None
            self._cdp_available = False
        self._configured = False
