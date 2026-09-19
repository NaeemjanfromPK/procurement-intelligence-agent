"""LLM backend for PIA - Ollama only, local and free."""
from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage, SystemMessage

from .config import Settings, settings as default_settings

_CACHE: dict[tuple, Runnable] = {}


def build_llm(cfg: Settings | None = None, *, json_mode: bool = False) -> Runnable:
    cfg = cfg or default_settings
    key = (cfg.ollama_model, cfg.temperature, json_mode)
    if key in _CACHE:
        return _CACHE[key]

    from langchain_ollama import ChatOllama

    kwargs: dict[str, Any] = {
        "model": cfg.ollama_model,
        "base_url": cfg.ollama_base_url,
        "temperature": cfg.temperature,
        "num_ctx": 8192,
    }
    if json_mode:
        kwargs["format"] = "json"

    llm: Runnable = ChatOllama(**kwargs)
    _CACHE[key] = llm
    return llm


def chat(system: str, user: str, *, llm: Runnable | None = None, json_mode: bool = False) -> str:
    model = llm or build_llm(json_mode=json_mode)
    reply = model.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    content = reply.content
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return str(content).strip()


_FENCE = re.compile(r"`(?:python|py|json)?\s*(.*?)`", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> dict:
    for candidate in (*_FENCE.findall(text), text):
        candidate = candidate.strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return {}


def health_check(cfg: Settings | None = None) -> tuple[bool, str]:
    cfg = cfg or default_settings
    try:
        reply = chat("Reply with the single word: ready", "ping")
        return True, f"ollama:{cfg.ollama_model} -> {reply[:60]!r}"
    except Exception as exc:
        return False, f"ollama:{cfg.ollama_model} unavailable -> {exc}"
