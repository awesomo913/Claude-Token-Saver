# From: cdp_client.py:976
# Check if Chrome is currently running.

def is_chrome_running() -> bool:
    """Check if Chrome is currently running."""
    import subprocess
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq chrome.exe'],
            capture_output=True, text=True, timeout=5,
        )
        return 'chrome.exe' in result.stdout
    except Exception:
        return False
