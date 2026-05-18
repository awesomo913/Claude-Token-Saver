# From: gemini_coder/config.py:57
# Get a configuration value.

    def get(self, key: str, default=None):
        """Get a configuration value."""
        return getattr(self.config, key, default)
