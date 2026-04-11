# From: browser_actions.py:131
# Send the message using the profile's send method.

def send_message(hwnd: int, profile: AIProfile = GEMINI_PROFILE) -> None:
    """Send the message using the profile's send method."""
    if not PYAUTOGUI_AVAILABLE:
        return

    if profile.send_method == "click_button":
        rect = get_window_rect(hwnd)
        if rect:
            left, top, right, bottom = rect
            sx = right - profile.send_button_right_offset
            sy = bottom - profile.send_button_bottom_offset
            pyautogui.click(sx, sy)
    else:
        pyautogui.press("enter")

    time.sleep(0.5)
