# From: cdp_client.py:989
# Kill all Chrome processes (needed to relaunch with CDP).

def kill_chrome() -> bool:
    """Kill all Chrome processes (needed to relaunch with CDP)."""
    import subprocess
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'],
                       capture_output=True, timeout=10)
        time.sleep(2)
        return not is_chrome_running()
    except Exception:
        return False
