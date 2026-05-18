# From: cdp_client.py:454
# Dispatch Enter key event on a specific element.

    def dispatch_enter_on(self, selector: str) -> bool:
        """Dispatch Enter key event on a specific element.

        Uses CDP Input.dispatchKeyEvent for maximum compatibility
        (works with ProseMirror, Quill, React, etc.)
        """
        # First focus the element
        focus_js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return false;
            el.focus();
            return true;
        }})()
        """
        try:
            focused = self.evaluate_js(focus_js)
            if not focused:
                return False
        except Exception:
            return False

        # Then dispatch Enter via CDP protocol (more reliable than JS events)
        try:
            self.send_command("Input.dispatchKeyEvent", {
                "type": "keyDown",
                "key": "Enter",
                "code": "Enter",
                "windowsVirtualKeyCode": 13,
                "nativeVirtualKeyCode": 13,
            })
            self.send_command("Input.dispatchKeyEvent", {
                "type": "keyUp",
                "key": "Enter",
                "code": "Enter",
                "windowsVirtualKeyCode": 13,
                "nativeVirtualKeyCode": 13,
            })
            return True
        except Exception as e:
            logger.warning("CDP Enter key failed: %s, trying JS fallback", e)

        # Fallback: JS-level events
        js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return false;
            el.focus();
            for (const type of ['keydown', 'keypress', 'keyup']) {{
                el.dispatchEvent(new KeyboardEvent(type, {{
                    key: 'Enter', code: 'Enter', keyCode: 13,
                    which: 13, bubbles: true, cancelable: true,
                }}));
            }}
            return true;
        }})()
        """
        try:
            return bool(self.evaluate_js(js))
        except Exception:
            return False
