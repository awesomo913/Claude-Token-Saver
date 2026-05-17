# From: claude_backend/prefs.py:80
# Persist prefs atomically. Returns True on success.

    def save(self) -> bool:
        """Persist prefs atomically. Returns True on success."""
        try:
            PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
            text = json.dumps(asdict(self), indent=2)
            tmp = PREFS_PATH.with_suffix(PREFS_PATH.suffix + ".tmp")
            try:
                tmp.write_text(text, encoding="utf-8")
                os.replace(tmp, PREFS_PATH)
            except OSError:
                # Clean up temp file if rename failed.
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass
                raise
            return True
        except OSError as e:
            logger.warning("prefs save failed: %s", e)
            return False
