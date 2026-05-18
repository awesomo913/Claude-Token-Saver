# From: cdp_client.py:630

    def __init__(
        self,
        connection: CDPConnection,
        selectors: CDPSelectors,
        profile_name: str = "Unknown",
    ) -> None:
        self._conn = connection
        self._sel = selectors
        self._profile_name = profile_name
        self._response_count_before: int = 0
