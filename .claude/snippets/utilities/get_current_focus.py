# From: NeoAutocoder/provider_chain.py:176
# Cycle through curated focuses.

    def get_current_focus(self, iteration: int) -> str:
        """Cycle through curated focuses."""
        return FOCUS_ORDER[iteration % len(FOCUS_ORDER)]
