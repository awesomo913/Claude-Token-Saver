# From: cdp_client.py:218

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and self._ws.connected
