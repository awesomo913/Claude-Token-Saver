# From: browser_actions.py:111
# Type text into the focused input via clipboard paste.

def type_prompt(text: str, chunk_size: int = 500) -> None:
    """Type text into the focused input via clipboard paste."""
    if not PYAUTOGUI_AVAILABLE or not PYPERCLIP_AVAILABLE:
        return

    if len(text) <= chunk_size:
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
        return

    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        pyperclip.copy(chunk)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.15)

    time.sleep(0.3)
