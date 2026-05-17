# From: claude_backend/config.py:92
# Write a config example to disk.

def save_config_example(path: Path) -> None:
    """Write a config example to disk."""
    example = asdict(ScanConfig())
    path.write_text(
        json.dumps(example, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Wrote config example to %s", path)
