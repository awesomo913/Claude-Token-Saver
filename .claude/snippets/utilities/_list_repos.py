# From: claude_backend/scanners/github.py:52
# Fetch repo list for a user or org.

def _list_repos(
    name: str, s_type: str, max_repos: int, token: Optional[str]
) -> list[dict]:
    """Fetch repo list for a user or org."""
    if s_type not in ("user", "organization"):
        s_type = "user"
    url = f"{GITHUB_API}/{s_type}s/{name}/repos?per_page={max_repos}"
    data = _fetch_json(url, token)
    return data if isinstance(data, list) else []
