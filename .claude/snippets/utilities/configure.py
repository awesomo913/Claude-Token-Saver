# From: universal_client.py:156
# Find or launch the AI's window. api_key param ignored (compat).

    def configure(self, api_key: str = "") -> bool:
        """Find or launch the AI's window. api_key param ignored (compat).

        Tries CDP first (connect to existing Chrome debug port),
        then falls back to pyautogui window finding.
        """
        # ── Try CDP first ─────────────────────────────────────────
        if self._try_configure_cdp():
            logger.info("Configured %s via CDP (reliable DOM mode)", self._profile.name)
            self._configured = True
            return True

        # ── Fallback to pyautogui ─────────────────────────────────
        if not PYAUTOGUI_AVAILABLE:
            logger.error("Neither CDP nor pyautogui available")
            return False

        # Don't permanently disable traffic — it may start later
        if self._use_traffic and not TrafficClient.is_server_running():
            logger.warning("Traffic Controller not running yet (will re-check at generate time)")

        # Try to find an existing window matching the profile
        if self._profile.title_pattern:
            handles = find_windows_by_title(self._profile.title_pattern)
            with self._claimed_lock:
                available = [h for h in handles if h not in self._claimed_hwnds]
            if available:
                self._hwnd = available[0]
                with self._claimed_lock:
                    self._claimed_hwnds.add(self._hwnd)
                position_existing_window(self._hwnd, self._corner)
                self._configured = True
                logger.info("Found %s window: hwnd=%d (pyautogui fallback)",
                            self._profile.name, self._hwnd)
                return True

        # No existing window — try to launch
        if self._profile.url:
            hwnd = launch_to_url(
                url=self._profile.url,
                corner=self._corner,
                browser=self._profile.browser,
                title_pattern=self._profile.title_pattern,
            )
            if hwnd:
                self._hwnd = hwnd
                with self._claimed_lock:
                    self._claimed_hwnds.add(hwnd)
                self._configured = True
                logger.info("Launched %s window: hwnd=%d (pyautogui fallback)",
                            self._profile.name, hwnd)
                return True

        logger.error("Could not find or launch %s window", self._profile.name)
        return False
