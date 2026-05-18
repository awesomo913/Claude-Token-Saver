# From: gemini_coder/gemini_client.py:25
# Get the conversation history.

    def get_messages(self) -> List[dict]:
        """Get the conversation history."""
        return list(self.history)
