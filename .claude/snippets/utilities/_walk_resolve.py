# From: claude_backend/http_server.py:90
# Recursive helper for `_resolve_slug_filesystem_walk`.

def _walk_resolve(prefix: Path, tokens: list[str]) -> Path | None:
    """Recursive helper for `_resolve_slug_filesystem_walk`.

    For each k from len(tokens) down to 1, take the first k tokens,
    join them with each candidate separator (`-`, ` `), and recurse if
    the resulting path exists on disk and is not a symlink.
    """
    if not tokens:
        return prefix
    for k in range(len(tokens), 0, -1):
        head = tokens[:k]
        rest = tokens[k:]
        for joiner in ("-", " "):
            cand = prefix / joiner.join(head)
            try:
                # Skip symlinks: a junction or symlink could lead the
                # walker outside the drive root and let a crafted slug
                # resolve to an arbitrary path on the system.
                if cand.is_symlink() or not cand.is_dir():
                    continue
            except OSError:
                continue
            resolved = _walk_resolve(cand, rest)
            if resolved is not None:
                return resolved
    return None
