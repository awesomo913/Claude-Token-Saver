# From: session_manager.py:50

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._corner_map: dict[str, str] = {}  # corner -> session_id
