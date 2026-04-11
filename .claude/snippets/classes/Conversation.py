# From: gemini_coder/gemini_client.py:9

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
