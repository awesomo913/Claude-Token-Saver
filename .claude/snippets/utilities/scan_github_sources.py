# From: claude_backend/scanners/github.py:18
# Scan configured GitHub sources and return FileEntry list.

def scan_github_sources(
    sources: list[dict],
    token: str = "",
) -> list[FileEntry]:
    """Scan configured GitHub sources and return FileEntry list.

    Each source dict:
        name: GitHub user or org name
        type: "user" or "organization"
        max_repos: max repos to scan (default 3)
        extensions: list of file extensions to include
    """
    entries: list[FileEntry] = []
    for src in sources:
        name = src.get("name", "")
        s_type = src.get("type", "user")
        max_repos = int(src.get("max_repos", 3))
        extensions = src.get("extensions", [".py", ".js", ".ts", ".md"])
        if not name:
            continue

        repos = _list_repos(name, s_type, max_repos, token or None)
        for repo in repos:
            owner = repo.get("owner", {}).get("login", name)
            repo_name = repo.get("name", "")
            if not repo_name:
                continue
            files = _scan_repo(owner, repo_name, extensions, token=token or None)
            entries.extend(files)
            logger.info("GitHub: %s/%s -> %d files", owner, repo_name, len(files))

    return entries
