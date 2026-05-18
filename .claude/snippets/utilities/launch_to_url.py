# From: window_manager.py:186
# Launch a browser to a URL, position to corner, return hwnd.

def launch_to_url(
    url: str,
    corner: str = "bottom-right",
    browser: str = "chrome",
    title_pattern: str = "",
    enable_cdp: bool = True,
    cdp_port: int = 9222,
) -> Optional[int]:
    """Launch a browser to a URL, position to corner, return hwnd.

    Args:
        url: The URL to open
        corner: Screen corner to position the window
        browser: Which browser ("chrome", "edge", "firefox", "any")
        title_pattern: Pattern to find the window after launch
        enable_cdp: Add --remote-debugging-port for CDP automation
        cdp_port: Port for Chrome DevTools Protocol
    """
    if not url:
        return None

    rect = get_quarter_rect(corner)
    browser_exe = _find_browser_exe(browser)

    if not browser_exe:
        logger.error("Browser '%s' not found on this system", browser)
        return None

    args = [browser_exe]

    # Browser-specific window sizing args
    if "chrome" in browser_exe.lower() or "edge" in browser_exe.lower():
        args.extend([
            f"--window-size={rect.width},{rect.height}",
            f"--window-position={rect.x},{rect.y}",
            "--new-window",
        ])
        # Enable CDP for reliable automation
        if enable_cdp:
            args.append(f"--remote-debugging-port={cdp_port}")
    elif "firefox" in browser_exe.lower():
        args.extend([
            f"-width={rect.width}",
            f"-height={rect.height}",
        ])

    args.append(url)

    try:
        subprocess.Popen(args)
        logger.info("Launched %s to %s at %s corner", browser, url, corner)
    except FileNotFoundError:
        logger.error("Failed to launch %s", browser_exe)
        return None

    # Wait for window to appear
    time.sleep(3)

    # Find the window
    if title_pattern:
        handles = find_windows_by_title(title_pattern)
    else:
        # Try to guess from URL
        domain = url.split("//")[-1].split("/")[0].split(".")[0]
        handles = find_windows_by_title(domain)

    for hwnd in handles:
        move_window(hwnd, rect)
        logger.info("Found and positioned launched window: hwnd=%d", hwnd)
        return hwnd

    # Fallback: if we can't find by title, try the browser name
    if browser != "any":
        browser_name = os.path.basename(browser_exe).split(".")[0]
        handles = find_windows_by_title(browser_name)
        if handles:
            move_window(handles[0], rect)
            return handles[0]

    return None
