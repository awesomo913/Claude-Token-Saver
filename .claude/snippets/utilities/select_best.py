# From: claude_backend/ollama_manager.py:168
# Auto-select the best small model for search assist.

    def select_best(self) -> Optional[str]:
        """Auto-select the best small model for search assist.

        Priority: coding+turbo > coding > small turbo > first available.
        """
        models = self.list_models()
        if not models:
            return None

        # Pass 1: coding + turbo quant
        for m in models:
            nl = m["name"].lower()
            if any(k in nl for k in CODING_KEYWORDS) and m["quantization"].lower() in TURBO_QUANTS:
                self._current_model = m["name"]; return m["name"]

        # Pass 2: any coding model
        for m in models:
            if any(k in m["name"].lower() for k in CODING_KEYWORDS):
                self._current_model = m["name"]; return m["name"]

        # Pass 3: smallest model (for search, we want fast not smart)
        models_by_size = sorted(models, key=lambda m: m["size_gb"])
        self._current_model = models_by_size[0]["name"]
        return self._current_model
