# From: extension_native_bridge/host/claude_native_host.py:77
# Send one frame to Chrome.

def write_message(obj: dict) -> None:
    """Send one frame to Chrome."""
    j = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    with _write_lock:
        sys.stdout.buffer.write(struct.pack("<I", len(j)))
        sys.stdout.buffer.write(j)
        sys.stdout.buffer.flush()
