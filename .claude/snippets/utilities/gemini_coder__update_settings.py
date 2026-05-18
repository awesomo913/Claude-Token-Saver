# From: gemini_coder/gemini_client.py:50
# Update client settings.

    def update_settings(self, **kwargs) -> None:
        """Update client settings."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
