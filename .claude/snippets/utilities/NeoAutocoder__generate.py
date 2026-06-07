# From: NeoAutocoder/provider_chain.py:129
# Main entrypoint - try providers in order with fallbacks.

    def generate(self, prompt: str, session: Any = None) -> str:
        """Main entrypoint - try providers in order with fallbacks."""
        attempts = 0
        max_attempts = len(self.providers) * 2
        
        while attempts < max_attempts:
            provider = self.get_next_provider()
            attempts += 1
            
            if provider.is_on_cooldown():
                print(f"[ProviderChain] {provider.name} on cooldown, skipping...")
                continue
            
            try:
                if not provider.client:
                    provider.client = provider.factory()
                
                print(f"[ProviderChain] Using {provider.name} (successes: {provider.successes}, failures: {provider.failures})")
                
                # Temperature cycling to break identity loops (Fix 9)
                temp = 0.7 + (random.random() * 0.4)  # 0.7-1.1 range
                
                if hasattr(provider.client, 'generate'):
                    response = provider.client.generate(prompt, temperature=temp)
                else:
                    # Assume CDP-style interface
                    response = provider.client.send_prompt(prompt)
                
                if response and len(response.strip()) > 100:  # basic quality gate
                    provider.record_success()
                    return response
                else:
                    print(f"[ProviderChain] Empty or poor response from {provider.name}")
                    provider.record_failure()
                    
            except Exception as e:
                error_str = str(e).lower()
                is_rate_limit = any(k in error_str for k in ["rate", "limit", "429", "quota"])
                provider.record_failure(is_rate_limit=is_rate_limit)
                print(f"[ProviderChain] {provider.name} failed: {e}")
                
                # Smart recovery hint
                if "login" in error_str or "auth" in error_str:
                    print("  → Login issue detected. Consider running auto-login or manual check.")
        
        raise RuntimeError("All providers exhausted or failed. Check connections and credentials.")
