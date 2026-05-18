# From: gemini_coder/config.py:50
# Update configuration fields.

    def update(self, **kwargs) -> None:
        """Update configuration fields."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save()
