# From: cdp_client.py:523
# Get the current page title.

    def get_page_title(self) -> str:
        """Get the current page title."""
        try:
            return str(self.evaluate_js("document.title") or "")
        except Exception:
            return ""
