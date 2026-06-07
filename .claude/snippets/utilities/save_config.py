# From: NeoAutocoder/provider_chain.py:180
# Persist provider stats.

    def save_config(self):
        """Persist provider stats."""
        stats = {p.name: {"successes": p.successes, "failures": p.failures} for p in self.providers}
        (self.config_dir / "provider_stats.json").write_text(json.dumps(stats, indent=2))
