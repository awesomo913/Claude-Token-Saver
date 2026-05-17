# From: claude_backend/config.py:85
# Convert a dict to ScanConfig, ignoring unknown keys.

def _dict_to_config(data: dict) -> ScanConfig:
    """Convert a dict to ScanConfig, ignoring unknown keys."""
    known = {f.name for f in ScanConfig.__dataclass_fields__.values()}
    filtered = {k: v for k, v in data.items() if k in known}
    return ScanConfig(**filtered)
