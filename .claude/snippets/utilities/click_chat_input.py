# From: browser_actions.py:87
# Click on the AI chat input area using profile offsets.

def click_chat_input(hwnd: int, profile: AIProfile = GEMINI_PROFILE) -> bool:
    """Click on the AI chat input area using profile offsets."""
    if not PYAUTOGUI_AVAILABLE:
        return False

    rect = get_window_rect(hwnd)
    if not rect:
        return False

    left, top, right, bottom = rect
    win_w = right - left

    # Chat input is usually center-right (sites have left sidebars)
    # Use 60% from left edge for the x-coordinate
    cx = left + int(win_w * 0.6)
    cy = bottom - profile.input_offset_from_bottom

    focus_window(hwnd)
    time.sleep(0.3)
    pyautogui.click(cx, cy)
    time.sleep(0.5)
    return True
