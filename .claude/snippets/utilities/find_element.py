# From: cdp_client.py:280
# Check if a DOM element matching the selector exists.

    def find_element(self, selector: str) -> bool:
        """Check if a DOM element matching the selector exists."""
        js = f"!!document.querySelector({json.dumps(selector)})"
        try:
            return bool(self.evaluate_js(js))
        except Exception:
            return False
