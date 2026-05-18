# From: extension_native_bridge/host/claude_native_host.py:58
# Read one Native Messaging frame from stdin.

def read_message() -> dict | None:
    """Read one Native Messaging frame from stdin."""
    raw_len = sys.stdin.buffer.read(4)
    if not raw_len:
        return None
    (length,) = struct.unpack("<I", raw_len)
    if length > 64 * 1024 * 1024:
        logger.error("Rejecting oversized frame: %s", length)
        return None
    data = sys.stdin.buffer.read(length)
    if len(data) != length:
        return None
    try:
        return json.loads(data.decode("utf-8"))
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON from extension: %s", e)
        return None
