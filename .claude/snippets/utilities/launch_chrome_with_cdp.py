# From: cdp_client.py:918
# Launch Chrome/Edge with remote debugging enabled.

def launch_chrome_with_cdp(
    url: str = "",
    port: int = DEFAULT_CDP_PORT,
    browser_exe: str = "",
    extra_args: Optional[list[str]] = None,
    corner: str = "",
) -> bool:
    """Launch Chrome/Edge with remote debugging enabled.

    Uses a dedicated Autocoder Chrome profile (~/.autocoder/chrome_profile).
    The user logs in once to each AI site and it's remembered across sessions.
    Chrome's real profile can't be used with --remote-debugging-port.
    """
    import subprocess
    import os
    from pathlib import Path

    if not browser_exe:
        from .window_manager import _find_browser_exe
        browser_exe = _find_browser_exe("chrome") or _find_browser_exe("edge") or ""

    if not browser_exe:
        logger.error("No browser found")
        return False

    # If a corner is specified, use its dedicated port
    if corner and corner in CDP_CORNER_PORTS:
        port = CDP_CORNER_PORTS[corner]

    args = [browser_exe] + get_chrome_debug_args(port)

    # Always use a dedicated Autocoder profile.
    # Chrome won't honor --remote-debugging-port with the real profile
    # because of its singleton process model. The user logs in once
    # to each AI site in this profile and it's remembered.
    profile_dir = str(Path.home() / ".autocoder" / "chrome_profile")
    args.append(f"--user-data-dir={profile_dir}")

    if extra_args:
        args.extend(extra_args)

    if url:
        args.append(url)

    try:
        subprocess.Popen(
            args,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        logger.info("Launched browser with CDP on port %d: %s", port, url)
        # Wait for browser to start
        time.sleep(4)
        return is_cdp_available(port)
    except Exception as e:
        logger.error("Failed to launch browser with CDP: %s", e)
        return False
