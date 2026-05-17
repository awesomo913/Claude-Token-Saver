# From: claude_backend/prefs.py:59
# Load prefs. Missing file or bad JSON -> defaults.

    @classmethod
    def load(cls) -> "Prefs":
        """Load prefs. Missing file or bad JSON -> defaults."""
        if not PREFS_PATH.is_file():
            return cls()
        try:
            data = json.loads(PREFS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("prefs load failed (%s); using defaults", e)
            return cls()
        if not isinstance(data, dict):
            return cls()
        # Filter to known fields only — forward-compat for new keys.
        valid = {f.name for f in fields(cls)}
        clean = {k: v for k, v in data.items() if k in valid}
        try:
            return cls(**clean)
        except TypeError as e:
            logger.warning("prefs schema mismatch (%s); using defaults", e)
            return cls()
