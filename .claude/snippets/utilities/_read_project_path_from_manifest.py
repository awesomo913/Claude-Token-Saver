# From: claude_backend/http_server.py:138
# Recover the original project root for a Token-Saver-bootstrapped slug.

def _read_project_path_from_manifest(memory_dir: Path) -> str | None:
    """Recover the original project root for a Token-Saver-bootstrapped slug.

    Strategy (in order):

    1. Read `origin.txt` (sibling of memory/). Authoritative source written
       by `memory_files.write_memory_files`. Has been written since v0.2;
       older bootstraps don't have it (fall through to step 2).
    2. Walk the filesystem to disambiguate the slug (handles paths with
       internal dashes OR spaces, which the older `.replace('-', os.sep)`
       could not). Returns the candidate ONLY if its
       `.claude/manifest.jsonl` exists. On success, also writes
       origin.txt so subsequent calls hit step 1.
    3. Give up — return None. /projects still lists the project by slug name
       but the picker can't use it for context until next prep regenerates.
    """
    slug_dir = memory_dir.parent
    slug = slug_dir.name
    if not slug:
        return None

    # 1. Authoritative: origin.txt
    origin = slug_dir / "origin.txt"
    if origin.is_file():
        try:
            txt = origin.read_text(encoding="utf-8").strip()
            if txt and Path(txt).is_dir():
                return txt
        except OSError as e:
            logger.debug(
                "origin.txt read failed for %s (will fall through "
                "to filesystem walk): %s", slug_dir.name, e,
            )

    # 2. Walk the filesystem to disambiguate.
    cp = _resolve_slug_filesystem_walk(slug)
    if cp is not None and (cp / ".claude" / "manifest.jsonl").is_file():
        real = str(cp)
        _cache_origin_txt(slug_dir, real)
        return real

    return None
