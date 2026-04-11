# From: gemini_coder/gemini_client.py:30

class GeminiClient:
    """Stub Gemini client for browser-based automation."""

    def __init__(self, api_key: str = "", model: str = "gemini-2.0-flash", 
                 temperature: float = 0.9):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.conversation = Conversation(model, temperature)

    def generate(self, prompt: str, system_instruction: str = "",
                 on_progress: Optional[callable] = None) -> str:
        """Generate a response (stub - actual implementation uses browser automation)."""
        logger.warning("GeminiClient.generate() called - this should use browser automation instead")
        return f"[Stub] Response to: {prompt[:50]}..."

    def cancel(self) -> None:
        """Cancel any ongoing generation."""
        pass

    def update_settings(self, **kwargs) -> None:
        """Update client settings."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
