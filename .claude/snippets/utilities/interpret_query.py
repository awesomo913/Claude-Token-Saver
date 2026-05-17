# From: claude_backend/ollama_manager.py:257
# Ask the current model to extract search keywords from sloppy English.

    def interpret_query(self, user_query: str) -> str:
        """Ask the current model to extract search keywords from sloppy English."""
        if not self._current_model:
            return ""

        prompt = (
            "You are a code search assistant. The user describes what they want in "
            "casual English with possible typos. Extract the key technical terms and "
            "programming concepts. Output ONLY a comma-separated list of clean "
            "search keywords, nothing else.\n\n"
            f"User says: \"{user_query}\"\n\nKeywords:"
        )

        try:
            data = self._api_post("/api/generate", {
                "model": self._current_model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 60, "temperature": 0.1},
            }, timeout=15)
            raw = data.get("response", "").strip()
            import re
            keywords = re.sub(r"[^a-zA-Z0-9_, ]", "", raw.split("\n")[0])
            return keywords.strip().strip(",").strip()
        except Exception as e:
            logger.debug("Ollama interpret failed: %s", e)
            return ""
