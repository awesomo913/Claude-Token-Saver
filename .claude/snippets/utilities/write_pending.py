# From: claude_backend/http_server.py:419
# Write IPC payload for GUI to pick up. Atomic via os.replace.

def write_pending(payload: dict) -> bool:
    """Write IPC payload for GUI to pick up. Atomic via os.replace."""
    try:
        PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = PENDING_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, PENDING_PATH)
        return True
    except OSError as e:
        logger.warning("Failed to write pending file: %s", e)
        return False
