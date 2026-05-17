# From: cdp_client.py:530
# Scroll the page to the bottom (useful for chat views).

    def scroll_to_bottom(self) -> None:
        """Scroll the page to the bottom (useful for chat views)."""
        self.evaluate_js("window.scrollTo(0, document.body.scrollHeight)")
