# From: claude_backend/hotkey.py:54
# Triggered by hotkey press. Runs in a fresh thread each fire.

def _capture_and_improve() -> None:
    """Triggered by hotkey press. Runs in a fresh thread each fire."""
    if pyautogui is None or pyperclip is None:
        logger.warning("Hotkey trigger requires pyautogui + pyperclip")
        return

    try:
        prefs = Prefs.load()

        # Save and restore clipboard so the user's normal clipboard
        # contents aren't permanently overwritten by our select-all+copy.
        saved = ""
        try:
            saved = pyperclip.paste()
        except Exception:
            pass

        # Select-all + copy in the focused window. Hotkey already
        # consumed the Ctrl+Shift+I keystroke; we send fresh keystrokes.
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.1)

        captured = ""
        try:
            captured = pyperclip.paste()
        except Exception as e:
            logger.warning("Clipboard read failed: %s", e)

        captured = (captured or "").strip()
        if not captured:
            logger.info("Hotkey: empty clipboard, aborting")
            return

        # Use last_project_path. Hotkey path doesn't show a picker — too
        # disruptive when fired from a terminal. User picks via GUI/overlay
        # if they want a different project.
        project_path = prefs.last_project_path or ""

        body = json.dumps({
            "prompt": captured, "project_path": project_path,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{prefs.http_port}/improve",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            _ = r.read()

        # Restore clipboard (best-effort).
        if saved:
            try:
                pyperclip.copy(saved)
            except Exception:
                pass
    except Exception as e:
        logger.warning("Hotkey pipeline failed: %s", e)
