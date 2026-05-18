# From: claude_backend/scanners/project.py:142
# Fast scan that only returns {relative_path: mtime} without reading content.

def scan_project_fast_mtimes(root: Path, config: ScanConfig) -> dict[str, float]:
    """Fast scan that only returns {relative_path: mtime} without reading content.

    Used by auto-scan to detect changes without re-reading all files.
    ~10x faster than full scan on large repos.
    """
    root = root.resolve()
    if not root.is_dir():
        return {}

    ext_set = set(config.extensions)
    exact_ignore = set()
    glob_suffixes: list[str] = []
    for pat in config.ignore_dirs:
        if pat.startswith("*"):
            glob_suffixes.append(pat[1:])
        else:
            exact_ignore.add(pat)

    root_str = str(root)
    mtimes: dict[str, float] = {}
    stack: list[str] = [root_str]

    while stack:
        current = stack.pop()
        try:
            scanner = os.scandir(current)
        except (PermissionError, OSError):
            continue
        with scanner:
            for item in scanner:
                name = item.name
                if item.is_dir(follow_symlinks=False):
                    if name in exact_ignore:
                        continue
                    if any(name.endswith(suf) for suf in glob_suffixes):
                        continue
                    if name.startswith(".") and name not in (".", ".claude"):
                        continue
                    stack.append(item.path)
                    continue
                if not item.is_file(follow_symlinks=False):
                    continue
                dot_idx = name.rfind(".")
                if dot_idx <= 0:
                    continue
                if name[dot_idx:] not in ext_set:
                    continue
                try:
                    st = item.stat()
                    rel = os.path.relpath(item.path, root_str).replace("\\", "/")
                    mtimes[rel] = st.st_mtime
                except (OSError, ValueError):
                    continue

    return mtimes
