# From: claude_backend/ollama_manager.py:51
# Check if Ollama server is reachable.

    def is_running(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            self._api_get("/api/tags", timeout=3)
            return True
        except Exception:
            return False
