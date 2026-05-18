# From: claude_backend/generators/memory_files.py:42
# Generate all memory file contents as a dict of filename -> content.

def generate_memory_files(analysis: ProjectAnalysis) -> dict[str, str]:
    """Generate all memory file contents as a dict of filename -> content."""
    files: dict[str, str] = {}

    files["reference_architecture.md"] = _gen_architecture(analysis)
    files["reference_patterns.md"] = _gen_patterns(analysis)
    files["reference_utilities.md"] = _gen_utilities(analysis)
    files["project_conventions.md"] = _gen_conventions(analysis)
    hot = _gen_hot_functions(analysis)
    if hot:
        files["hot_functions.md"] = hot
    files["MEMORY.md"] = _gen_index(files)

    return files
