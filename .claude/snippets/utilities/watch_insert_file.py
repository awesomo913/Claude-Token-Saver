# From: extension_native_bridge/host/claude_native_host.py:139
# Poll insert_request.json; on change, send insert_text to extension.

def watch_insert_file(stop: threading.Event) -> None:
    """Poll insert_request.json; on change, send insert_text to extension."""
    mtime = 0.0
    while not stop.is_set():
        time.sleep(0.4)
        try:
            p = INSERT_FILE
            if not p.is_file():
                continue
            cur = p.stat().st_mtime
            if cur == mtime:
                continue
            mtime = cur
            data = json.loads(p.read_text(encoding="utf-8"))
            text = (data.get("text") or "").strip()
            if not text:
                continue
            write_message({"type": "insert_text", "text": text})
            logger.info("forwarded insert_request (%d chars) to extension", len(text))
            try:
                p.unlink()
            except OSError:
                pass
        except (json.JSONDecodeError, OSError) as e:
            logger.debug("insert watch: %s", e)
