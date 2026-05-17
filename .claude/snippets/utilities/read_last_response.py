# From: cdp_client.py:795
# Read the text of the AI's most recent response.

    def read_last_response(self) -> str:
        """Read the text of the AI's most recent response.

        Always gets ALL response elements and takes the LAST one.
        CSS :last-of-type selectors are unreliable for nested chat structures.
        """
        if not self._conn.is_connected:
            return ""

        # Primary: Get all responses via response_selector, take last
        if self._sel.response_selector:
            for selector in self._sel.response_selector.split(","):
                selector = selector.strip()
                texts = self._conn.get_all_elements_text(selector)
                if texts:
                    meaningful = [t for t in texts if len(t.strip()) > 5]
                    if meaningful:
                        return meaningful[-1].strip()

        # Fallback: try common selectors
        fallback_selectors = [
            ".markdown", ".prose", "[class*='response'] .markdown",
            "[class*='message']", "[class*='answer']",
            "article", ".content",
        ]
        for selector in fallback_selectors:
            texts = self._conn.get_all_elements_text(selector)
            meaningful = [t for t in texts if len(t.strip()) > 10]
            if meaningful:
                return meaningful[-1].strip()

        logger.warning("Could not find response text for %s", self._profile_name)
        return ""
