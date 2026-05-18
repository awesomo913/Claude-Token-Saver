# From: gemini_coder_web/bridge.py:17

    def __init__(self, session_manager: SessionManager, history=None, expander=None) -> None:
        self.session_manager = session_manager
        self._history = history
        self._expander = expander
