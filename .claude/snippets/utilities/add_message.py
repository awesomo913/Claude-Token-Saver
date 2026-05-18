# From: gemini_coder/gemini_client.py:17
# Add a message to the conversation history.

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.history.append({"role": role, "content": content})
