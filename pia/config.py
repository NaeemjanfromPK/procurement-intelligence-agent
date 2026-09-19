"""Central runtime configuration, loaded from environment / .env."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "ollama").lower())
    ollama_base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"))
    temperature: float = field(default_factory=lambda: _float("LLM_TEMPERATURE", 0.1))
    llm_timeout: int = field(default_factory=lambda: _int("LLM_TIMEOUT", 180))
    max_retries: int = field(default_factory=lambda: _int("MAX_RETRIES", 3))
    runs_dir: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("RUNS_DIR", "runs"))

    def model_name(self) -> str:
        return self.ollama_model

    def validate(self) -> None:
        if self.provider not in {"ollama"}:
            raise ValueError(f"LLM_PROVIDER must be 'ollama', got {self.provider!r}")


settings = Settings()
