# From: claude_backend/auto_inject.py:97
# Write `text` to `path` atomically: temp file + os.replace.

def _atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Write `text` to `path` atomically: temp file + os.replace.

    On any exception, removes the temp file before re-raising. The target
    file is left untouched if the write fails partway.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(text, encoding=encoding)
        os.replace(tmp, path)
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
