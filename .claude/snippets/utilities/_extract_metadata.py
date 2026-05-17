# From: classifier/classifier.py:221
# Extract URLs, code languages, error patterns from prompt.

    @staticmethod
    def _extract_metadata(prompt: str) -> dict:
        """Extract URLs, code languages, error patterns from prompt."""
        urls = re.findall(r"https?://\S+", prompt)
        # Code block languages: ```python, ```c, ```javascript etc.
        code_langs = re.findall(r"```(\w+)", prompt)
        # Error/traceback blocks
        error_patterns = [
            r"Traceback \(most recent call last\)",
            r"^\s*File \".*\", line \d+",
            r"FATAL|panic:|SIGSEGV|segmentation fault",
            r"^\s*at [\w.]+\([\w.]+:\d+\)",  # Java/JS stack frames
        ]
        error_blocks = any(
            re.search(p, prompt, re.MULTILINE | re.IGNORECASE)
            for p in error_patterns
        )
        return {
            "url_count": len(urls),
            "code_languages": list(set(code_langs)),
            "error_blocks": error_blocks,
        }
