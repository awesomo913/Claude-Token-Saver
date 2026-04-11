"""Smart prompt builder — integrates Prompt Architect logic for better prompts.

Structures user requests with role assignment, constraints, reasoning frameworks,
and quality gates. Makes Claude give better answers while using fewer tokens.
"""

from __future__ import annotations

# ── Roles (auto-assigned based on what the user is doing) ──────────

ROLES = {
    "code": "Senior Software Engineer specializing in Python, clean architecture, and production-grade code",
    "debug": "Expert Debugger who systematically isolates root causes using stack traces, logs, and code analysis",
    "refactor": "Code Architect focused on readability, DRY principles, SOLID design, and reducing complexity",
    "test": "QA Engineer who writes thorough tests covering happy paths, edge cases, and failure modes",
    "review": "Senior Code Reviewer checking for bugs, security issues, performance problems, and maintainability",
    "explain": "Technical Educator who explains complex code clearly with examples and analogies",
    "optimize": "Performance Engineer focused on algorithmic complexity, memory usage, and execution speed",
    "feature": "Feature Engineer who implements clean, well-tested features following existing project patterns",
}

# ── Constraint presets ─────────────────────────────────────────────

CONSTRAINTS = {
    "python": ["Follow PEP 8.", "Use type hints on all functions.", "Add docstrings.",
               "Use pathlib for paths.", "Use logging, not print()."],
    "robust": ["Handle all edge cases.", "Validate inputs.", "Use specific exception types.",
               "Add meaningful error messages.", "Never silently swallow exceptions."],
    "efficient": ["Minimize token usage in response.", "No filler or restating the question.",
                  "Code only — explain in comments, not prose."],
    "security": ["Sanitize all inputs.", "No hardcoded secrets or credentials.",
                 "Use parameterized queries for any data access."],
}

# ── Reasoning frameworks ───────────────────────────────────────────

REASONING = {
    "scot": (
        "Use Structured Chain of Thought:\n"
        "1. Identify the core problem\n"
        "2. Break into sub-tasks\n"
        "3. Solve each sub-task\n"
        "4. Integrate and verify"
    ),
    "minimal": "Think step by step, then give the solution.",
    "none": "",
}

# ── Intent detection ───────────────────────────────────────────────

_INTENT_KEYWORDS = {
    "debug": ["fix", "bug", "error", "crash", "broken", "issue", "fail", "wrong", "debug", "trace"],
    "feature": ["build", "add", "create", "implement", "new", "feature", "make"],
    "refactor": ["refactor", "clean", "simplify", "restructure", "rewrite", "improve", "organize"],
    "test": ["test", "unittest", "pytest", "coverage", "assert", "mock", "spec"],
    "review": ["review", "check", "audit", "inspect", "evaluate", "assess"],
    "explain": ["explain", "how does", "what does", "understand", "walk through", "describe"],
    "optimize": ["optimize", "performance", "speed", "slow", "fast", "memory", "efficient"],
    "code": [],  # default fallback
}


