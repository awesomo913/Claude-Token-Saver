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
    # Pass 1: dedupe — keep block with shortest file_path for each
    # (name, source-stripped) key. Track first-seen position of each
    # key in the input list so we can preserve traversal order in the
    # output. Previous version filtered the input via `id(b) in kept_ids`,
    # which silently dropped both copies if a caller passed two refs to
    # the same object — structurally fragile even though the current
    # scanner emits one block per source location.
    canonical: dict[tuple[str, str], CodeBlock] = {}
    first_seen: dict[tuple[str, str], int] = {}
    for i, b in enumerate(blocks):
        key = (b.name, b.source.strip())
        existing = canonical.get(key)
        if existing is None or len(b.file_path) < len(existing.file_path):
            canonical[key] = b
        if key not in first_seen:
            first_seen[key] = i
    deduped = [canonical[k] for k in sorted(canonical, key=first_seen.get)]

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
