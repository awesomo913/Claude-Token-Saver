# From: cdp_client.py:871
# Get the text of the LAST (newest) response for change detection.

    def _get_latest_response_text(self) -> str:
        """Get the text of the LAST (newest) response for change detection.

        Always uses get_all_elements_text and takes [-1] to ensure
        we're reading the newest response, not an older one.
        """
        # Strategy: get ALL response elements and take the last one
        if self._sel.response_selector:
            for selector in self._sel.response_selector.split(","):
                selector = selector.strip()
                texts = self._conn.get_all_elements_text(selector)
                if texts:
                    # Filter meaningful and return the last
                    meaningful = [t for t in texts if len(t.strip()) > 5]
                    if meaningful:
                        return meaningful[-1]
        # Fallback to last_response_selector
        if self._sel.last_response_selector:
            for selector in self._sel.last_response_selector.split(","):
                selector = selector.strip()
                text = self._conn.get_element_text(selector)
                if text and len(text.strip()) > 5:
                    return text
        return ""
