"""Gemini client module stub for browser-based AI client."""

import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class Conversation:
    """Stub conversation class for browser-based clients."""

    def __init__(self, model: str = "gemini-2.0-flash", temperature: float = 0.9):
        self.model = model
        self.temperature = temperature
        self.history: List[dict] = []

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.history.append({"role": role, "content": content})

    def clear(self) -> None:
        """Clear conversation history."""
        self.history.clear()

    def get_messages(self) -> List[dict]:
        """Get the conversation history."""
        return list(self.history)


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
