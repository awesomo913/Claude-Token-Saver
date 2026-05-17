"""Localhost HTTP backend — three thin clients funnel into one server.

Browser extension, Win32 overlay window, and global hotkey daemon all
POST captured prompts here. Server runs in tray process so it's always
available while the tray is up.

Endpoints:
  GET  /health     -> {ok: true, version}
  GET  /projects   -> [{slug, path, name, last_used_iso}] (max 10)
  POST /improve    -> {improved_prompt, token_savings_estimate, builder_opened}

Communication with GUI process is via a pending-file at
~/.claude/token_saver_pending.json. Server writes it; GUI polls for it
via tkinter.after() loop, loads the contents into the Builder tab,
then deletes the file. If GUI isn't running, server spawns it via the
same mechanism session_launcher uses.

Security:
  - Bound to 127.0.0.1 ONLY (never 0.0.0.0). Localhost-only access.
  - CORS strict to chrome-extension://* origins for browser ext.
  - No auth (it's a local-tool API).
"""

from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

PENDING_PATH = Path.home() / ".claude" / "token_saver_pending.json"
VERSION = "0.1.0"

# Module-level state for the running server. Tray creates one on boot.
_server: ThreadingHTTPServer | None = None
_server_thread: threading.Thread | None = None


# ── Project enumeration ─────────────────────────────────────────────

def _claude_projects_dir() -> Path:
    """Where Token Saver writes per-project memory files."""
    return Path.home() / ".claude" / "projects"


# Defensive cap so a malformed/very-deep slug can't blow Python's
# recursion limit. Real Claude Code slugs are well under this.
_SLUG_RESOLVE_MAX_DEPTH = 40


def _resolve_slug_filesystem_walk(slug: str) -> Path | None:
    """Decode a Claude Code slug to a real path by walking the filesystem.

    Slugs collapse `\\`, ` ` (space), and literal `-` all to `-`, so a
    slug like `C--Users-computer-Desktop-AI-claude-interaction-tool`
    can decode to many candidates. Naive `replace('-', '\\')` only
    finds one — we walk the disk and pick whichever exists.

    Strategy: at each prefix, try the longest token-merge first. For
    each merge, try both `-` and ` ` joiners (both are encoded the
    same way). Returns None if no chain of existing directories spells
    out the slug.

    Symlinks are skipped — they could escape the drive root and let a
    crafted slug resolve to an arbitrary path. Recursion depth is
    capped to keep adversarial slugs from raising RecursionError.
    """
    if len(slug) < 3 or slug[1:3] != "--":
        return None
    drive_root = Path(f"{slug[0]}:" + os.sep)
    if not drive_root.exists():
        return None
    tokens = slug[3:].split("-")
    if not tokens or not all(tokens):
        return None
    if len(tokens) > _SLUG_RESOLVE_MAX_DEPTH:
        return None
    return _walk_resolve(drive_root, tokens)


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


def _cache_origin_txt(slug_dir: Path, real_path: str) -> None:
    """Write origin.txt for an existing slug that lacked one — so the
    next /projects call hits step 1 and avoids the filesystem walk.

    Refuses to write if `slug_dir` isn't directly under the Claude
    projects dir — defensive guard against a path-traversal slug name
    redirecting the write outside the expected tree.
    """
    if slug_dir.parent != _claude_projects_dir():
        logger.debug(
            "origin.txt cache skipped: %s is outside %s",
            slug_dir, _claude_projects_dir(),
        )
        return
    try:
        (slug_dir / "origin.txt").write_text(real_path, encoding="utf-8")
    except OSError as e:
        logger.debug("origin.txt cache write failed for %s: %s", slug_dir.name, e)


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


