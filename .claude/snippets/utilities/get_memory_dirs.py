# From: claude_backend/generators/memory_files.py:34
# Return (claude_code_memory_dir, project_memory_dir).

def get_memory_dirs(project_path: Path) -> tuple[Path, Path]:
    """Return (claude_code_memory_dir, project_memory_dir)."""
    slug = compute_project_slug(project_path)
    claude_code_dir = Path.home() / ".claude" / "projects" / slug / "memory"
    project_dir = project_path / ".claude" / "memory"
    return claude_code_dir, project_dir
