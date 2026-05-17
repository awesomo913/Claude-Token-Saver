# From: cdp_client.py:288
# Get the text content of an element.

    def get_element_text(self, selector: str) -> str:
        """Get the text content of an element."""
        js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            return el ? el.innerText || el.textContent || '' : '';
        }})()
        """
        try:
            result = self.evaluate_js(js)
            return str(result) if result else ""
        except Exception:
            return ""
