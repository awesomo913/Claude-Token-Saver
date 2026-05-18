# From: cdp_client.py:706
# Wait for the AI to finish generating its response.

    def wait_for_response(
        self,
        timeout: float = MAX_COMPLETION_WAIT,
        poll_interval: float = COMPLETION_POLL_INTERVAL,
        on_progress: Optional[Any] = None,
        cancel_event: Optional[threading.Event] = None,
    ) -> bool:
        """Wait for the AI to finish generating its response.

        Uses multiple detection strategies:
        1. New response element appears (count increases)
        2. Loading/stop indicators appear then disappear
        3. Response text stops changing (stabilizes)

        Returns True if response detected, False on timeout.
        """
        start = time.time()
        last_text = ""
        stable_count = 0
        STABLE_THRESHOLD = 3  # Text unchanged for 3 polls = done
        new_response_detected = False
        initial_text = self._get_latest_response_text()

        # Initial delay to let generation start
        time.sleep(1.5)

        while time.time() - start < timeout:
            if cancel_event and cancel_event.is_set():
                raise InterruptedError("Cancelled during wait")

            elapsed = time.time() - start

            # Check indicators
            has_loading = self._check_loading()
            has_stop = self._check_stop_button()

            # Check response count
            current_count = self._count_responses()
            if current_count > self._response_count_before:
                new_response_detected = True

            # Get latest response text
            current_text = self._get_latest_response_text()

            # Ignore temporary empty reads (DOM re-rendering)
            if not current_text and last_text:
                current_text = last_text  # Keep previous value

            # Only count as stable if a NEW response appeared and text changed
            if new_response_detected and current_text != initial_text:
                if current_text and current_text == last_text and len(current_text) > 5:
                    stable_count += 1
                elif current_text and current_text != last_text:
                    stable_count = 0  # Still changing
                # Don't reset stable_count for empty reads
            else:
                stable_count = 0
            last_text = current_text

            # Report progress
            if on_progress:
                remaining = int(timeout - elapsed)
                status = "generating" if (has_loading or has_stop) else "checking"
                on_progress(
                    f"{self._profile_name}: {status}... "
                    f"{remaining}s remaining | {len(current_text)} chars"
                )

            # Decision: Are we done?
            if new_response_detected and current_text != initial_text:
                # New response appeared and text is different from before
                if not has_loading and not has_stop and stable_count >= STABLE_THRESHOLD:
                    logger.info(
                        "%s finished generating (%.1fs, %d chars)",
                        self._profile_name, elapsed, len(current_text)
                    )
                    return True
            elif elapsed > 20 and not new_response_detected:
                # 20s and no new response element — maybe the site uses
                # a different structure. Check if text changed at all.
                if current_text and current_text != initial_text and stable_count >= STABLE_THRESHOLD:
                    logger.info("%s: text changed and stabilized after %.1fs", self._profile_name, elapsed)
                    return True

            time.sleep(poll_interval)

        logger.warning("%s: response wait timed out after %.0fs", self._profile_name, timeout)
        return False
