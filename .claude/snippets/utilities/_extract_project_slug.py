# From: NeoAutocoder/core_loop.py:198
# Extract project name from code or task for organized storage.

    def _extract_project_slug(self, code: str) -> Optional[str]:
        """Extract project name from code or task for organized storage."""
        match = re.search(r'(?:class|def|project|app)\s+([A-Za-z0-9_]+)', code)
        if match:
            return match.group(1).lower()
        return None
