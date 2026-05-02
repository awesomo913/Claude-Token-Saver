# From: extension_native_bridge/host/claude_native_host.py:86

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
