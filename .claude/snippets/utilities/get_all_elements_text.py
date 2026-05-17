# From: cdp_client.py:302
# Get text content of ALL elements matching a selector.

    def get_all_elements_text(self, selector: str) -> list[str]:
        """Get text content of ALL elements matching a selector."""
        js = f"""
        (() => {{
            const els = document.querySelectorAll({json.dumps(selector)});
            return Array.from(els).map(el => el.innerText || el.textContent || '');
        }})()
        """
        try:
            result = self.evaluate_js(js)
            return result if isinstance(result, list) else []
        except Exception:
            return []
