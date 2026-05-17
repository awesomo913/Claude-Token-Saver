# From: claude_backend/ollama_manager.py:303
# Detect quantization from model name.

def _detect_quant(name: str) -> str:
    """Detect quantization from model name."""
    nl = name.lower()
    for q in ["q2_k", "q3_k_s", "q3_k_m", "q4_0", "q4_k_s", "q4_k_m",
              "q5_0", "q5_k_s", "q5_k_m", "q6_k", "q8_0", "fp16"]:
        if q in nl:
            return q
    return ""
