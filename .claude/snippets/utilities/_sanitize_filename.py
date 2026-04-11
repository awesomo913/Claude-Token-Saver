# From: auto_save.py:13
# Make a string safe for use as a filename.

def _sanitize_filename(name: str, max_len: int = 60) -> str:
    """Make a string safe for use as a filename."""
    clean = re.sub(r'[<>:"/\\|?*]', '_', name)
    clean = re.sub(r'\s+', '_', clean)
    clean = re.sub(r'_+', '_', clean)
    clean = clean.strip('_.')
    return clean[:max_len] if clean else "task_output"
