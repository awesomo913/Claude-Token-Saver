# From: launch_token_saver.py:65
# Tray mode if --tray (or -t) anywhere in argv. Other args ignored.

def _is_tray_mode() -> bool:
    """Tray mode if --tray (or -t) anywhere in argv. Other args ignored."""
    return any(a in ("--tray", "-t") for a in sys.argv[1:])
