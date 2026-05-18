# From: claude_backend/analyzers/code_extractor.py:138
# Find the closing brace matching the one at open_pos.

def _find_matching_brace(source: str, open_pos: int) -> int:
    """Find the closing brace matching the one at open_pos.

    Tracks state to skip braces inside strings, template literals, and comments.
    """
    state = "normal"
    depth = 1
    i = open_pos + 1
    length = len(source)

    while i < length and depth > 0:
        ch = source[i]
        prev = source[i - 1] if i > 0 else ""

        if state == "normal":
            if ch == "/" and i + 1 < length:
                next_ch = source[i + 1]
                if next_ch == "/":
                    state = "line_comment"
                    i += 2
                    continue
                elif next_ch == "*":
                    state = "block_comment"
                    i += 2
                    continue
            if ch == '"':
                state = "double_quote"
            elif ch == "'":
                state = "single_quote"
            elif ch == "`":
                state = "template_literal"
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i

        elif state == "double_quote":
            if ch == '"' and prev != "\\":
                state = "normal"

        elif state == "single_quote":
            if ch == "'" and prev != "\\":
                state = "normal"

        elif state == "template_literal":
            if ch == "`" and prev != "\\":
                state = "normal"

        elif state == "line_comment":
            if ch == "\n":
                state = "normal"

        elif state == "block_comment":
            if ch == "/" and prev == "*":
                state = "normal"

        i += 1

    return -1
