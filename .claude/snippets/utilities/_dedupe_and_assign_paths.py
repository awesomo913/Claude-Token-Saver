# From: claude_backend/generators/snippet_library.py:207
# Collapse content-duplicates and assign collision-safe filenames.

def _dedupe_and_assign_paths(
    blocks: list[CodeBlock], subdir: str,
) -> list[tuple[CodeBlock, str]]:
    """Collapse content-duplicates and assign collision-safe filenames.

    Two stages:
      1. Dedupe by (name, source-stripped). Prefer the block whose
         file_path is shorter (less nested = more canonical).
      2. Assign `<subdir>/<safe_name>.py` to each kept block. On
         collision, prefix with parent dir (`<subdir>/<parent>__<name>.py`)
         and fall back to a numeric suffix for any residual clash.

    Preserves the original ordering of kept blocks so the cap-slice
    applied by the caller still sees blocks in traversal order.
    """
    # Pass 1: dedupe — last writer wins for same shape, but we re-check
    # which file_path is shorter, so canonical location is kept.
    canonical: dict[tuple[str, str], CodeBlock] = {}
    for b in blocks:
        key = (b.name, b.source.strip())
        existing = canonical.get(key)
        if existing is None or len(b.file_path) < len(existing.file_path):
            canonical[key] = b
    kept_ids = {id(b) for b in canonical.values()}
    deduped = [b for b in blocks if id(b) in kept_ids]

    # Pass 2: assign safe paths with collision disambiguation.
    out: list[tuple[CodeBlock, str]] = []
    used: set[str] = set()
    for b in deduped:
        base = _safe_name(b.name)
        path = f"{subdir}/{base}.py"
        if path in used:
            parent = PurePosixPath(b.file_path.replace("\\", "/")).parent.name or "_root"
            parent_safe = _safe_name(parent)
            path = f"{subdir}/{parent_safe}__{base}.py"
            n = 2
            while path in used:
                path = f"{subdir}/{parent_safe}__{base}_{n}.py"
                n += 1
        used.add(path)
        out.append((b, path))
    return out
