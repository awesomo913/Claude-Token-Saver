# From: cdp_client.py:316
# Click a DOM element by selector.

    def click_element(self, selector: str) -> bool:
        """Click a DOM element by selector."""
        js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return false;
            el.scrollIntoView({{block: 'center'}});
            el.focus();
            el.click();
            return true;
        }})()
        """
        try:
            return bool(self.evaluate_js(js))
        except Exception:
            return False
