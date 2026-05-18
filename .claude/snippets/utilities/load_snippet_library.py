# From: claude_backend/generators/snippet_library.py:127
# Read .claude/snippets/*/*.py back into CodeBlocks for search.

def load_snippet_library(base: Path) -> list[CodeBlock]:
    """Read .claude/snippets/*/*.py back into CodeBlocks for search.

    Inverse of write_snippet_library. Each file has a "# From: path:line"
    header (optionally followed by "# <docstring>") and then source.
    Returns [] if base missing or no parseable files. Never raises.
    """
    if not base.is_dir():
        return []

    blocks: list[CodeBlock] = []
    for sub in ("utilities", "classes", "patterns"):
        kind = _KIND_BY_DIR[sub]
        sub_dir = base / sub
        if not sub_dir.is_dir():
            continue
        for file in sorted(sub_dir.glob("*.py")):
            try:
                text = file.read_text(encoding="utf-8")
            except OSError as e:
                logger.warning("Cannot read snippet %s: %s", file, e)
                continue

            lines = text.splitlines()
            if not lines:
                continue

            header_match = _HEADER_RE.match(lines[0])
            if not header_match:
                logger.warning("Snippet %s missing '# From: ...' header, skipping", file)
                continue
            file_path = header_match.group(1).strip()
            try:
                start_line = int(header_match.group(2))
            except ValueError:
                logger.warning("Snippet %s has non-integer line in header, skipping", file)
                continue

            cursor = 1
            docstring: str | None = None
            if cursor < len(lines) and lines[cursor].startswith("#"):
                docstring = lines[cursor].lstrip("# ").strip() or None
                cursor += 1
            while cursor < len(lines) and not lines[cursor].strip():
                cursor += 1

            source = "\n".join(lines[cursor:]).rstrip()
            if not source:
                continue

            blocks.append(CodeBlock(
                name=file.stem,
                kind=kind,
                source=source,
                start_line=start_line,
                end_line=start_line + source.count("\n"),
                docstring=docstring,
                file_path=file_path,
            ))

    return blocks
