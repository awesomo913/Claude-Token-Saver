# From: claude_backend/config.py:71
# Load a JSON config file, return empty dict on failure.

def _load_json(path: Path) -> dict:
    """Load a JSON config file, return empty dict on failure."""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if isinstance(data, dict):
            logger.debug("Loaded config from %s", path)
            return data
        logger.warning("Config at %s is not a JSON object, ignoring", path)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load config %s: %s", path, e)
    return {}
