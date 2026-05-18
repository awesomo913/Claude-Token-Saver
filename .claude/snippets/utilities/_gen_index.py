# From: claude_backend/generators/memory_files.py:325
# Generate MEMORY.md index.

def _gen_index(files: dict[str, str]) -> str:
    """Generate MEMORY.md index."""
    lines = []
    file_descs = {
        "reference_architecture.md": "Module map and dependency graph",
        "reference_patterns.md": "Common code patterns and error handling",
        "reference_utilities.md": "Reusable functions with locations",
        "project_conventions.md": "Detected coding standards and rules",
    }
    for filename, desc in file_descs.items():
        if filename in files:
            lines.append(f"- [{filename.replace('.md', '').replace('_', ' ').title()}]({filename}) -- {desc}")

    return "\n".join(lines) + "\n"
