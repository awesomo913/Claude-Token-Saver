# From: claude_backend/ollama_manager.py:44

    def __init__(self, host: str = DEFAULT_HOST) -> None:
        self.host = host.rstrip("/")
        self._current_model: Optional[str] = None
        self._models_cache: list[dict] = []
