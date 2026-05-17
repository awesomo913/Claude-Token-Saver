# From: claude_backend/ollama_manager.py:162
# Just the names.

    def get_model_names(self) -> list[str]:
        """Just the names."""
        return [m["name"] for m in self.list_models()]