def list_recent_projects(
    limit: int = 5, *, recovered_only: bool = True,
) -> list[dict]:
    """Enumerate Token-Saver-bootstrapped projects, sorted by recency.

    Returns up to `limit` projects. Each entry: slug, path, name,
    last_used_iso. Top-pinned: Prefs.last_project_path if set.

    `recovered_only=True` (default) skips entries whose original path
    couldn't be recovered (no `origin.txt` AND filesystem walk failed,
    OR walk succeeded but `.claude/manifest.jsonl` is gone). Stale
    pytest temp dirs and deleted worktrees fall into this bucket and
    just clutter the picker. Pass `False` to include them anyway (e.g.
    if you want to surface "this project was bootstrapped but the
    folder vanished" diagnostics).
    """
    out: list[dict] = []
    pdir = _claude_projects_dir()
    if not pdir.is_dir():
        return out

    # Slug-name substrings that mark non-user projects we should never
    # surface (pytest scratch dirs, %TEMP% paths, etc). Filtering these
    # at the cheap-stat stage avoids per-slug filesystem walks that
    # blow the picker's HTTP timeout when ~/.claude/projects/ holds
    # dozens of test residue dirs.
    _SLUG_BLOCKLIST = (
        "pytest-of-",
        "-AppData-Local-Temp-",
        "-AppData-Local-Temp",
        "-Temp-pytest",
    )

    # Two-pass enumeration: cheap mtime collect first, then resolve
    # paths only for the top-K most-recent candidates. Previously
    # every slug got a filesystem walk via
    # `_read_project_path_from_manifest`, which on ~60 pytest temp
    # dirs took 8-12s — longer than the picker's HTTP timeout.
    cheap: list[tuple[float, Path]] = []  # (mtime, slug_dir)
    for slug_dir in pdir.iterdir():
        if not slug_dir.is_dir():
            continue
        name = slug_dir.name
        if any(s in name for s in _SLUG_BLOCKLIST):
            continue
        memory_dir = slug_dir / "memory"
        if not memory_dir.is_dir():
            continue
        try:
            mtime = memory_dir.stat().st_mtime
        except OSError:
            continue
        cheap.append((mtime, slug_dir))

    cheap.sort(key=lambda x: x[0], reverse=True)

    # Resolve real paths only for the top candidates. 5x the requested
    # limit gives slack for entries whose path resolution fails (we
    # filter them out below); avoids resolving all 60 when we only
    # need 5.
    resolve_cap = max(limit * 5, 10)
    candidates: list[tuple[float, dict]] = []
    for mtime, slug_dir in cheap[:resolve_cap]:
        memory_dir = slug_dir / "memory"
        project_path = _read_project_path_from_manifest(memory_dir) or ""
        if recovered_only and not project_path:
            continue
        proj_name = (
            Path(project_path).name if project_path else slug_dir.name
        )
        candidates.append((mtime, {
            "slug": slug_dir.name,
            "path": project_path,
            "name": proj_name,
            "last_used_iso": datetime.fromtimestamp(
                mtime,
            ).isoformat(timespec="seconds"),
        }))

    out = [entry for _, entry in candidates[:limit]]

    # Pin last_project_path to the top if not already there
    try:
        from .prefs import Prefs
        prefs = Prefs.load()
        last = prefs.last_project_path
        if last:
            existing_idx = next(
                (i for i, e in enumerate(out) if e["path"] == last), -1,
            )
            if existing_idx > 0:
                out.insert(0, out.pop(existing_idx))
            elif existing_idx == -1 and Path(last).is_dir():
                # Add it to the top
                out.insert(0, {
                    "slug": "(current)",
                    "path": last,
                    "name": Path(last).name,
                    "last_used_iso": datetime.now().isoformat(timespec="seconds"),
                })
                out = out[:limit]
    except Exception as e:
        logger.debug("Pinning last_project_path failed: %s", e)

    return out


# ── Improve pipeline ────────────────────────────────────────────────

from .constants import (
    RECENT_PROJECTS_LIMIT,
    SNIPPET_TOKEN_BUDGET,
    SNIPPET_TOP_K,
)


def _gather_snippet_context(
    project_path: str, query: str,
) -> tuple[str, int, int]:
    """Search the project's snippet library, format top matches as code_context.

    Returns (code_context, injected_blocks, injected_tokens). All zeros if
    the library is absent or no match clears the search threshold.
    """
    if not project_path:
        return "", 0, 0
    try:
        from .generators.snippet_library import load_snippet_library
        from .search import smart_search
        from .tokenizer import count_tokens
    except Exception as e:
        logger.warning("snippet imports failed: %s", e)
        return "", 0, 0

    base = Path(project_path) / ".claude" / "snippets"
    try:
        blocks = load_snippet_library(base)
    except Exception as e:
        logger.warning("load_snippet_library failed for %s: %s", base, e)
        return "", 0, 0
    if not blocks:
        return "", 0, 0

    try:
        ranked = smart_search(blocks, query, max_results=SNIPPET_TOP_K)
    except Exception as e:
        logger.warning("smart_search failed: %s", e)
        return "", 0, 0
    if not ranked:
        return "", 0, 0

    sections: list[str] = []
    injected_blocks = 0
    injected_tokens = 0
    for _score, block in ranked:
        header = f"# From: {block.file_path}:{block.start_line}"
        section = f"{header}\n{block.source}"
        try:
            section_tokens = count_tokens(section)
        except Exception as e:
            logger.warning(
                "count_tokens failed for snippet %s, skipping: %s", block.name, e,
            )
            continue
        if injected_tokens + section_tokens > SNIPPET_TOKEN_BUDGET:
            continue
        sections.append(section)
        injected_blocks += 1
        injected_tokens += section_tokens

    return "\n\n".join(sections), injected_blocks, injected_tokens


