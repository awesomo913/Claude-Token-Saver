# From: classifier/classifier.py:29

    @staticmethod
    def _load_keywords(path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to load keywords from %s: %s", path, e)
            return {"free_signals": {}, "claude_signals": {}, "domain_modifiers": {}}
