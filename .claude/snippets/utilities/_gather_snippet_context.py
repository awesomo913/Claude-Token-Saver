# From: claude_backend/http_server.py:298
# Search the project's snippet library, format top matches as code_context.

def _gather_snippet_context(
    project_path: str, query: str,
) -> tuple[str, int, int]:
    """Search the project's snippet library, format top matches as code_context.

    Returns (code_context, injected_blocks, injected_tokens). All zeros if
    the library is absent or no match clears the search threshold.
    """
    if not project_path:
        return "", 0, 0
    try:
        from .generators.snippet_library import load_snippet_library
        from .search import smart_search
        from .tokenizer import count_tokens
    except Exception as e:
        logger.warning("snippet imports failed: %s", e)
        return "", 0, 0

    base = Path(project_path) / ".claude" / "snippets"
    try:
        blocks = load_snippet_library(base)
    except Exception as e:
        logger.warning("load_snippet_library failed for %s: %s", base, e)
        return "", 0, 0
    if not blocks:
        return "", 0, 0

    try:
        ranked = smart_search(blocks, query, max_results=SNIPPET_TOP_K)
    except Exception as e:
        logger.warning("smart_search failed: %s", e)
        return "", 0, 0
    if not ranked:
        return "", 0, 0

    sections: list[str] = []
    injected_blocks = 0
    injected_tokens = 0
    for _score, block in ranked:
        header = f"# From: {block.file_path}:{block.start_line}"
        section = f"{header}\n{block.source}"
        try:
            section_tokens = count_tokens(section)
        except Exception as e:
            logger.warning(
                "count_tokens failed for snippet %s, skipping: %s", block.name, e,
            )
            continue
        if injected_tokens + section_tokens > SNIPPET_TOKEN_BUDGET:
            continue
        sections.append(section)
        injected_blocks += 1
        injected_tokens += section_tokens

    return "\n\n".join(sections), injected_blocks, injected_tokens