def run_improve_pipeline(
    prompt: str, project_path: str = "", intent_hint: str = "",
) -> dict:
    """Run prompt_builder pipeline. Returns dict with improved_prompt + estimate.

    Doesn't touch the GUI directly — that's the pending-file's job.
    """
    from .prompt_builder import (
        clean_request, build_smart_prompt, review_prompt, detect_intent,
    )
    from .tokenizer import count_tokens

    cleaned = clean_request(prompt)

    # Pull project conventions if a project was picked.
    project_conventions = ""
    if project_path:
        pp = Path(project_path)
        conv_path = pp / ".claude" / "memory" / "project_conventions.md"
        if conv_path.is_file():
            try:
                project_conventions = conv_path.read_text(encoding="utf-8")[:2000]
            except OSError:
                pass

    code_context, injected_blocks, injected_tokens = _gather_snippet_context(
        project_path, cleaned,
    )

    intent = intent_hint or detect_intent(cleaned)
    improved = build_smart_prompt(
        request=cleaned,
        code_context=code_context,
        project_conventions=project_conventions,
    )
    review = review_prompt(prompt, improved)

    # Each injected snippet is code Claude would otherwise have to
    # regenerate from scratch, so cost ≈ savings.
    if project_path:
        try:
            from .tracker import TokenTracker
            TokenTracker().record(
                operation="improve",
                tokens=injected_tokens,
                project=Path(project_path).name,
                detail=f"snippets={injected_blocks} intent={intent}",
                tokens_avoided=injected_tokens,
            )
        except Exception as e:
            logger.warning("token tracker record failed: %s", e)

    return {
        "improved_prompt": improved,
        "original_tokens": count_tokens(prompt),
        "improved_tokens": review["prompt_tokens"],
        "intent": intent,
        "expansion_ratio": review["expansion_ratio"],
        "impact": review["impact"],
        "injected_snippets": injected_blocks,
        "injected_tokens": injected_tokens,
    }


def write_pending(payload: dict) -> bool:
    """Write IPC payload for GUI to pick up. Atomic via os.replace."""
    try:
        PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = PENDING_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, PENDING_PATH)
        return True
    except OSError as e:
        logger.warning("Failed to write pending file: %s", e)
        return False


