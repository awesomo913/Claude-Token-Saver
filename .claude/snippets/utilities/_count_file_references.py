# From: classifier/classifier.py:201
# Count references to file paths in the prompt.

    @staticmethod
    def _count_file_references(prompt: str) -> int:
        """Count references to file paths in the prompt."""
        patterns = [
            r"\b\w+\.\w{1,4}\b",  # file.ext
            r"[/\\]\w+[/\\]",      # path separators
        ]
        files = set()
        for p in patterns:
            files.update(re.findall(p, prompt))
        # Filter out common false positives
        exts = {".py", ".js", ".ts", ".c", ".h", ".json", ".yaml", ".toml",
                ".md", ".html", ".css", ".txt", ".rs", ".go", ".java"}
        real_files = [f for f in files if any(f.endswith(e) for e in exts)]
        return len(real_files)
