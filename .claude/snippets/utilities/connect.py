# From: cdp_client.py:195
# Open WebSocket connection to the CDP target.

    def connect(self) -> bool:
        """Open WebSocket connection to the CDP target."""
        try:
            self._ws = websocket.create_connection(
                self._ws_url,
                timeout=self._timeout,
                suppress_origin=True,
            )
            logger.info("CDP connected: %s", self._ws_url[:80])
            return True
        except Exception as e:
            logger.error("CDP connection failed: %s", e)
            return False
