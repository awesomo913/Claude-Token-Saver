# From: browser_actions.py:273
# Switch the active model on OpenRouter's AI Chat Playground.

def switch_model_openrouter(hwnd: int, model_name: str) -> bool:
    """Switch the active model on OpenRouter's AI Chat Playground.

    OpenRouter layout: model tabs appear near the top of the chat pane.
    There's a "+" button to add a new model tab. Clicking "+" opens
    a model search dropdown. We type the model name, click the result.

    Also works if the model is already a tab — we just click it.
    """
    if not PYAUTOGUI_AVAILABLE or not PYPERCLIP_AVAILABLE:
        return False

    try:
        rect = get_window_rect(hwnd)
        if not rect:
            return False

        left, top, right, bottom = rect
        win_w = right - left
        win_h = bottom - top
        focus_window(hwnd)
        time.sleep(0.5)

        # Check window title to see if model is already selected
        title = _get_window_title(hwnd)

        # OpenRouter chat layout:
        # - Top bar: OpenRouter logo + nav (~40px)
        # - Below that: model tabs row (~35px) with "+" button at the end
        # - Below that: chat area
        # The model tab row starts about 90-110px from top of window

        # Click the "+" button to open model picker
        # "+" is after the existing tabs, roughly right-center area
        plus_x = left + int(win_w * 0.45)
        plus_y = top + 105  # Model tab row area
        pyautogui.click(plus_x, plus_y)
        time.sleep(1.0)

        # A search/dropdown should appear — type model name to filter
        # Clear any existing text first
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)

        # Type the short search term (just key part of model name)
        # e.g., "Qwen3.6" from "Qwen3.6 Plus Preview (free)"
        search_term = model_name.split("(")[0].strip()  # Remove "(free)" etc.
        pyperclip.copy(search_term)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(1.5)

        # Click the first search result (appears below the search input)
        result_x = plus_x
        result_y = plus_y + 60
        pyautogui.click(result_x, result_y)
        time.sleep(0.8)

        # Press Escape to close any remaining dropdown
        pyautogui.press("escape")
        time.sleep(0.3)

        logger.info("Switched model to '%s' on hwnd=%d", model_name, hwnd)
        return True

    except Exception as e:
        logger.warning("Failed to switch model: %s", e)
        return False
