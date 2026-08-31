"""
Centralised configuration. This project only ever talks to a local, free
LLM backend (Ollama) — there is no paid provider path in this repository
at all, by design, so there's nothing to accidentally enable.
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    max_tokens: int = int(os.environ.get("RECURO_MAX_TOKENS", "800"))
    # Lower temperature: this is a healthcare-adjacent coach, not a creative assistant.
    temperature: float = float(os.environ.get("RECURO_TEMPERATURE", "0.2"))
    env: str = os.environ.get("RECURO_ENV", "dev")  # dev | prod

    # Free, local LLM backend — no API key, ever, anywhere in this repo.
    ollama_model: str = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
    ollama_base_url: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


settings = Settings()
