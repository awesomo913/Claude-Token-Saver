# From: cdp_client.py:896
# Count the number of response elements on the page.

    def _count_responses(self) -> int:
        """Count the number of response elements on the page."""
        if self._sel.response_selector:
            for selector in self._sel.response_selector.split(","):
                selector = selector.strip()
                count = self._conn.count_elements(selector)
                if count > 0:
                    return count
        return 0
