# From: universal_client.py:375
# Generate using pyautogui — legacy blind mouse/keyboard automation.

    def _generate_pyautogui(
        self,
        prompt: str,
        conversation: Optional[Conversation],
        on_progress: Optional[Callable[[str], None]],
    ) -> str:
        """Generate using pyautogui — legacy blind mouse/keyboard automation."""
        for attempt in range(self.MAX_RETRIES):
            if self._cancel_event.is_set():
                raise InterruptedError("Generation cancelled")

            try:
                # Re-check traffic availability at generate time
                use_traffic = (self._use_traffic and TRAFFIC_AVAILABLE
                               and TrafficClient.is_server_running())
                if use_traffic:
                    traffic_name = f"ai-coder-{self._corner}"

                    # PHASE 1: Acquire lock, send prompt, release lock (~5 seconds)
                    traffic = TrafficClient(traffic_name, timeout=self._traffic_timeout)
                    traffic.acquire()
                    try:
                        traffic.mark_move()
                        send_prompt_phase(self._hwnd, prompt, self._profile)
                    finally:
                        traffic.release()

                    # PHASE 2: Wait (NO lock, all sessions wait in parallel)
                    if on_progress:
                        on_progress(f"{self._profile.name}: Waiting for response (pyautogui)...")
                    wait_for_generation_done(
                        self._hwnd, prompt_length=len(prompt),
                        profile=self._profile, timeout=300,
                        on_progress=on_progress, cancel_event=self._cancel_event,
                    )
                    time.sleep(POST_GENERATE_WAIT)

                    # PHASE 3: Acquire lock, read response, release lock (~5 seconds)
                    traffic2 = TrafficClient(traffic_name, timeout=self._traffic_timeout)
                    traffic2.acquire()
                    try:
                        traffic2.mark_move()
                        result = read_response_phase(self._hwnd, self._profile)
                    finally:
                        traffic2.release()
                else:
                    result = self._do_generate_pyautogui(prompt, on_progress)

                if conversation:
                    conversation.add_user_message(prompt)
                    conversation.add_model_message(result)

                return result

            except InterruptedError:
                raise
            except Exception as e:
                logger.warning(
                    "%s pyautogui generation failed (attempt %d/%d): %s",
                    self._profile.name, attempt + 1, self.MAX_RETRIES, e
                )
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.BASE_DELAY * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise RuntimeError(
                        f"{self._profile.name} failed after {self.MAX_RETRIES} attempts: {e}"
                    ) from e

        return ""
