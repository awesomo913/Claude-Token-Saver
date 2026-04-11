# From: claude_backend/generators/snippet_library.py:108

def _build_index(
    utilities: list[CodeBlock],
    classes: list[CodeBlock],
    patterns: list[CodeBlock],
) -> str:
    lines = ["# Snippet Library\n"]

    if utilities:
        lines.append("## Utilities\n")
        for block in utilities[:30]:
            doc = ""
            if block.docstring:
                doc = f" -- {block.docstring.split(chr(10))[0].strip()}"
            lines.append(f"- [`{block.name}`](utilities/{_safe_name(block.name)}.py)"
                        f" (from `{block.file_path}:{block.start_line}`){doc}")
        lines.append("")

    if classes:
        lines.append("## Classes\n")
        for block in classes[:20]:
            doc = ""
            if block.docstring:
                doc = f" -- {block.docstring.split(chr(10))[0].strip()}"
            lines.append(f"- [`{block.name}`](classes/{_safe_name(block.name)}.py)"
                        f" (from `{block.file_path}:{block.start_line}`){doc}")
        lines.append("")

    if patterns:
        lines.append("## Patterns\n")
        for block in patterns[:15]:
            doc = ""
            if block.docstring:
                doc = f" -- {block.docstring.split(chr(10))[0].strip()}"
            lines.append(f"- [`{block.name}`](patterns/{_safe_name(block.name)}.py)"
                        f" (from `{block.file_path}:{block.start_line}`){doc}")
        lines.append("")

    return "\n".join(lines)
