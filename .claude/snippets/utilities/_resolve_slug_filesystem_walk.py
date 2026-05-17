# From: claude_backend/http_server.py:60
# Decode a Claude Code slug to a real path by walking the filesystem.

def _resolve_slug_filesystem_walk(slug: str) -> Path | None:
    """Decode a Claude Code slug to a real path by walking the filesystem.

    Slugs collapse `\\`, ` ` (space), and literal `-` all to `-`, so a
    slug like `C--Users-computer-Desktop-AI-claude-interaction-tool`
    can decode to many candidates. Naive `replace('-', '\\')` only
    finds one — we walk the disk and pick whichever exists.

    Strategy: at each prefix, try the longest token-merge first. For
    each merge, try both `-` and ` ` joiners (both are encoded the
    same way). Returns None if no chain of existing directories spells
    out the slug.

    Symlinks are skipped — they could escape the drive root and let a
    crafted slug resolve to an arbitrary path. Recursion depth is
    capped to keep adversarial slugs from raising RecursionError.
    """
    if len(slug) < 3 or slug[1:3] != "--":
        return None
    drive_root = Path(f"{slug[0]}:" + os.sep)
    if not drive_root.exists():
        return None
    tokens = slug[3:].split("-")
    if not tokens or not all(tokens):
        return None
    if len(tokens) > _SLUG_RESOLVE_MAX_DEPTH:
        return None
    return _walk_resolve(drive_root, tokens)
