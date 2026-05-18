# From: claude_backend/generators/snippet_library.py:252

def _build_index(
    utility_writes: list[tuple[CodeBlock, str]],
    class_writes: list[tuple[CodeBlock, str]],
    pattern_writes: list[tuple[CodeBlock, str]],
) -> str:
    lines = ["# Snippet Library\n"]

    def _section(title: str, writes: list[tuple[CodeBlock, str]]) -> None:
        if not writes:
            return
        lines.append(f"## {title}\n")
        for block, path in writes:
            doc = ""
            if block.docstring:
                doc = f" -- {block.docstring.split(chr(10))[0].strip()}"
            lines.append(
                f"- [`{block.name}`]({path})"
                f" (from `{block.file_path}:{block.start_line}`){doc}"
            )
        lines.append("")

    _section("Utilities", utility_writes)
    _section("Classes", class_writes)
    _section("Patterns", pattern_writes)

    return "\n".join(lines)
