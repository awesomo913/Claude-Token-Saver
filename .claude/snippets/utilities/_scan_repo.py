# From: claude_backend/scanners/github.py:63
# Scan a single repo's contents.

def _scan_repo(
    owner: str,
    repo: str,
    extensions: list[str],
    token: Optional[str] = None,
    max_files: int = 40,
) -> list[FileEntry]:
    """Scan a single repo's contents."""
    entries: list[FileEntry] = []
    ext_set = set(extensions)
    stack = [f"{GITHUB_API}/repos/{owner}/{repo}/contents/"]

    while stack and len(entries) < max_files:
        url = stack.pop()
        data = _fetch_json(url, token)
        if not isinstance(data, list):
            continue

        for item in data:
            if len(entries) >= max_files:
                break
            itype = item.get("type", "")
            path = item.get("path", "")
            name = item.get("name", "")

            if itype == "dir":
                stack.append(item.get("url", ""))
            elif itype == "file":
                ext = ""
                for e in ext_set:
                    if name.endswith(e):
                        ext = e
                        break
                if not ext:
                    continue

                dl_url = item.get("download_url", "")
                if not dl_url:
                    continue

                content = _download(dl_url)
                if content is None:
                    continue

                entries.append(FileEntry(
                    path=f"{owner}/{repo}/{path}",
                    content=content,
                    ext=ext,
                    source=f"github:{owner}/{repo}",
                ))

    return entries
