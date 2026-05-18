# From: browser_actions.py:205
# Read all visible text from the AI page or terminal. Done ONCE, carefully.

def read_page_text_once(hwnd: int, profile: AIProfile = GEMINI_PROFILE) -> str:
    """Read all visible text from the AI page or terminal. Done ONCE, carefully."""
    if not PYAUTOGUI_AVAILABLE or not PYPERCLIP_AVAILABLE:
        return ""

    try:
        rect = get_window_rect(hwnd)
        if not rect:
            return ""

        left, top, right, bottom = rect
        is_terminal = _is_terminal_window(hwnd)

        # Ensure THIS window is focused
        focus_window(hwnd)
        time.sleep(0.5)
        focus_window(hwnd)
        time.sleep(0.3)

        pyperclip.copy("__SENTINEL__")

        if is_terminal:
            # Terminals: right-click opens context menu with "Select All" / "Copy"
            # Or use keyboard: Ctrl+Shift+A to select all, then Enter to copy
            # Windows Terminal / PowerShell: Ctrl+A selects in input only
            # Best approach: click body area, then Ctrl+Shift+A, Enter
            safe_x = left + int((right - left) * 0.5)
            safe_y = top + int((bottom - top) * 0.5)
            pyautogui.click(safe_x, safe_y)
            time.sleep(0.3)

            # Select all text in terminal buffer
            pyautogui.hotkey("ctrl", "shift", "a")  # Windows Terminal: select all
            time.sleep(0.3)
            pyautogui.hotkey("ctrl", "shift", "c")  # Copy selection
            time.sleep(0.5)
        else:
            # Browser: click safe area, Ctrl+A, Ctrl+C
            safe_x = left + int((right - left) * 0.6)
            safe_y = top + int((bottom - top) * profile.read_click_fraction)
            pyautogui.click(safe_x, safe_y)
            time.sleep(0.5)

            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.5)
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.8)

        text = pyperclip.paste()

        # Clean up
        pyautogui.press("escape")
        time.sleep(0.1)
        pyperclip.copy("")
        time.sleep(0.1)

        if text == "__SENTINEL__" or not text:
            return ""

        return text.strip()

    except Exception as e:
        logger.error("Failed to read page text: %s", e)
        return ""
