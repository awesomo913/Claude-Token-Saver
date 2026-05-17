# From: launch_token_saver.py:70
# Overlay mode if --overlay anywhere in argv.

def _is_overlay_mode() -> bool:
    """Overlay mode if --overlay anywhere in argv."""
    return "--overlay" in sys.argv[1:]
