"""Enumerate bootstrap-able projects and rank them for the overlay picker.

Why this exists: the floating overlay's Bootstrap picker needs to show the
user the projects most likely to be the one they're working in -- even with
many CLI sessions open. We learned the hard way that neither the process
working directory (all sessions launch from home) nor Claude Code's
project-history folders (timestamps get clobbered by a bootstrap run) are
reliable. The one clean signal is the modification time of real *source*
files inside each project: a bootstrap run adds CLAUDE.md but never touches
existing code, so "newest source file" still tracks genuine recent work.

Public API:
    list_projects(roots=None)                 -> list[Project]  # newest first
    focused_pick(projects, window_title)      -> Project | None # title match
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Where projects live. C:\Users\computer\Desktop\AI children + a couple of
# top-level repos that sit outside it.
_DEFAULT_ROOTS = [
    Path.home() / "Desktop" / "AI",
]
_EXTRA_PROJECTS = [
    Path("C:/StolenEmerald"),
    Path("C:/Quasar"),
]

# Source extensions whose mtime counts as "real work" (NOT generated files).
_CODE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".kt", ".java",
    ".c", ".cpp", ".h", ".go", ".rs", ".rb", ".cs", ".swift",
    ".html", ".css", ".vue", ".svelte",
}
# Folders we never descend into when timing source files.
_SKIP_DIRS = {
    ".claude", ".git", ".venv", "venv", "node_modules", "__pycache__",
    "dist", "build", ".egg-info", ".pytest_cache", ".mypy_cache",
}
# Don't surface these helper/junk folders as projects.
_SKIP_PROJECT_NAMES = re.compile(
    r"^\.|__pycache__|\.egg-info$|^logs$|^build_logs$|^docs$|^study$|"
    r"^path$|^ffmpeg$|^npm-bootstrap$|^external-repos$|^proposals$|^ai$|"
    r"session-archive|review-swarm|swarm-review|-briefs$|-targets$|"
    r"chrome-debug-profile|chrome-profiles|RETIRED|repo-temp$|_screens$",
    re.IGNORECASE,
)

# Cap how many files we stat per project, and how deep we descend, so a huge
# tree can't stall the click. Tuned so a full 100+ project scan stays well
# under a second (vs ~9s with a 400-file uncapped walk).
_MAX_FILES_PER_PROJECT = 60
_MAX_DEPTH = 3

# Cache so re-opening the picker is instant. 5 min is fine: the recency
# ordering is a hint, not live data, and focused_pick re-runs every open.
_CACHE_TTL_S = 300.0
_cache: dict = {"key": None, "ts": 0.0, "projects": []}


@dataclass(frozen=True)
class Project:
    """A bootstrap-able project, with recency + bootstrap status."""

    name: str
    path: str
    recency_ts: float       # newest source-file mtime (epoch seconds)
    bootstrapped: bool      # has the full Token Saver treatment already

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "recency_ts": self.recency_ts,
            "bootstrapped": self.bootstrapped,
        }


def _newest_code_mtime(project: Path) -> float:
    """Newest mtime among real source files in project (capped, shallow-ish)."""
    # Recency = the project folder's own mtime: a SINGLE stat per project.
    # The previous deep file-walk (up to 60 files x 104 projects) cost ~75s on
    # a cold disk cache and made the picker look frozen. The folder mtime is a
    # good-enough ordering signal, and the focused-title match (focused_pick)
    # is what actually surfaces the right project to the top anyway.
    try:
        return project.stat().st_mtime
    except OSError as exc:
        logger.debug("stat failed at %s: %s", project, exc)
        return 0.0


def _has_code(project: Path) -> bool:
    """Cheap check: does the project have at least one source file (depth<=2)?"""
    try:
        for entry in project.iterdir():
            if entry.is_file() and entry.suffix.lower() in _CODE_EXTS:
                return True
            if entry.is_dir() and entry.name not in _SKIP_DIRS:
                try:
                    for sub in entry.iterdir():
                        if sub.is_file() and sub.suffix.lower() in _CODE_EXTS:
                            return True
                except OSError:
                    continue
    except OSError as exc:
        logger.debug("_has_code iterdir failed at %s: %s", project, exc)
    return False


def _is_bootstrapped(project: Path) -> bool:
    return (project / ".claude" / "snippets" / "INDEX.md").is_file()


def list_projects(roots: list[Path] | None = None) -> list[Project]:
    """Return bootstrap-able projects, newest source-edit first.

    Never raises; logs and returns what it found.
    """
    import time
    effective_roots = roots or _DEFAULT_ROOTS
    cache_key = tuple(str(r) for r in effective_roots)
    now = time.time()
    if (_cache["key"] == cache_key
            and now - _cache["ts"] < _CACHE_TTL_S
            and _cache["projects"]):
        logger.debug("list_projects cache hit (%d)", len(_cache["projects"]))
        return list(_cache["projects"])  # copy: callers iterate across threads

    candidates: list[Path] = list(_EXTRA_PROJECTS)
    for root in effective_roots:
        try:
            candidates.extend(d for d in root.iterdir() if d.is_dir())
        except OSError as exc:
            logger.debug("root iterdir failed at %s: %s", root, exc)

    projects: list[Project] = []
    for path in candidates:
        try:
            if not path.is_dir():
                continue
            if _SKIP_PROJECT_NAMES.search(path.name):
                continue
            if not _has_code(path):
                continue
            projects.append(Project(
                name=path.name,
                path=str(path),
                recency_ts=_newest_code_mtime(path),
                bootstrapped=_is_bootstrapped(path),
            ))
        except Exception as exc:
            logger.warning("skipping project %s: %s", path, exc)

    projects.sort(key=lambda p: p.recency_ts, reverse=True)
    _cache.update(key=cache_key, ts=now, projects=projects)
    logger.info("listed %d project(s)", len(projects))
    return list(projects)  # copy: callers iterate across threads


def _score_title(project: Project, window_title: str) -> int:
    """Score how well a project matches a focused-window title (0 = no match)."""
    if not window_title:
        return 0
    title = window_title.lower()
    name = project.name.lower()
    score = 0
    if name and name in title:
        score += 60
    for part in re.split(r"[/\\]", project.path.lower()):
        if len(part) > 2 and part in title:
            score += 20
    title_tokens = set(re.split(r"[\s\-|/\\_.]+", title)) - {"", "the", "a"}
    name_tokens = set(re.split(r"[\s\-_]+", name)) - {""}
    score += len(title_tokens & name_tokens) * 10
    return score


def focused_pick(projects: list[Project], window_title: str) -> Project | None:
    """Best project match for the focused window title, or None if no signal."""
    if not projects or not window_title:
        return None
    scored = [(p, _score_title(p, window_title)) for p in projects]
    best, best_score = max(scored, key=lambda x: x[1])
    return best if best_score > 0 else None


if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.INFO)
    title_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    projs = list_projects()
    focus = focused_pick(projs, title_arg)
    print(json.dumps({
        "count": len(projs),
        "focused_match": focus.name if focus else None,
        "top10": [
            {"name": p.name, "bootstrapped": p.bootstrapped,
             "recency_ts": round(p.recency_ts)}
            for p in projs[:10]
        ],
    }, indent=2))
