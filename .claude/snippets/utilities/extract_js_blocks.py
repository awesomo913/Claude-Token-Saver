# From: claude_backend/analyzers/code_extractor.py:107
# Extract function and class blocks from JS/TS source.

def extract_js_blocks(source: str, file_path: str = "") -> list[CodeBlock]:
    """Extract function and class blocks from JS/TS source.

    Uses a string-literal-aware brace matcher to avoid being tricked
    by braces inside strings or comments.
    """
    blocks: list[CodeBlock] = []

    for match in _JS_DECL_RE.finditer(source):
        # Find the opening brace after the declaration
        pos = match.end()
        brace_pos = source.find("{", pos)
        if brace_pos == -1:
            continue

        end_pos = _find_matching_brace(source, brace_pos)
        if end_pos == -1:
            continue

        block_text = source[match.start():end_pos + 1].strip()
        start_line = source[:match.start()].count("\n") + 1
        end_line = source[:end_pos + 1].count("\n") + 1

        # Extract name from the declaration
        name = _extract_js_name(block_text)

        blocks.append(CodeBlock(
            name=name,
            kind="js_function",
            source=block_text,
            start_line=start_line,
            end_line=end_line,
            file_path=file_path,
        ))

    return blocks
