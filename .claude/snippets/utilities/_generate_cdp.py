# From: universal_client.py:321
# Generate using CDP — direct DOM manipulation. No mouse needed.

    def _generate_cdp(
        self,
        prompt: str,
        conversation: Optional[Conversation],
        on_progress: Optional[Callable[[str], None]],
    ) -> str:
        """Generate using CDP — direct DOM manipulation. No mouse needed."""
        for attempt in range(self.MAX_RETRIES):
            if self._cancel_event.is_set():
                raise InterruptedError("Generation cancelled")

            try:
                if on_progress:
                    on_progress(f"{self._profile.name}: Sending via CDP...")

                result = self._cdp.send_and_read(
                    prompt=prompt,
                    timeout=300,
                    on_progress=on_progress,
                    cancel_event=self._cancel_event,
                )

                if not result or len(result.strip()) < 5:
                    raise RuntimeError("Empty response from CDP")

                if conversation:
                    conversation.add_user_message(prompt)
                    conversation.add_model_message(result)

                logger.info("CDP response from %s: %d chars", self._profile.name, len(result))
                return result

            except InterruptedError:
                raise
            except Exception as e:
                logger.warning(
                    "%s CDP generation failed (attempt %d/%d): %s",
                    self._profile.name, attempt + 1, self.MAX_RETRIES, e
                )
                if attempt < self.MAX_RETRIES - 1:
                    # Try reconnecting CDP
                    self._cdp.connection.disconnect()
                    time.sleep(self.BASE_DELAY * (2 ** attempt))
                    if not self._try_configure_cdp():
                        logger.warning("CDP reconnect failed, will fall back to pyautogui")
                        self._cdp_available = False
                        return self._generate_pyautogui(prompt, conversation, on_progress)
                else:
                    raise RuntimeError(
                        f"{self._profile.name} CDP failed after {self.MAX_RETRIES} attempts: {e}"
                    ) from e

        return ""
