"""Auto-save task output to Downloads folder as .txt files."""

import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _sanitize_filename(name: str, max_len: int = 60) -> str:
    """Make a string safe for use as a filename."""
    clean = re.sub(r'[<>:"/\\|?*]', '_', name)
    clean = re.sub(r'\s+', '_', clean)
    clean = re.sub(r'_+', '_', clean)
    clean = clean.strip('_.')
    return clean[:max_len] if clean else "task_output"


def save_task_output(
    title: str,
    output: str,
    ai_name: str = "Unknown AI",
    corner: str = "",
    elapsed_seconds: float = 0,
    iterations: int = 0,
    download_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Save task output to ~/Downloads as a .txt file.

    Args:
        title: Task title (used in filename)
        output: The full code/text output
        ai_name: Which AI produced it
        corner: Which screen corner the session was in
        elapsed_seconds: How long the task took
        iterations: How many iterations completed
        download_dir: Override download directory (default: ~/Downloads)

    Returns:
        Path to the saved file, or None on failure.
    """
    if not output or not output.strip():
        logger.warning("No output to save for task: %s", title)
        return None

    if download_dir is None:
        download_dir = Path.home() / "Downloads"

    download_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = _sanitize_filename(title)
    safe_ai = _sanitize_filename(ai_name, max_len=20)
    safe_corner = _sanitize_filename(corner, max_len=15) if corner else ""
    if safe_corner:
        filename = f"{safe_ai}_{safe_corner}_{safe_title}_{timestamp}.txt"
    else:
        filename = f"{safe_ai}_{safe_title}_{timestamp}.txt"
    filepath = download_dir / filename

    # Build header
    header_lines = [
        f"# Task: {title}",
        f"# AI: {ai_name}",
    ]
    if corner:
        header_lines.append(f"# Session: {corner}")
    header_lines.extend([
        f"# Completed: {datetime.now().isoformat()}",
        f"# Duration: {elapsed_seconds:.0f} seconds",
        f"# Iterations: {iterations}",
        "# ---",
        "",
    ])
    header = "\n".join(header_lines)

    try:
        filepath.write_text(header + output, encoding="utf-8")
        logger.info("Saved task output: %s (%d chars)", filepath, len(output))
        return filepath
    except Exception as e:
        logger.error("Failed to save task output: %s", e)
        return None
