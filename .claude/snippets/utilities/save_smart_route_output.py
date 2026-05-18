# From: auto_save.py:89
# Save combined Smart Route results (free + claude) as one file.

def save_smart_route_output(
    title: str,
    free_output: str,
    free_ai_name: str,
    claude_output: str,
    claude_ai_name: str,
    classification_summary: str,
    elapsed_seconds: float = 0,
    download_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Save combined Smart Route results (free + claude) as one file."""
    if not free_output and not claude_output:
        return None

    if download_dir is None:
        download_dir = Path.home() / "Downloads"
    download_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = _sanitize_filename(title)
    filename = f"SmartRoute_{safe_title}_{timestamp}.txt"
    filepath = download_dir / filename

    lines = [
        f"# Smart Route Results",
        f"# Task: {title}",
        f"# Classification: {classification_summary}",
        f"# Completed: {datetime.now().isoformat()}",
        f"# Duration: {elapsed_seconds:.0f} seconds",
        "# ---",
        "",
    ]

    if free_output:
        lines.extend([
            f"## FREE MODEL ({free_ai_name})",
            f"## {'='*50}",
            "",
            free_output,
            "",
        ])

    if claude_output:
        lines.extend([
            f"## CLAUDE ({claude_ai_name})",
            f"## {'='*50}",
            "",
            claude_output,
        ])

    try:
        filepath.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Saved smart route output: %s", filepath)
        return filepath
    except Exception as e:
        logger.error("Failed to save smart route output: %s", e)
        return None
