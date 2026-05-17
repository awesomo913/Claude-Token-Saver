# From: universal_client.py:150
# Thread-safe hwnd release.

    @classmethod
    def _release_hwnd(cls, hwnd: int) -> None:
        """Thread-safe hwnd release."""
        with cls._claimed_lock:
            cls._claimed_hwnds.discard(hwnd)