def _allow_foreground_steal() -> None:
    """Grant any process permission to call SetForegroundWindow.

    The HTTP server runs in the tray process; the GUI is a separate
    process. Windows blocks SetForegroundWindow from a non-foreground
    process, which is why `lift() + focus_force()` from the GUI
    sometimes only blinks the taskbar instead of surfacing the window.
    Calling AllowSetForegroundWindow(ASFW_ANY) hands the foreground
    privilege to whichever process tries to claim it next — typically
    the GUI when it picks up the pending file. No-op on non-Windows
    or when ctypes/user32 is unavailable.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.user32.AllowSetForegroundWindow(-1)  # ASFW_ANY
    except Exception as e:
        logger.debug("AllowSetForegroundWindow failed: %s", e)


def ensure_gui_running() -> bool:
    """If GUI not running, spawn it. Returns True if it should appear soon."""
    try:
        from .single_instance import is_locked
        if is_locked("ClaudeTokenSaverGUI"):
            return True
    except Exception as e:
        logger.debug("is_locked check failed: %s", e)

    # Spawn GUI subprocess. Reuse session_launcher's spawn helper for
    # consistency in detached-process flags.
    try:
        from .session_launcher import _spawn_detached, _find_exe
        exe = _find_exe()
        if exe is not None:
            return _spawn_detached([str(exe)])
        # Fallback to python -m
        py = sys.executable
        if sys.platform == "win32":
            cand = Path(py).with_name("pythonw.exe")
            if cand.is_file():
                py = str(cand)
        return _spawn_detached([py, "-m", "claude_backend.gui"])
    except Exception as e:
        logger.warning("Failed to spawn GUI: %s", e)
        return False


# ── HTTP handler ────────────────────────────────────────────────────

ALLOWED_ORIGIN_PREFIXES = (
    "chrome-extension://",
    "moz-extension://",
    "edge-extension://",
)


def _origin_allowed(origin: str) -> bool:
    if not origin:
        return True  # curl, native callers
    return origin.startswith(ALLOWED_ORIGIN_PREFIXES)


class _Handler(BaseHTTPRequestHandler):
    """Minimal request router."""

    # Silence default per-request stderr logging.
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        logger.debug("%s - %s", self.client_address[0], format % args)

    def _send_json(self, code: int, payload: dict, origin: str = "") -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if origin and _origin_allowed(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _handle_options(self) -> None:
        origin = self.headers.get("Origin", "")
        self.send_response(204)
        if origin and _origin_allowed(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._handle_options()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        origin = self.headers.get("Origin", "")
        if path == "/health":
            self._send_json(200, {"ok": True, "version": VERSION}, origin)
        elif path == "/projects":
            try:
                projects = list_recent_projects(limit=RECENT_PROJECTS_LIMIT)
                self._send_json(200, {"projects": projects}, origin)
            except Exception as e:
                logger.exception("/projects failed")
                self._send_json(500, {"error": str(e)}, origin)
        else:
            self._send_json(404, {"error": "not found"}, origin)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        origin = self.headers.get("Origin", "")

        if not _origin_allowed(origin):
            self._send_json(403, {"error": "origin not allowed"}, "")
            return

        if path != "/improve":
            self._send_json(404, {"error": "not found"}, origin)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length else ""
            data = json.loads(raw) if raw else {}
        except (ValueError, json.JSONDecodeError) as e:
            self._send_json(400, {"error": f"bad JSON: {e}"}, origin)
            return

        prompt = str(data.get("prompt", ""))
        project_path = str(data.get("project_path", ""))
        intent_hint = str(data.get("intent_hint", ""))

        if not prompt.strip():
            self._send_json(400, {"error": "prompt is empty"}, origin)
            return

        try:
            result = run_improve_pipeline(prompt, project_path, intent_hint)
        except Exception as e:
            logger.exception("/improve pipeline failed")
            self._send_json(500, {"error": str(e)}, origin)
            return

        # Write pending file for GUI; spawn GUI if needed.
        write_pending({
            "kind": "improve_request",
            "ts": datetime.now().isoformat(timespec="seconds"),
            "original_prompt": prompt,
            "project_path": project_path,
            **result,
        })
        # Belt-and-braces grant: even if the overlay process didn't
        # call AllowSetForegroundWindow first (e.g. Chrome extension
        # path), the tray process gets a chance here to permit the
        # GUI to raise. Cheap no-op when the call has no effect.
        _allow_foreground_steal()
        gui_ok = ensure_gui_running()

        result["builder_opened"] = gui_ok
        self._send_json(200, result, origin)


# ── Public API ──────────────────────────────────────────────────────

def is_port_free(port: int) -> bool:
    """Check whether 127.0.0.1:port is free for bind.

    NOTE: unreliable on Windows when the running server has
    SO_REUSEADDR set (which `http.server.HTTPServer` does by default —
    `allow_reuse_address = 1`). A fresh bind from a different process
    can succeed even though the port is bound. Prefer `is_backend_alive`
    for "is OUR HTTP server up?" questions. Kept here for callers that
    actually need pre-bind availability (e.g. start_server).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False
    finally:
        try:
            s.close()
        except OSError:
            pass


def is_backend_alive(port: int, timeout: float = 0.4) -> bool:
    """Authoritative check: is OUR HTTP backend answering on port?

    Hits GET /health, returns True iff response body has `ok: true`.
    Independent of bind semantics, so it works correctly even on
    Windows where `is_port_free` lies due to SO_REUSEADDR.
    """
    import json as _json
    import urllib.error
    import urllib.request

    url = f"http://127.0.0.1:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            if r.status != 200:
                return False
            body = _json.loads(r.read().decode("utf-8"))
            return bool(body.get("ok"))
    except (urllib.error.URLError, OSError, ValueError):
        return False


def start_server(port: int) -> bool:
    """Start HTTP server in a daemon thread. Idempotent.

    Returns True on successful start (or already-running). False if port
    is unavailable or another error prevents binding.
    """
    global _server, _server_thread
    if _server is not None and _server_thread is not None and _server_thread.is_alive():
        return True

    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    except OSError as e:
        logger.warning("HTTP server bind failed on 127.0.0.1:%d: %s", port, e)
        return False

    thread = threading.Thread(
        target=server.serve_forever,
        name="token_saver_http",
        daemon=True,
    )
    thread.start()
    _server = server
    _server_thread = thread
    logger.info("HTTP server listening on 127.0.0.1:%d", port)
    return True


def stop_server() -> None:
    """Shut down the running server. Mostly for tests / Quit."""
    global _server, _server_thread
    if _server is not None:
        try:
            _server.shutdown()
            _server.server_close()
        except Exception as e:
            logger.debug("Server shutdown error: %s", e)
    _server = None
    _server_thread = None


def is_running() -> bool:
    """Quick check whether server thread is alive."""
    return _server_thread is not None and _server_thread.is_alive()
