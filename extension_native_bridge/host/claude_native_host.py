#!/usr/bin/env python3
"""
Chrome Native Messaging host: length-prefixed JSON on stdin/stdout (4-byte little-endian len + UTF-8).

Pairs with extension_native_bridge/extension/ — no CDP, no debug port.

Drop a file named insert_request.json into the data directory to push text into the page:
  {"text": "your context here"}
The host forwards it to the extension as {"type": "insert_text", "text": "..."}.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import struct
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# Native Messaging allows host-initiated frames; only one writer at a time.
_write_lock = threading.Lock()

# Windows: APPDATA\claude_token_saver\extension_bridge
if sys.platform == "win32":
    _base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
else:
    _base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

DATA_DIR = _base / "claude_token_saver" / "extension_bridge"
LOG_FILE = DATA_DIR / "bridge.log"
MD_LOG = DATA_DIR / "claude_messages.md"
SQLITE_PATH = DATA_DIR / "messages.sqlite"
INSERT_FILE = DATA_DIR / "insert_request.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("claude_native_host")


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(fh)
    except OSError as e:
        logger.warning("Could not attach file log: %s", e)


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


def write_message(obj: dict) -> None:
    """Send one frame to Chrome."""
    j = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    with _write_lock:
        sys.stdout.buffer.write(struct.pack("<I", len(j)))
        sys.stdout.buffer.write(j)
        sys.stdout.buffer.flush()


def init_sqlite() -> None:
    with sqlite3.connect(SQLITE_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assistant_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                url TEXT,
                title TEXT,
                text TEXT NOT NULL
            )
            """
        )
        conn.commit()


def handle_incoming(msg: dict) -> None:
    t = msg.get("type")
    if t == "ping":
        logger.info("ping from extension (%s)", msg.get("source", "?"))
        return
    if t != "assistant_message":
        logger.debug("ignored message type: %s", t)
        return

    text = (msg.get("text") or "").strip()
    if not text:
        return

    ts = msg.get("ts") or datetime.now(timezone.utc).isoformat()
    url = msg.get("url") or ""
    title = msg.get("title") or ""

    block = f"\n\n---\n**{ts}** — {title}\n\n{text}\n"
    try:
        with open(MD_LOG, "a", encoding="utf-8") as f:
            f.write(block)
    except OSError as e:
        logger.error("append markdown failed: %s", e)

    try:
        with sqlite3.connect(SQLITE_PATH) as conn:
            conn.execute(
                "INSERT INTO assistant_messages (ts, url, title, text) VALUES (?,?,?,?)",
                (ts, url, title, text),
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.error("sqlite insert failed: %s", e)

    logger.info("saved assistant message (%d chars)", len(text))


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


def main() -> int:
    ensure_data_dir()
    init_sqlite()
    logger.info("claude_native_host started; data dir: %s", DATA_DIR)
    if sys.stdout is None or not hasattr(sys.stdout.buffer, "write"):
        logger.error("stdout must be a binary stream for native messaging")
        return 1

    stop = threading.Event()
    t = threading.Thread(target=watch_insert_file, args=(stop,), daemon=True)
    t.start()

    try:
        while True:
            msg = read_message()
            if msg is None:
                break
            try:
                handle_incoming(msg)
            except Exception as e:  # noqa: BLE001 — keep host alive
                logger.exception("handler error: %s", e)
    finally:
        stop.set()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
