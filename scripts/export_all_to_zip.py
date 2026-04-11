#!/usr/bin/env python3
"""Export all current project files to a single zip on the Desktop.

Includes claude_backend, tests, scripts, and top-level config/examples.
This is a best-effort snapshot of the workspace for offline review.
"""
import os
import shutil
from pathlib import Path


def main():
    # Discover repo root (two levels up from this file: scripts/ -> repo root)
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent

    # Desktop path (Windows user home)
    user_home = Path(os.environ.get("USERPROFILE", str(Path.home())))
    desktop = user_home / "Desktop"
    zip_base = desktop / "gemini_coder_web_export"
    zip_path = zip_base.with_suffix(".zip")

    # Remove existing export if present
    if zip_path.exists():
        zip_path.unlink()

    print(f"Exporting workspace at {repo_root} to {zip_path}...")
    shutil.make_archive(str(zip_base), "zip", str(repo_root))
    print(f"Export complete: {zip_path}")


if __name__ == "__main__":
    main()
