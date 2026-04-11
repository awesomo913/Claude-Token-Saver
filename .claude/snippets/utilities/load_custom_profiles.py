# From: ai_profiles.py:251
# Load custom profiles from disk.

def load_custom_profiles() -> list[AIProfile]:
    """Load custom profiles from disk."""
    path = _custom_profiles_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [AIProfile.from_dict(d) for d in data]
    except Exception as e:
        logger.error("Failed to load custom profiles: %s", e)
        return []
