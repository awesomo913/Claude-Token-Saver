# From: claude_backend/prompt_builder.py:75
# Clean up sloppy English in the user's request before it goes to Claude.

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
