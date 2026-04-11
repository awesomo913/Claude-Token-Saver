"""Optional GitHub scanner for pulling code from public repos."""

from __future__ import annotations

import json
import logging
import urllib.request
from urllib.error import HTTPError, URLError
from typing import Optional

from ..types import FileEntry

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


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


def _list_repos(
    name: str, s_type: str, max_repos: int, token: Optional[str]
) -> list[dict]:
    """Fetch repo list for a user or org."""
    if s_type not in ("user", "organization"):
        s_type = "user"
    url = f"{GITHUB_API}/{s_type}s/{name}/repos?per_page={max_repos}"
    data = _fetch_json(url, token)
    return data if isinstance(data, list) else []


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


def _fetch_json(url: str, token: Optional[str] = None) -> object:
    """Fetch JSON from a URL with optional auth token."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "claude-token-saver")
    if token:
        req.add_header("Authorization", f"token {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError, OSError) as e:
        logger.debug("GitHub API error for %s: %s", url, e)
        return None


def _download(url: str) -> Optional[str]:
    """Download file content as string."""
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, OSError) as e:
        logger.debug("Download failed %s: %s", url, e)
        return None
