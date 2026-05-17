# From: cdp_client.py:861
# Check if a stop/cancel generation button is present.

    def _check_stop_button(self) -> bool:
        """Check if a stop/cancel generation button is present."""
        if not self._sel.stop_button_selector:
            return False
        for selector in self._sel.stop_button_selector.split(","):
            selector = selector.strip()
            if self._conn.find_element(selector):
                return True
        return False
