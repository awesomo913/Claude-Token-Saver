"""Ollama model manager — list, pull, delete, select models via HTTP API.

No external deps. Pure urllib against localhost:11434.
"""

from __future__ import annotations

import json
import logging
import threading
import urllib.request
from typing import Any, Callable, Optional
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)

DEFAULT_HOST = "http://localhost:11434"

# Models recommended for search assist (small, fast, won't kill your PC)
RECOMMENDED_MODELS = [
    {"name": "qwen2.5:0.5b", "desc": "Tiny 0.5B — fastest, lowest RAM (~400MB)", "size": "0.4 GB"},
    {"name": "qwen2.5:1.5b", "desc": "Small 1.5B — good balance (~1GB RAM)", "size": "1.0 GB"},
    {"name": "qwen2.5-coder:1.5b", "desc": "Code-tuned 1.5B — best for code search", "size": "1.0 GB"},
    {"name": "llama3.2:1b", "desc": "Meta 1B — fast general purpose", "size": "0.7 GB"},
    {"name": "phi3:mini", "desc": "Microsoft 3.8B — smarter but heavier (~2.5GB)", "size": "2.3 GB"},
    {"name": "gemma2:2b", "desc": "Google 2B — good reasoning (~1.5GB)", "size": "1.6 GB"},
    {"name": "deepseek-coder:1.3b", "desc": "Code-focused 1.3B", "size": "0.8 GB"},
    {"name": "tinyllama", "desc": "TinyLlama 1.1B — ultra light", "size": "0.6 GB"},
]

TURBO_QUANTS = {"q4_k_m", "q4_k_s", "q5_k_m", "q5_k_s", "q4_0", "q5_0"}
CODING_KEYWORDS = ["coder", "code", "deepseek", "starcoder", "codellama", "qwen2.5-coder"]


class OllamaManager:
    """Manages Ollama models via HTTP API. No pip package needed."""

    def __init__(self, host: str = DEFAULT_HOST) -> None:
        self.host = host.rstrip("/")
        self._current_model: Optional[str] = None
        self._models_cache: list[dict] = []

    # ── Server status ──────────────────────────────────────────────────

    def is_running(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            self._api_get("/api/tags", timeout=3)
            return True
        except Exception:
            return False

    # ── Model listing ──────────────────────────────────────────────────

    def list_models(self) -> list[dict[str, Any]]:
        """Get all locally installed models with metadata."""
        try:
            data = self._api_get("/api/tags", timeout=5)
            raw = data.get("models", [])
            models = []
            for m in raw:
                name = m.get("model", "") or m.get("name", "")
                size = m.get("size", 0) or 0
                size_gb = round(size / (1024**3), 1)
                details = m.get("details", {}) or {}
                quant = details.get("quantization_level", "") or _detect_quant(name)
                models.append({
                    "name": name,
                    "size_gb": size_gb,
                    "family": details.get("family", "unknown"),
                    "parameters": details.get("parameter_size", "?"),
                    "quantization": quant.upper() if quant else "DEFAULT",
                    "modified": str(m.get("modified_at", ""))[:19],
                })
            self._models_cache = models
            return models
        except Exception as e:
            logger.debug("Failed to list models: %s", e)
            return []

    def get_model_names(self) -> list[str]:
        """Just the names."""
        return [m["name"] for m in self.list_models()]

    # ── Model selection ────────────────────────────────────────────────

    def select_best(self) -> Optional[str]:
        """Auto-select the best small model for search assist.

        Priority: coding+turbo > coding > small turbo > first available.
        """
        models = self.list_models()
        if not models:
            return None

        # Pass 1: coding + turbo quant
        for m in models:
            nl = m["name"].lower()
            if any(k in nl for k in CODING_KEYWORDS) and m["quantization"].lower() in TURBO_QUANTS:
                self._current_model = m["name"]; return m["name"]

        # Pass 2: any coding model
        for m in models:
            if any(k in m["name"].lower() for k in CODING_KEYWORDS):
                self._current_model = m["name"]; return m["name"]

        # Pass 3: smallest model (for search, we want fast not smart)
        models_by_size = sorted(models, key=lambda m: m["size_gb"])
        self._current_model = models_by_size[0]["name"]
        return self._current_model

    def set_model(self, name: str) -> None:
        self._current_model = name

    def get_current(self) -> Optional[str]:
        return self._current_model

    # ── Model pulling (download) ───────────────────────────────────────

    def pull_model(
        self,
        model_name: str,
        on_progress: Optional[Callable[[float, str], None]] = None,
        on_done: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Download a model in a background thread. Streams progress."""
        def _run():
            try:
                payload = json.dumps({"name": model_name, "stream": True}).encode()
                req = urllib.request.Request(
                    f"{self.host}/api/pull",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=600) as resp:
                    for line in resp:
                        try:
                            chunk = json.loads(line.decode("utf-8", errors="replace"))
                        except json.JSONDecodeError:
                            continue
                        status = chunk.get("status", "")
                        total = chunk.get("total", 0) or 0
                        completed = chunk.get("completed", 0) or 0
                        pct = (completed / total * 100) if total > 0 else 0
                        if on_progress:
                            on_progress(pct, status)
                if on_done:
                    on_done()
            except Exception as e:
                if on_error:
                    on_error(str(e))

        threading.Thread(target=_run, daemon=True).start()

    # ── Model deletion ─────────────────────────────────────────────────

    def delete_model(self, model_name: str) -> bool:
        """Delete a locally installed model."""
        try:
            payload = json.dumps({"name": model_name}).encode()
            req = urllib.request.Request(
                f"{self.host}/api/delete",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="DELETE",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status == 200
        except Exception as e:
            logger.debug("Failed to delete %s: %s", model_name, e)
            return False

    # ── Generation (for search assist) ─────────────────────────────────

    def interpret_query(self, user_query: str) -> str:
        """Ask the current model to extract search keywords from sloppy English."""
        if not self._current_model:
            return ""

        prompt = (
            "You are a code search assistant. The user describes what they want in "
            "casual English with possible typos. Extract the key technical terms and "
            "programming concepts. Output ONLY a comma-separated list of clean "
            "search keywords, nothing else.\n\n"
            f"User says: \"{user_query}\"\n\nKeywords:"
        )

        try:
            data = self._api_post("/api/generate", {
                "model": self._current_model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 60, "temperature": 0.1},
            }, timeout=15)
            raw = data.get("response", "").strip()
            import re
            keywords = re.sub(r"[^a-zA-Z0-9_, ]", "", raw.split("\n")[0])
            return keywords.strip().strip(",").strip()
        except Exception as e:
            logger.debug("Ollama interpret failed: %s", e)
            return ""

    # ── HTTP helpers ───────────────────────────────────────────────────

    def _api_get(self, path: str, timeout: int = 5) -> dict:
        req = urllib.request.Request(f"{self.host}{path}")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _api_post(self, path: str, body: dict, timeout: int = 30) -> dict:
        payload = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.host}{path}",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))


def _detect_quant(name: str) -> str:
    """Detect quantization from model name."""
    nl = name.lower()
    for q in ["q2_k", "q3_k_s", "q3_k_m", "q4_0", "q4_k_s", "q4_k_m",
              "q5_0", "q5_k_s", "q5_k_m", "q6_k", "q8_0", "fp16"]:
        if q in nl:
            return q
    return ""
