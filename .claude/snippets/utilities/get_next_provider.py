# From: NeoAutocoder/provider_chain.py:97
# Get next available provider, respecting cooldowns and rotation.

    def get_next_provider(self, force_rotation: bool = False) -> ProviderEntry:
        """Get next available provider, respecting cooldowns and rotation."""
        self.iter_since_rotation += 1
        
        if force_rotation or self.iter_since_rotation >= self.rotation_interval:
            self.current_index = (self.current_index + 1) % len(self.providers)
            self.iter_since_rotation = 0
            print(f"[ProviderChain] Rotated to {self.providers[self.current_index].name}")
        
        start_index = self.current_index
        for _ in range(len(self.providers)):
            provider = self.providers[self.current_index]
            if not provider.is_on_cooldown() and provider.client is not None:
                return provider
            
            # Lazy init client if not present
            if provider.client is None:
                try:
                    provider.client = provider.factory()
                    if provider.client:
                        print(f"[ProviderChain] Initialized {provider.name}")
                        return provider
                except Exception as e:
                    print(f"[ProviderChain] Failed to init {provider.name}: {e}")
                    provider.record_failure()
            
            self.current_index = (self.current_index + 1) % len(self.providers)
        
        # All on cooldown - return first one anyway (will handle in caller)
        self.current_index = start_index
        return self.providers[self.current_index]
