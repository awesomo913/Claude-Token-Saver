# From: cdp_client.py:516
# Get the current page URL.

    def get_page_url(self) -> str:
        """Get the current page URL."""
        try:
            return str(self.evaluate_js("window.location.href") or "")
        except Exception:
            return ""
