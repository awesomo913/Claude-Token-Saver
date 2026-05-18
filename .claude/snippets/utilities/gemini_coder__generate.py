# From: gemini_coder/gemini_client.py:40
# Generate a response (stub - actual implementation uses browser automation).

    def generate(self, prompt: str, system_instruction: str = "",
                 on_progress: Optional[callable] = None) -> str:
        """Generate a response (stub - actual implementation uses browser automation)."""
        logger.warning("GeminiClient.generate() called - this should use browser automation instead")
        return f"[Stub] Response to: {prompt[:50]}..."
