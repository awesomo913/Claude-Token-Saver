# From: cdp_client.py:433
# Simulate pressing Enter on the focused element.

    def press_enter(self) -> bool:
        """Simulate pressing Enter on the focused element."""
        js = """
        (() => {
            const el = document.activeElement;
            if (!el) return false;
            const events = ['keydown', 'keypress', 'keyup'];
            for (const type of events) {
                el.dispatchEvent(new KeyboardEvent(type, {
                    key: 'Enter', code: 'Enter', keyCode: 13,
                    which: 13, bubbles: true, cancelable: true,
                }));
            }
            return true;
        })()
        """
        try:
            return bool(self.evaluate_js(js))
        except Exception:
            return False
