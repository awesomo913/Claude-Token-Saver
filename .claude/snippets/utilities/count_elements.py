# From: cdp_client.py:534
# Count how many elements match a selector.

    def count_elements(self, selector: str) -> int:
        """Count how many elements match a selector."""
        js = f"document.querySelectorAll({json.dumps(selector)}).length"
        try:
            return int(self.evaluate_js(js) or 0)
        except Exception:
            return 0
