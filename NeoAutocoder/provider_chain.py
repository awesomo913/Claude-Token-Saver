import time
import random
import json
from typing import List, Dict, Callable, Optional, Any
from dataclasses import dataclass
import requests
from pathlib import Path

from session import ProviderEntry

# Improvement focuses - curated to ~10 high-impact per tune-up skill (avoids proliferation)
IMPROVEMENT_FOCUSES = {
    "Deep Code Dive": "Perform a deep architectural review. Identify hidden complexities, edge cases, and optimization opportunities in the core logic. Improve without changing the public interface.",
    "Extra Features": "Add one thoughtful, well-integrated new feature that enhances usability or capability. Implement it cleanly and document it.",
    "Pressure Test": "Add comprehensive error handling, input validation, logging, and resilience. Make it production-solid. Include tests if appropriate.",
    "Explore & Expand": "Think creatively. Add a companion module, utility, or extension that complements the main codebase. Keep it cohesive.",
    "Beautiful GUI": "If there's a UI component, enhance visuals, UX, theming, accessibility, and responsiveness. Use modern patterns.",
    "Solid & Functional": "Ensure correctness, clean code, proper separation of concerns, type hints, and comprehensive docstrings.",
    "Reference Images": "If visual, ensure output matches reference style. Otherwise, improve formatting and structure to professional standards.",
    "Review & Grade": "Self-review the entire codebase. Provide specific improvements, then implement the top 3. CODE MUST COME FIRST in output.",
}

FOCUS_ORDER = ["Solid & Functional", "Deep Code Dive", "Pressure Test", "Extra Features", 
               "Beautiful GUI", "Explore & Expand", "Review & Grade"]  # Curated subset

class ProviderChain:
    """Full production-ready provider chain with cooldowns, cycling, and fallbacks."""
    
    def __init__(self, config_dir: Path = None):
        if config_dir is None:
            config_dir = Path.home() / ".neoautocoder"
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.providers: List[ProviderEntry] = []
        self.current_index = 0
        self.rotation_interval = 5  # iterations before forced rotation
        self.iter_since_rotation = 0
        
        self._register_providers()
    
    def _register_providers(self):
        """Register in ranked order: API first for stability, then CDP browsers."""
        
        # OpenRouter API (preferred - stable, many free models)
        def openrouter_factory():
            from openrouter_api_client import OpenRouterClient
            return OpenRouterClient(config_dir=self.config_dir)
        
        self.providers.append(ProviderEntry(
            name="OpenRouter_API",
            factory=openrouter_factory,
            cooldown_sec_on_failure=60.0,  # Faster recovery for API
        ))
        
        # Gemini CDP (excellent context)
        def gemini_factory():
            from cdp_client import connect_to_ai_site
            return connect_to_ai_site("Gemini", port=9222)
        
        self.providers.append(ProviderEntry(
            name="Gemini_CDP",
            factory=gemini_factory,
        ))
        
        # ChatGPT CDP
        def chatgpt_factory():
            from cdp_client import connect_to_ai_site
            return connect_to_ai_site("ChatGPT", port=9225)
        
        self.providers.append(ProviderEntry(
            name="ChatGPT_CDP",
            factory=chatgpt_factory,
        ))
        
        # Ollama local
        def ollama_factory():
            from ollama_api_client import OllamaClient
            return OllamaClient()
        
        self.providers.append(ProviderEntry(
            name="Ollama_Local",
            factory=ollama_factory,
            cooldown_sec_on_failure=30.0,
        ))
        
        # Copilot as last resort
        def copilot_factory():
            from cdp_client import connect_to_ai_site
            return connect_to_ai_site("Copilot", port=9224)
        
        self.providers.append(ProviderEntry(
            name="Copilot_CDP",
            factory=copilot_factory,
        ))
    
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
    
    def get_current_focus(self, iteration: int) -> str:
        """Cycle through curated focuses."""
        return FOCUS_ORDER[iteration % len(FOCUS_ORDER)]
    
    def save_config(self):
        """Persist provider stats."""
        stats = {p.name: {"successes": p.successes, "failures": p.failures} for p in self.providers}
        (self.config_dir / "provider_stats.json").write_text(json.dumps(stats, indent=2))
