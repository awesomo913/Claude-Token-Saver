# From: universal_client.py:132
# Whether this client is using CDP (vs pyautogui fallback).

    @property
    def using_cdp(self) -> bool:
        """Whether this client is using CDP (vs pyautogui fallback)."""
        return self._cdp_available and self._cdp is not None
