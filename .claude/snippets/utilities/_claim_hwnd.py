# From: universal_client.py:141
# Thread-safe hwnd claiming.

    @classmethod
    def _claim_hwnd(cls, hwnd: int) -> bool:
        """Thread-safe hwnd claiming."""
        with cls._claimed_lock:
            if hwnd in cls._claimed_hwnds:
                return False
            cls._claimed_hwnds.add(hwnd)
            return True
