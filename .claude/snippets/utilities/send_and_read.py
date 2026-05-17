# From: cdp_client.py:829
# Full cycle: send prompt, wait for response, read it.

    def send_and_read(
        self,
        prompt: str,
        timeout: float = MAX_COMPLETION_WAIT,
        on_progress: Optional[Any] = None,
        cancel_event: Optional[threading.Event] = None,
    ) -> str:
        """Full cycle: send prompt, wait for response, read it."""
        if not self.send_prompt(prompt):
            raise RuntimeError(f"Failed to send prompt to {self._profile_name}")

        if not self.wait_for_response(
            timeout=timeout,
            on_progress=on_progress,
            cancel_event=cancel_event,
        ):
            logger.warning("%s: wait timed out, reading whatever is available", self._profile_name)

        # Small delay for final rendering
        time.sleep(1.0)
        return self.read_last_response()
