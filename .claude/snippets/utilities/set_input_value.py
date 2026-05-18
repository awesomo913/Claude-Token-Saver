# From: cdp_client.py:333
# Set the value of an input element.

    def set_input_value(self, selector: str, text: str, is_contenteditable: bool = False) -> bool:
        """Set the value of an input element.

        Handles both <textarea> and contenteditable <div> elements.
        For contenteditable (ProseMirror, Quill), uses CDP Input.insertText
        which is more reliable than execCommand and properly triggers
        framework state updates.
        """
        escaped_text = json.dumps(text)

        if is_contenteditable:
            # Step 1: Focus the element and clear it
            focus_js = f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return false;
                el.focus();
                // Select all existing content and delete it
                const sel = window.getSelection();
                sel.selectAllChildren(el);
                return true;
            }})()
            """
            try:
                focused = self.evaluate_js(focus_js)
                if not focused:
                    return False
            except Exception:
                return False

            # Step 2: Delete existing content via CDP keyboard
            try:
                self.send_command("Input.dispatchKeyEvent", {
                    "type": "keyDown", "key": "Backspace", "code": "Backspace",
                    "windowsVirtualKeyCode": 8, "nativeVirtualKeyCode": 8,
                })
                self.send_command("Input.dispatchKeyEvent", {
                    "type": "keyUp", "key": "Backspace", "code": "Backspace",
                    "windowsVirtualKeyCode": 8, "nativeVirtualKeyCode": 8,
                })
            except Exception:
                pass  # May fail if empty, that's OK

            import time as _time
            _time.sleep(0.1)

            # Step 3: Insert text via CDP (works with ProseMirror, Quill, etc.)
            try:
                self.send_command("Input.insertText", {"text": text})
                logger.debug("Inserted %d chars via CDP Input.insertText", len(text))
                return True
            except Exception as e:
                logger.warning("CDP Input.insertText failed: %s, trying execCommand", e)

            # Fallback: execCommand
            js = f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return false;
                el.focus();
                el.innerHTML = '';
                document.execCommand('insertText', false, {escaped_text});
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                return true;
            }})()
            """
            try:
                return bool(self.evaluate_js(js))
            except Exception as e:
                logger.error("Both CDP and execCommand failed: %s", e)
                return False
        else:
            # Standard textarea/input
            js = f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return false;
                el.focus();
                // Use native setter to bypass React's synthetic events
                const nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLTextAreaElement.prototype, 'value'
                )?.set || Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                )?.set;
                if (nativeSetter) {{
                    nativeSetter.call(el, {escaped_text});
                }} else {{
                    el.value = {escaped_text};
                }}
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                return true;
            }})()
            """
            try:
                return bool(self.evaluate_js(js))
            except Exception as e:
                logger.error("Failed to set textarea value: %s", e)
                return False
