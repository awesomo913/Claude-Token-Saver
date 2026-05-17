# From: universal_client.py:474
# Test that the AI window is accessible.

    def test_connection(self) -> tuple[bool, str]:
        """Test that the AI window is accessible."""
        # Test CDP first
        if self._cdp_available and self._cdp and self._cdp.is_connected:
            try:
                title = self._cdp.connection.get_page_title()
                url = self._cdp.connection.get_page_url()
                return True, f"{self._profile.name} ready via CDP ({title[:30]})"
            except Exception:
                pass

        # Test pyautogui
        if not PYAUTOGUI_AVAILABLE:
            return False, "Neither CDP nor pyautogui available"

        if self._hwnd is None:
            configured = self.configure()
            if not configured:
                return False, f"Could not find or launch {self._profile.name}"

        if focus_window(self._hwnd):
            mode = "CDP" if self._cdp_available else "pyautogui"
            traffic_status = ""
            if self._use_traffic:
                if TrafficClient.is_server_running():
                    traffic_status = " | Traffic: Connected"
                else:
                    traffic_status = " | Traffic: Not running"
            return True, f"{self._profile.name} ready [{mode}] (hwnd={self._hwnd}){traffic_status}"

        return False, f"Could not focus {self._profile.name} window"
