# From: universal_client.py:212
# Try to connect to the AI site via CDP.

    def _try_configure_cdp(self) -> bool:
        """Try to connect to the AI site via CDP."""
        url_pattern = self._profile.url_pattern or AI_URL_PATTERNS.get(self._profile.name, "")
        title_pattern = self._profile.title_pattern

        if not url_pattern and not title_pattern:
            return False

        cdp = connect_to_ai_site(
            profile_name=self._profile.name,
            url_pattern=url_pattern,
            title_pattern=title_pattern,
            port=self._cdp_port,
        )

        if cdp and cdp.is_connected:
            self._cdp = cdp
            self._cdp_available = True
            logger.info("CDP connected to %s: %s", self._profile.name, cdp.connection.get_page_url())
            return True

        return False
