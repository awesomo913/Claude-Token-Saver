# From: universal_client.py:446
# Browser automation with defensive timeout (pyautogui).

    def _do_generate_pyautogui(
        self,
        prompt: str,
        on_progress: Optional[Callable[[str], None]],
    ) -> str:
        """Browser automation with defensive timeout (pyautogui)."""
        result = safe_call(
            send_prompt_and_get_response,
            args=(self._hwnd, prompt),
            kwargs={
                "profile": self._profile,
                "timeout": 300,
                "on_progress": on_progress,
                "cancel_event": self._cancel_event,
            },
            timeout_ms=330_000,
        )

        if result.timed_out:
            raise RuntimeError(
                f"{self._profile.name} automation timed out. "
                "Force-killed to protect the main loop."
            )
        if result.error:
            raise RuntimeError(f"{self._profile.name} error: {result.error}")

        return result.stdout
