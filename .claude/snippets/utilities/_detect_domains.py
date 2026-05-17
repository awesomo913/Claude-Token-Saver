# From: classifier/classifier.py:166
# Return list of detected domain names.

    def _detect_domains(self, text: str) -> list[str]:
        """Return list of detected domain names."""
        domains: list[str] = []
        for domain, info in self._keywords.get("domain_modifiers", {}).items():
            if any(kw in text for kw in info.get("keywords", [])):
                domains.append(domain)
        return domains
