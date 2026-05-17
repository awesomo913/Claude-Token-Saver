# From: universal_client.py:290
# Generate a response by typing into the AI web chat.

    def generate(
        self,
        prompt: str,
        conversation: Optional[Conversation] = None,
        system_instruction: str = "",
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Generate a response by typing into the AI web chat.

        Uses CDP if available, falls back to pyautogui.
        """
        self._cancel_event.clear()

        if not self.is_configured:
            raise RuntimeError(
                f"{self._profile.name} not configured. "
                "Click 'Launch' in the session panel."
            )

        with self._lock:
            # Try CDP first
            if self._cdp_available and self._cdp and self._cdp.is_connected:
                return self._generate_cdp(prompt, conversation, on_progress)

            # Try to reconnect CDP (connection may have dropped)
            if self._try_configure_cdp():
                return self._generate_cdp(prompt, conversation, on_progress)

            # Fallback to pyautogui
            return self._generate_pyautogui(prompt, conversation, on_progress)
