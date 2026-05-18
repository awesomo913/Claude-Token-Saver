# From: claude_backend/generators/snippet_library.py:23
# Generate snippet files organized by category.

def generate_snippet_library(
    analysis: ProjectAnalysis,
    max_lines: int = 100,
) -> dict[str, str]:
    """Generate snippet files organized by category.

    Returns dict of relative_path -> content for all snippets + INDEX.md.
    """
    snippets: dict[str, str] = {}
    utilities: list[CodeBlock] = []
    classes: list[CodeBlock] = []
    patterns: list[CodeBlock] = []

    # "method" was excluded prior to 2026-05 — class-heavy projects
    # (e.g. claude_backend itself) had ZERO indexed coverage. Grader
    # bottomed out at 30% hit rate on this project as a result.
    # Include methods alongside free functions so retrieval sees them.
    _CALLABLE_KINDS = ("function", "async_function", "method")
    # Private underscore-prefix filter dropped, since codebases like
    # this one use _handle_pending / _show_picker / _copy_context as
    # the main internal API — exactly what users ask about.
    for block in analysis.blocks:
        lines = block.end_line - block.start_line + 1
        # Skip very small blocks (one-liners aren't useful snippets).
        if lines < 3:
            continue

        # Two separate size budgets: classes get 150 (full small classes
        # stay readable), callables get max_lines (default 50). The
        # previous code applied max_lines as a single gate up top, which
        # silently dropped every 50<lines<=150 class — including
        # TokenTracker, OverlayButton, SearchIndex.
        if block.kind == "class" and lines <= 150:
            classes.append(block)
        elif block.kind in _CALLABLE_KINDS and lines <= max_lines and block.docstring:
            utilities.append(block)
        elif block.kind in _CALLABLE_KINDS and lines <= max_lines and _is_pattern(block):
            patterns.append(block)

    # Dedupe + assign collision-safe filenames BEFORE applying the cap.
    # Without this, ~half the utilities pool is gemini_coder_web/* copies
    # of root-level files (browser_actions.py, broadcast.py etc.) that
    # crowd out unique symbols like build_menu and generate_memory_files.
    # Filename collisions also silently overwrote distinct callables
    # sharing a short name (`main`, `load`, `save`).
    # Cap utilities at 350 (was 250). After dedup recovered ~100 slots,
    # there's still a 435-callable pool and useful symbols like
    # build_menu (pos 305) + generate_memory_files (pos 328) sat past
    # the old cap. 350 covers them with headroom; smart_search inverted
    # index still O(candidates), well under perf thresholds.
    utility_writes = _dedupe_and_assign_paths(utilities, "utilities")[:350]
    class_writes = _dedupe_and_assign_paths(classes, "classes")[:100]
    pattern_writes = _dedupe_and_assign_paths(patterns, "patterns")[:100]

    # Docstring header MUST be written for every kind. load_snippet_library
    # reads the second `# ...` line as block.docstring; without it, classes
    # and patterns round-trip as docstring=None, losing the ranker's
    # ×1.3 doc-length bonus and the doc-word match contributions.
    def _make(block: CodeBlock) -> str:
        header = f"# From: {block.file_path}:{block.start_line}\n"
        if block.docstring:
            header += f"# {block.docstring.split(chr(10))[0].strip()}\n"
        return header + "\n" + block.source

    for block, path in utility_writes:
        snippets[path] = _make(block)
    for block, path in class_writes:
        snippets[path] = _make(block)
    for block, path in pattern_writes:
        snippets[path] = _make(block)

    if snippets:
        snippets["INDEX.md"] = _build_index(
            utility_writes, class_writes, pattern_writes,
        )

    return snippets
