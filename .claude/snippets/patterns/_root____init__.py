# From: cdp_client.py:188

    def __init__(self, ws_url: str, timeout: float = CDP_TIMEOUT) -> None:
        self._ws_url = ws_url
        self._timeout = timeout
        self._ws: Optional[websocket.WebSocket] = None
        self._msg_id = 0
        self._lock = threading.Lock()
