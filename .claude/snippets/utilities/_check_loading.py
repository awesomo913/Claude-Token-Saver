# From: cdp_client.py:851
# Check if any loading indicator is present.

    def _check_loading(self) -> bool:
        """Check if any loading indicator is present."""
        if not self._sel.loading_selector:
            return False
        for selector in self._sel.loading_selector.split(","):
            selector = selector.strip()
            if self._conn.find_element(selector):
                return True
        return False
