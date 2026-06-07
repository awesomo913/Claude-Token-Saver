# From: NeoAutocoder/session.py:62
# Exact match to original ProviderEntry.

@dataclass
class ProviderEntry:
    """Exact match to original ProviderEntry."""
    name: str
    factory: Any  # Callable[[], object]
    client: Optional[Any] = None
    cooldown_until: float = 0.0
    failures: int = 0
    successes: int = 0
    cooldown_sec_on_failure: float = 120.0
    cooldown_sec_on_rate_limit: float = 300.0

    def is_on_cooldown(self) -> bool:
        from time import time
        return time() < self.cooldown_until

    def record_failure(self, is_rate_limit: bool = False):
        self.failures += 1
        cooldown = self.cooldown_sec_on_rate_limit if is_rate_limit else self.cooldown_sec_on_failure
        from time import time
        self.cooldown_until = time() + cooldown

    def record_success(self):
        self.successes += 1
        self.failures = max(0, self.failures - 1)
