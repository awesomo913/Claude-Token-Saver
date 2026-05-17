# From: claude_backend/cli.py:418
# Print a human-readable analysis report.

def _print_analysis(analysis) -> None:
    """Print a human-readable analysis report."""
    print(f"\n=== Project: {analysis.name} ===")
    print(f"Path: {analysis.root}")
    print(f"Files: {len(analysis.files)}")

    if analysis.language_stats:
        print("\nLanguages:")
        for ext, count in list(analysis.language_stats.items())[:10]:
            print(f"  {ext}: {count}")

    if analysis.entry_points:
        print(f"\nEntry points: {', '.join(analysis.entry_points[:5])}")

    if analysis.dependencies:
        print(f"Dependencies: {', '.join(analysis.dependencies[:10])}")

    if analysis.key_files:
        print(f"Key files: {', '.join(analysis.key_files)}")

    print(f"\nModules: {len(analysis.modules)}")
    print(f"Code blocks: {len(analysis.blocks)}")

    conv = analysis.conventions
    if conv.samples_analyzed > 0:
        print(f"\nConventions ({conv.samples_analyzed} files sampled):")
        print(f"  Path handling: {conv.path_style}")
        print(f"  Type hints: {conv.type_hints}")
        print(f"  Formatting: {conv.string_format}")
        print(f"  Error handling: {conv.error_handling}")
        print(f"  Logging: {conv.logging_style}")
        print(f"  Imports: {conv.import_style}")
