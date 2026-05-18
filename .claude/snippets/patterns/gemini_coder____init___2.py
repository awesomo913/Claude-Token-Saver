# From: gemini_coder/expander.py:12

    def __init__(self, client, depth_limit: int = 3) -> None:
        self._client = client
        self._depth_limit = depth_limit
