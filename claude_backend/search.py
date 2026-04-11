"""Fuzzy semantic search engine for code snippets.

Handles: typos, synonyms, intent detection, sloppy English.
No external dependencies — pure stdlib.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Optional

from .types import CodeBlock

# ── Domain detection ───────────────────────────────────────────────
# Maps file path fragments to human-readable domain names.
# Used by Snippets view for "Browse by Area" and by Quick Grab.

FILE_DOMAINS: dict[str, str] = {
    "cdp_client": "Browser",
    "browser_actions": "Browser",
    "browser_client": "Browser",
    "window_manager": "Windows",
    "ai_profiles": "AI Chat",
    "broadcast": "AI Chat",
    "session_manager": "Sessions",
    "universal_client": "Sessions",
    "auto_save": "Files",
    "storage": "Files",
    "config": "Config",
    "search": "Search",
    "tracker": "Tracking",
    "prompt_builder": "Prompts",
    "prompt_engine": "Prompts",
    "prompt_architect": "Prompts",
    "gui": "GUI",
    "app_web": "GUI",
    "code_extractor": "Analysis",
    "pattern_detector": "Analysis",
    "structure_mapper": "Analysis",
    "snippet_library": "Analysis",
    "claude_md": "Analysis",
    "memory_files": "Analysis",
    "ollama_manager": "AI Models",
    "mod_": "Game Mods",
    "emerald_mod": "Game Mods",
    "save_editor": "Save Editor",
    "build_manager": "Build",
    "task_manager": "Tasks",
    "expander": "Tasks",
    "history": "History",
    "scraper": "Scraping",
    "style_engine": "Styles",
    "tool_registry": "Tools",
    "video": "Video",
    "audio": "Audio",
}

# Colors for domain badges in the GUI
DOMAIN_COLORS: dict[str, str] = {
    "Browser": "#e81123",
    "Windows": "#ff8c00",
    "AI Chat": "#0078d4",
    "Sessions": "#8e44ad",
    "Files": "#107c10",
    "Config": "#107c10",
    "Search": "#00b7c3",
    "Tracking": "#00b7c3",
    "Prompts": "#8e44ad",
    "GUI": "#ff8c00",
    "Analysis": "#808080",
    "AI Models": "#0078d4",
    "Game Mods": "#e81123",
    "Tasks": "#ff8c00",
    "Build": "#808080",
}


def get_domain(file_path: str) -> str:
    """Get the domain label for a code block based on its file path."""
    fp = file_path.lower().replace("\\", "/")
    # Check longest matches first (mod_ prefix)
    for pattern, domain in FILE_DOMAINS.items():
        if pattern in fp:
            return domain
    return "Other"


def get_domain_color(domain: str) -> str:
    """Get the badge color for a domain."""
    return DOMAIN_COLORS.get(domain, "#808080")


def get_all_domains(snippets: list[CodeBlock]) -> list[str]:
    """Get sorted list of unique domains present in the snippets."""
    domains = set()
    for b in snippets:
        domains.add(get_domain(b.file_path))
    return sorted(domains)


# ── Typo correction ───────────────────────────────────────────────────
# Common programming/tech words that users misspell.
# Maps misspelling -> correct word. Applied BEFORE search expansion.
# Built from real user typos observed in tracker sessions.

_TYPO_FIXES: dict[str, str] = {
    # Short common typos
    "teh": "the", "hte": "the", "thn": "then", "adn": "and", "taht": "that",
    "fo": "for", "ot": "to", "si": "is", "ti": "it", "nto": "not",
    # Observed in real sessions
    "timout": "timeout", "tiemout": "timeout", "tmeout": "timeout",
    "conection": "connection", "connecion": "connection", "conecton": "connection",
    "sesion": "session", "sesions": "sessions", "sesson": "session",
    "brwoser": "browser", "broswer": "browser", "bowser": "browser",
    "clik": "click", "clck": "click", "clikc": "click",
    "windwo": "window", "widnow": "window", "winodw": "window",
    "promts": "prompts", "promt": "prompt", "pormpt": "prompt",
    "sendin": "sending", "snding": "sending",
    "fokus": "focus", "focsu": "focus",
    "downlod": "download", "donwload": "download", "dowload": "download",
    "exract": "extract", "extrat": "extract", "exctract": "extract",
    "clipbord": "clipboard", "clipbaord": "clipboard",
    "positon": "position", "postion": "position", "posiiton": "position",
    "manege": "manage", "mangae": "manage", "manaeg": "manage",
    "setings": "settings", "settigns": "settings", "settngs": "settings",
    "configration": "configuration", "confg": "config",
    "funtion": "function", "fucntion": "function", "funciton": "function",
    "reponse": "response", "respone": "response", "repsponse": "response",
    "mesage": "message", "messge": "message", "messsage": "message",
    "searh": "search", "serach": "search", "searhc": "search",
    "delet": "delete", "deleet": "delete",
    "updaet": "update", "updat": "update",
    "creat": "create", "craete": "create",
    "handel": "handle", "hanlde": "handle",
    "reuqest": "request", "requst": "request", "requets": "request",
    "dispaly": "display", "disply": "display",
    "rednder": "render", "rendr": "render",
    "modle": "model", "modle": "model",
    "tokne": "token", "toke": "token",
    "proflie": "profile", "proifle": "profile",
    "scaner": "scanner", "scannr": "scanner",
    "anaylze": "analyze", "anlyze": "analyze", "analze": "analyze",
    "generaet": "generate", "genrate": "generate",
    "automte": "automate", "autoamte": "automate",
    "perfomance": "performance", "performace": "performance",
    "trakker": "tracker", "trackr": "tracker", "tarcker": "tracker",
    "scaner": "scanner", "scanr": "scanner",
    "optmize": "optimize", "optimze": "optimize",
    "refator": "refactor", "refacor": "refactor",
    "debuger": "debugger", "debbuger": "debugger",
    "complie": "compile", "comiple": "compile",
    "librray": "library", "libary": "library",
    "templete": "template", "tempalte": "template",
    "webscoket": "websocket", "websoket": "websocket",
}


def _fix_typos(words: list[str]) -> list[str]:
    """Fix common typos using the dictionary, plus SequenceMatcher for unknown ones."""
    fixed = []
    # Build a vocabulary from concepts + domain names for fuzzy correction
    vocab = set()
    for concept_words in CONCEPTS.values():
        vocab.update(concept_words)
    vocab.update(CONCEPTS.keys())
    vocab.update(FILE_DOMAINS.values())

    for w in words:
        # Direct dictionary hit
        if w in _TYPO_FIXES:
            fixed.append(_TYPO_FIXES[w])
            continue

        # If the word is already in vocabulary, keep it
        if w in vocab:
            fixed.append(w)
            continue

        # Try fuzzy match against vocabulary for unknown typos
        best_word = w
        best_score = 0.0
        for v in vocab:
            if abs(len(v) - len(w)) > 2:
                continue  # skip words too different in length
            ratio = SequenceMatcher(None, w, v).ratio()
            if ratio > best_score and ratio > 0.75:
                best_score = ratio
                best_word = v

        fixed.append(best_word)
    return fixed


# ── Synonym / concept map ──────────────────────────────────────────────
# Each key is a "concept". If the user says any word in the value list,
# it expands to match ALL words in the list plus the key.
CONCEPTS: dict[str, list[str]] = {
    "gui": ["ui", "window", "widget", "button", "label", "frame", "dialog",
            "panel", "layout", "screen", "display", "render", "view", "tab",
            "sidebar", "toolbar", "menu", "modal", "popup", "toast", "theme",
            "color", "font", "style", "customtkinter", "ctk", "tkinter",
            "show", "page", "interface", "dashboard", "card"],
    "network": ["http", "request", "response", "api", "url", "fetch", "download",
                "upload", "socket", "websocket", "cdp", "chrome", "browser",
                "connection", "connect", "timeout", "port", "server", "client",
                "talk", "communicate", "site", "web", "page"],
    "file": ["path", "directory", "folder", "read", "write", "save", "load",
             "open", "close", "json", "yaml", "toml", "config", "settings",
             "storage", "disk", "io", "remember", "persist", "store", "work"],
    "error": ["exception", "bug", "fix", "crash", "fail", "broken", "issue",
              "problem", "debug", "trace", "traceback", "stack", "catch",
              "try", "except", "raise", "handle", "recover", "retry"],
    "test": ["testing", "unittest", "pytest", "assert", "mock", "fixture",
             "spec", "verify", "validate", "check", "smoke"],
    "async": ["thread", "threading", "concurrent", "parallel", "daemon",
              "background", "worker", "queue", "lock", "await", "coroutine"],
    "data": ["database", "db", "sql", "query", "table", "record", "row",
             "column", "schema", "model", "dataclass", "struct", "serialize",
             "deserialize", "parse", "format", "json", "csv"],
    "clipboard": ["copy", "paste", "pyperclip", "transfer", "clip"],
    "search": ["find", "lookup", "query", "filter", "match", "grep",
               "scan", "discover", "locate", "index"],
    "auth": ["login", "password", "token", "key", "secret", "credential",
             "permission", "access", "role", "session", "cookie", "oauth"],
    "log": ["logging", "logger", "print", "debug", "info", "warning",
            "output", "trace", "verbose", "message", "report"],
    "config": ["configuration", "settings", "options", "preferences",
               "setup", "initialize", "init", "defaults", "parameters"],
    "deploy": ["build", "package", "install", "release", "publish",
               "distribute", "bundle", "compile", "pip", "npm"],
    "ai": ["model", "prompt", "generate", "llm", "claude", "gemini",
           "chatgpt", "openai", "anthropic", "inference", "chat", "completion",
           "token", "context", "agent", "profile", "timeout", "retry",
           "instruction", "request", "message", "response"],
    "performance": ["speed", "slow", "fast", "latency", "benchmark", "profile",
                    "cache", "memoize", "optimize", "bottleneck", "memory"],
    "parse": ["parsing", "validate", "validation", "schema", "format",
              "deserialize", "marshal", "decode", "encode", "transform"],
    "state": ["store", "context", "global", "singleton", "variable",
              "mutation", "immutable", "observable", "reactive"],
    "process": ["subprocess", "shell", "command", "exec", "spawn", "pipe",
                "stdin", "stdout", "terminal", "powershell", "bash"],
    "prompt": ["instruction", "request", "message", "input", "query",
               "ask", "tell", "command", "task", "describe"],
    "remember": ["track", "log", "record", "memory", "cache", "history",
                 "store", "persist", "previous", "last", "recent"],
    "talk": ["chat", "message", "send", "ask", "communicate", "respond",
             "reply", "converse", "speak", "tell", "interact"],
    "show": ["display", "render", "draw", "output", "present", "visualize",
             "view", "print", "reveal", "open", "appear"],
    "control": ["manage", "handle", "operate", "run", "start", "stop",
                "toggle", "switch", "enable", "disable", "turn"],
    "automate": ["automatic", "auto", "bot", "script", "macro", "repeat",
                 "schedule", "trigger", "loop", "batch", "queue"],
    "window": ["hwnd", "foreground", "focus", "minimize", "maximize",
               "position", "move", "resize", "corner", "screen", "monitor"],
    "session": ["state", "manager", "manage", "lifecycle", "create", "destroy",
                "start", "stop", "active", "running", "idle", "coordinate",
                "session_manager", "sessions"],
    "extract": ["parse", "scrape", "pull", "grab", "collect", "gather",
                "harvest", "mine", "capture", "read", "get"],
    "send": ["submit", "post", "push", "transmit", "dispatch", "emit",
             "broadcast", "publish", "notify", "message", "prompt", "deliver"],
    "wait": ["sleep", "delay", "timeout", "poll", "interval", "timer",
             "countdown", "pause", "idle", "block"],
    "css": ["selector", "element", "dom", "html", "xpath", "class",
            "attribute", "style", "tag", "node"],
    "move": ["position", "place", "arrange", "layout", "relocate",
             "shift", "drag", "drop", "align", "center"],
}

# Build reverse index: word -> set of concept keys
_WORD_TO_CONCEPTS: dict[str, set[str]] = {}
for _concept, _words in CONCEPTS.items():
    for _w in _words:
        _WORD_TO_CONCEPTS.setdefault(_w, set()).add(_concept)
    _WORD_TO_CONCEPTS.setdefault(_concept, set()).add(_concept)


# ── Simple stemmer ─────────────────────────────────────────────────────
_SUFFIXES = ["tion", "sion", "ment", "ness", "able", "ible", "ful",
             "less", "ous", "ive", "ing", "ied", "ies", "ers", "est",
             "ify", "ize", "ise", "ated", "ting", "ted", "er", "ed",
             "ly", "al", "es", "ts", "en", "s"]

def _stem(word: str) -> str:
    """Cheap suffix-stripping stemmer. Not perfect, just good enough."""
    w = word.lower().strip()
    if len(w) <= 3:
        return w
    for suf in _SUFFIXES:
        if w.endswith(suf) and len(w) - len(suf) >= 2:
            return w[:-len(suf)]
    return w


# ── Fuzzy match ────────────────────────────────────────────────────────
def _fuzzy_match(query_word: str, target_word: str) -> float:
    """Score 0.0-1.0 for how well query matches target.

    Handles typos via SequenceMatcher.
    """
    if query_word == target_word:
        return 1.0
    if query_word in target_word or target_word in query_word:
        return 0.85
    # Stem match
    if _stem(query_word) == _stem(target_word):
        return 0.8
    # Fuzzy (typo tolerance) — generous threshold for sloppy typing
    ratio = SequenceMatcher(None, query_word, target_word).ratio()
    if ratio > 0.55:
        return ratio * 0.8
    # Also check if first 3 chars match (common typo pattern: right start, wrong end)
    if len(query_word) >= 3 and len(target_word) >= 3 and query_word[:3] == target_word[:3]:
        return 0.5
    return 0.0


def _expand_query(raw_query: str) -> list[str]:
    """Turn a sloppy English query into expanded search terms.

    - Splits into words (caps at 20 most distinctive words)
    - Adds synonym expansions
    - Adds stems
    """
    # Clean and split
    raw = raw_query.lower().strip()
    raw = re.sub(r"[^a-z0-9_ ]", " ", raw)
    all_words = [w for w in raw.split() if len(w) > 2]

    # Only strip TRUE filler — keep words that carry intent (build, make, show, find, etc.)
    _FILLER = {"the", "and", "for", "that", "with", "this", "from", "will", "have",
               "been", "they", "which", "their", "into", "also", "than", "them",
               "each", "all", "one", "not", "but", "are", "was", "were", "has",
               "had", "its", "our", "who", "very", "just", "really", "actually",
               "basically", "should", "could", "would", "about", "being", "whole",
               "thing", "some", "other", "every", "still", "already", "right"}
    words = [w for w in all_words if w not in _FILLER][:20]
    if not words:
        words = all_words[:10]  # fallback: use everything rather than return nothing

    # Fix typos BEFORE expansion so corrected words hit concepts properly
    words = _fix_typos(words)

    expanded: set[str] = set(words)

    for word in words:
        # Add stem
        expanded.add(_stem(word))

        # Add concept synonyms
        # Direct concept match
        if word in CONCEPTS:
            expanded.update(CONCEPTS[word])
        # Reverse: word is a synonym of a concept
        if word in _WORD_TO_CONCEPTS:
            for concept in _WORD_TO_CONCEPTS[word]:
                expanded.update(CONCEPTS[concept])

        # Also try stem against concepts
        stemmed = _stem(word)
        if stemmed in CONCEPTS:
            expanded.update(CONCEPTS[stemmed])
        if stemmed in _WORD_TO_CONCEPTS:
            for concept in _WORD_TO_CONCEPTS[stemmed]:
                expanded.update(CONCEPTS[concept])

    return list(expanded)


# ── Main scoring ───────────────────────────────────────────────────────

def score_block(block: CodeBlock, query_terms: list[str], raw_words: list[str]) -> float:
    """Score a code block against expanded query terms.

    Designed for NON-CODERS: matches vague descriptions, penalizes
    deep session artifacts, boosts well-documented code.

    Returns 0.0+ score. Higher = more relevant.
    """
    score = 0.0

    name_lower = block.name.lower()
    name_words = re.split(r"[_\s]+", name_lower)
    name_words = [w for w in name_words if w]

    doc_lower = (block.docstring or "").lower()
    doc_words = set(re.split(r"\W+", doc_lower)) if doc_lower else set()
    path_lower = block.file_path.lower()
    path_words = re.split(r"[_/\\\.\s]+", path_lower)

    kind_lower = block.kind.lower()

    # ── Score against raw user words (highest priority) ──
    for qw in raw_words:
        # Exact name word match
        if qw in name_words:
            score += 10.0
        else:
            best = max((_fuzzy_match(qw, nw) for nw in name_words), default=0.0)
            if best > 0.5:
                score += best * 8.0

        # Docstring: check both substring AND word-level match
        if qw in doc_lower:
            score += 4.0
        elif _stem(qw) in doc_words:
            score += 3.0
        elif any(_fuzzy_match(qw, dw) > 0.7 for dw in doc_words):
            score += 2.0  # fuzzy docstring match for typos

        # Path
        if qw in path_words:
            score += 3.0
        else:
            best_p = max((_fuzzy_match(qw, pw) for pw in path_words), default=0.0)
            if best_p > 0.6:
                score += best_p * 2.5

    # ── Score against expanded synonym terms (lower weight) ──
    expanded_only = [t for t in query_terms if t not in raw_words]
    content_matches = 0
    for term in expanded_only:
        if term in name_words:
            score += 3.0
        if term in doc_words:
            score += 1.5
        if term in path_words:
            score += 1.0
        if term in kind_lower:
            score += 2.0
        if content_matches < 5 and term in block.source.lower()[:500]:
            score += 0.5
            content_matches += 1

    # ── BONUSES for non-coder friendliness ──

    # Documented code is more useful to beginners
    if block.docstring and len(block.docstring) > 20:
        score *= 1.3  # 30% boost for well-documented blocks

    # ── PENALTIES ──

    # Deep paths = session artifacts, old generated code — less relevant
    depth = path_lower.count("/")
    if depth > 3:
        score *= 0.5  # halve score for deeply nested files
    elif depth > 2:
        score *= 0.75

    # Penalize code from sessions/ClaudeProjects (old generated artifacts)
    if "sessions/" in path_lower or "claudeprojects" in path_lower:
        score *= 0.3  # heavy penalty — these are old copies, not the real code

    return score


class SearchIndex:
    """Pre-computed inverted index for fast searching over large snippet sets.

    Build once after scanning, then run many queries against it.
    Avoids running SequenceMatcher on every block for every query.
    """

    def __init__(self, snippets: list[CodeBlock]) -> None:
        self._snippets = snippets
        # Inverted index: word -> set of block indices
        self._name_index: dict[str, set[int]] = {}
        self._doc_index: dict[str, set[int]] = {}
        self._path_index: dict[str, set[int]] = {}
        self._kind_index: dict[str, set[int]] = {}
        # Pre-split name/path words per block (avoid re-splitting on every query)
        self._name_words: list[list[str]] = []
        self._path_words: list[list[str]] = []
        self._build()

    def _build(self) -> None:
        for i, block in enumerate(self._snippets):
            nw = [w for w in re.split(r"[_\s]+", block.name.lower()) if w]
            self._name_words.append(nw)
            for w in nw:
                self._name_index.setdefault(w, set()).add(i)
                # Also index stems and prefixes for fuzzy
                self._name_index.setdefault(_stem(w), set()).add(i)
                if len(w) >= 3:
                    self._name_index.setdefault(w[:3], set()).add(i)

            pw = [w for w in re.split(r"[_/\\\.\s]+", block.file_path.lower()) if w]
            self._path_words.append(pw)
            for w in pw:
                self._path_index.setdefault(w, set()).add(i)

            doc = (block.docstring or "").lower()
            for w in set(re.split(r"\W+", doc)):
                if len(w) > 2:
                    self._doc_index.setdefault(w, set()).add(i)

            self._kind_index.setdefault(block.kind.lower(), set()).add(i)

    def search(self, query: str, max_results: int = 15, min_score: float = 3.0
               ) -> list[tuple[float, CodeBlock]]:
        """Search using the pre-built index. Fast even on 10K+ blocks."""
        if not query.strip():
            return []

        raw = re.sub(r"[^a-z0-9_ ]", " ", query.lower().strip())
        raw_words = [w for w in raw.split() if len(w) > 1]
        expanded = _expand_query(query)

        # Candidate selection: only score blocks that match at least one term
        candidates: set[int] = set()
        all_terms = set(raw_words) | set(expanded)
        for term in all_terms:
            candidates.update(self._name_index.get(term, set()))
            candidates.update(self._doc_index.get(term, set()))
            candidates.update(self._path_index.get(term, set()))
            candidates.update(self._kind_index.get(term, set()))
            # Also check stems
            st = _stem(term)
            candidates.update(self._name_index.get(st, set()))
            candidates.update(self._doc_index.get(st, set()))
            # Prefix match for fuzzy
            if len(term) >= 3:
                candidates.update(self._name_index.get(term[:3], set()))

        # Score only candidates (not all blocks)
        results: list[tuple[float, CodeBlock]] = []
        for idx in candidates:
            block = self._snippets[idx]
            sc = score_block(block, expanded, raw_words)
            if sc < min_score:
                continue
            # Penalize very large blocks — they waste tokens
            lines = block.end_line - block.start_line + 1
            if lines > 100:
                sc *= 0.5
            elif lines > 50:
                sc *= 0.75
            results.append((sc, block))

        # Deduplicate: same function from duplicate file paths (e.g. cdp_client.py vs gemini_coder_web/cdp_client.py)
        seen: dict[str, int] = {}  # "name:source_prefix" -> index in deduped
        deduped: list[tuple[float, CodeBlock]] = []
        for sc, block in sorted(results, key=lambda x: -x[0]):
            key = f"{block.name}:{block.source[:200]}"
            if key in seen:
                # Keep the one with shorter path (less nested = more canonical)
                existing_idx = seen[key]
                if len(block.file_path) < len(deduped[existing_idx][1].file_path):
                    deduped[existing_idx] = (sc, block)
            else:
                seen[key] = len(deduped)
                deduped.append((sc, block))

        return deduped[:max_results]


# Keep the simple function API for backward compatibility
_cached_index: Optional[SearchIndex] = None
_cached_snippets_id: Optional[int] = None
_cached_snippets_len: int = 0


def smart_search(
    snippets: list[CodeBlock],
    query: str,
    max_results: int = 15,
    min_score: float = 3.0,
) -> list[tuple[float, CodeBlock]]:
    """Search snippets with fuzzy matching, synonyms, and intent detection.

    Automatically builds and caches an inverted index for performance.
    On a 10K-block project, first query builds the index (~200ms),
    subsequent queries use it (~5ms each).
    """
    global _cached_index, _cached_snippets_id, _cached_snippets_len

    if not query.strip() or not snippets:
        return []

    # Rebuild index if list identity OR length changed (catches mutations)
    snippets_id = id(snippets)
    snippets_len = len(snippets)
    if (_cached_index is None
            or _cached_snippets_id != snippets_id
            or _cached_snippets_len != snippets_len):
        _cached_index = SearchIndex(snippets)
        _cached_snippets_id = snippets_id
        _cached_snippets_len = snippets_len

    # Scale min_score by query length — short queries need lower threshold
    raw = re.sub(r"[^a-z0-9_ ]", " ", query.lower().strip())
    raw_words = [w for w in raw.split() if len(w) > 2]
    effective_min = max(2.0, min_score * len(raw_words) / 4)

    return _cached_index.search(query, max_results, effective_min)