def detect_intent(request: str) -> str:
    """Detect what the user is trying to do from their request text."""
    lower = request.lower()
    scores: dict[str, int] = {}
    for intent, keywords in _INTENT_KEYWORDS.items():
        scores[intent] = sum(1 for kw in keywords if kw in lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "code"


def clean_request(text: str) -> str:
    """Clean up sloppy English in the user's request before it goes to Claude.

    Fixes common typos, swapped letters, missing punctuation, and
    run-on sentences. Doesn't change meaning — just makes it readable.
    """
    import re

    if not text or len(text.strip()) < 3:
        return text

    # Word-level typo fixes (same dict as search engine)
    _COMMON_FIXES = {
        "teh": "the", "hte": "the", "th": "the", "thn": "then",
        "taht": "that", "adn": "and", "nad": "and",
        "fo": "for", "ot": "to", "ti": "it", "si": "is", "nto": "not",
        "hwo": "how", "waht": "what", "whit": "with", "fro": "from",
        "dont": "don't", "doesnt": "doesn't", "cant": "can't",
        "wont": "won't", "isnt": "isn't", "im": "I'm", "ive": "I've",
        "youre": "you're", "theyre": "they're", "theres": "there's",
        "heres": "here's", "whats": "what's", "thats": "that's",
        "itll": "it'll", "youll": "you'll",
        "timout": "timeout", "conection": "connection", "brwoser": "browser",
        "windwo": "window", "fokus": "focus", "clik": "click",
        "sesion": "session", "positon": "position", "manege": "manage",
        "setings": "settings", "downlod": "download", "mesage": "message",
        "funtion": "function", "reponse": "response", "promts": "prompts",
        "clipbord": "clipboard", "webscoket": "websocket", "trakker": "tracker",
        "configration": "configuration", "perfomance": "performance",
        "exract": "extract", "sendin": "sending", "complie": "compile",
        "refator": "refactor", "modifiy": "modify", "encountrs": "encounters",
        "pokballs": "pokeballs", "traid": "trade", "beter": "better",
        "evry": "every", "befor": "before", "aftr": "after",
        "ther": "there", "wher": "where", "wich": "which",
        "becaus": "because", "alredy": "already", "somthing": "something",
        "evrything": "everything", "diffrent": "different",
        "conect": "connect", "maneger": "manager", "managr": "manager",
        "recieve": "receive", "occured": "occurred", "seperate": "separate",
        "definately": "definitely", "necesary": "necessary",
        "wierd": "weird", "untill": "until", "accross": "across",
        "basicly": "basically", "probly": "probably", "shoud": "should",
        "actualy": "actually", "gona": "gonna", "wanna": "want to",
        "lemme": "let me", "gimme": "give me", "kinda": "kind of",
        "prolly": "probably", "tryna": "trying to", "dunno": "don't know",
    }

    # Split into words, fix each one
    words = text.split()
    fixed = []
    for w in words:
        # Preserve punctuation attached to word
        prefix = ""
        suffix = ""
        core = w
        while core and not core[0].isalnum():
            prefix += core[0]; core = core[1:]
        while core and not core[-1].isalnum():
            suffix = core[-1] + suffix; core = core[:-1]

        lower = core.lower()
        if lower in _COMMON_FIXES:
            replacement = _COMMON_FIXES[lower]
            # Preserve original capitalization
            if core and core[0].isupper():
                replacement = replacement[0].upper() + replacement[1:]
            fixed.append(prefix + replacement + suffix)
        else:
            fixed.append(w)

    result = " ".join(fixed)

    # Capitalize first letter of each sentence
    result = re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), result)

    # Capitalize "i" standing alone
    result = re.sub(r'\bi\b', 'I', result)

    # Add period at end if missing punctuation
    result = result.strip()
    if result and result[-1] not in ".!?:":
        result += "."

    return result


def build_smart_prompt(
    request: str,
    code_context: str = "",
    project_conventions: str = "",
) -> str:
    """Build a lean structured prompt from user request + code context.

    Cleans up the user's English before including it — fixes typos,
    capitalizes sentences, adds punctuation. The request should be
    clear to Claude even if the user typed it sloppily.
    """
    sections: list[str] = []

    # Clean up the user's request before including it
    cleaned = clean_request(request)
    sections.append(cleaned)

    if code_context:
        sections.append(
            "Here is the relevant code from my project. "
            "Use these references instead of regenerating:\n\n" + code_context
        )

    if project_conventions:
        sections.append("Follow these project conventions:\n" + project_conventions)

    # The ONE constraint that actually changes behavior
    sections.append("Be concise. Code only — explain in comments, not prose.")

    return "\n\n".join(sections)


def review_prompt(original_request: str, final_prompt: str) -> dict:
    """Analyze the built prompt for token efficiency."""
    prompt_tokens = len(final_prompt) * 10 // 32
    request_tokens = max(len(original_request) * 10 // 32, 1)
    ratio = prompt_tokens / request_tokens

    if prompt_tokens < 500:
        impact = "LIGHT"
    elif prompt_tokens < 2000:
        impact = "MODERATE"
    elif prompt_tokens < 8000:
        impact = "LARGE"
    else:
        impact = "VERY LARGE"

    return {
        "prompt_tokens": prompt_tokens,
        "request_tokens": request_tokens,
        "expansion_ratio": round(ratio, 1),
        "impact": impact,
        "sections": final_prompt.count("\n# ") + (1 if final_prompt.startswith("# ") else 0),
    }
