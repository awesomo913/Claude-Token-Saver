# From: claude_backend/ollama_manager.py:136
# Get all locally installed models with metadata.

    def list_models(self) -> list[dict[str, Any]]:
        """Get all locally installed models with metadata."""
        try:
            data = self._api_get("/api/tags", timeout=5)
            raw = data.get("models", [])
            models = []
            for m in raw:
                name = m.get("model", "") or m.get("name", "")
                size = m.get("size", 0) or 0
                size_gb = round(size / (1024**3), 1)
                details = m.get("details", {}) or {}
                quant = details.get("quantization_level", "") or _detect_quant(name)
                models.append({
                    "name": name,
                    "size_gb": size_gb,
                    "family": details.get("family", "unknown"),
                    "parameters": details.get("parameter_size", "?"),
                    "quantization": quant.upper() if quant else "DEFAULT",
                    "modified": str(m.get("modified_at", ""))[:19],
                })
            self._models_cache = models
            return models
        except Exception as e:
            logger.debug("Failed to list models: %s", e)
            return []
