# From: cdp_client.py:649
# Type a prompt into the chat input and send it.

    def send_prompt(self, text: str) -> bool:
        """Type a prompt into the chat input and send it.

        Returns True if the prompt was sent successfully.
        """
        if not self._conn.is_connected:
            logger.error("CDP not connected for %s", self._profile_name)
            return False

        # Record current response count for completion detection
        self._response_count_before = self._count_responses()

        # Find and focus the input element
        # Try each selector in the comma-separated list
        input_found = False
        for selector in self._sel.input_selector.split(","):
            selector = selector.strip()
            if self._conn.find_element(selector):
                if self._conn.set_input_value(
                    selector, text,
                    is_contenteditable=self._sel.input_is_contenteditable,
                ):
                    input_found = True
                    logger.debug("Input found with selector: %s", selector)
                    break

        if not input_found:
            logger.error("Could not find chat input for %s", self._profile_name)
            return False

        # Small delay for UI to register the input
        time.sleep(0.3)

        # Send the message
        if self._sel.send_with_enter:
            # Dispatch Enter on the input
            for selector in self._sel.input_selector.split(","):
                selector = selector.strip()
                if self._conn.find_element(selector):
                    self._conn.dispatch_enter_on(selector)
                    break
        else:
            # Click the send button
            sent = False
            for selector in self._sel.send_button_selector.split(","):
                selector = selector.strip()
                if self._conn.click_element(selector):
                    sent = True
                    break
            if not sent:
                # Fallback: try Enter anyway
                logger.warning("Send button not found, trying Enter key")
                self._conn.press_enter()

        logger.info("Prompt sent to %s (%d chars)", self._profile_name, len(text))
        return True
