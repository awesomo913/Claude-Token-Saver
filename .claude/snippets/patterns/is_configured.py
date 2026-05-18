# From: universal_client.py:124

    @property
    def is_configured(self) -> bool:
        return self._configured and (self._cdp_available or self._hwnd is not None)
