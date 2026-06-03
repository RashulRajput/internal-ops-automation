"""
providers.py — Multi-provider LLM layer for OpsPilot.

Priority order: Gemini → Groq → Mistral → local fallback (handled by callers).

All HTTP calls use urllib.request only (no pip dependencies).
"""
from __future__ import annotations

import json
import os
import re
import ssl
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Optional

# ---------------------------------------------------------------------------
# SSL context — verify server certificates (safe for production)
# ---------------------------------------------------------------------------
_SSL_CTX = ssl.create_default_context()


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------
class LLMProvider(ABC):
    name: str = "unknown"

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        """Return the model's text response, or raise on failure."""

    def _post_json(self, url: str, payload: dict, headers: dict) -> dict:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            **headers
        }, method="POST")
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# Gemini provider
# ---------------------------------------------------------------------------
class GeminiProvider(LLMProvider):
    name = "Gemini"
    MODEL = "gemini-2.5-flash"
    BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str):
        self._key = api_key

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        url = f"{self.BASE}/{self.MODEL}:generateContent?key={self._key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.3}
        }
        resp = self._post_json(url, payload, {})
        return resp["candidates"][0]["content"]["parts"][0]["text"]


# ---------------------------------------------------------------------------
# Groq provider
# ---------------------------------------------------------------------------
class GroqProvider(LLMProvider):
    name = "Groq"
    MODEL = "llama-3.3-70b-versatile"
    BASE = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str):
        self._key = api_key

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        payload = {
            "model": self.MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        resp = self._post_json(self.BASE, payload, {"Authorization": f"Bearer {self._key}"})
        return resp["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Mistral provider
# ---------------------------------------------------------------------------
class MistralProvider(LLMProvider):
    name = "Mistral"
    MODEL = "open-mixtral-8x7b"
    BASE = "https://api.mistral.ai/v1/chat/completions"

    def __init__(self, api_key: str):
        self._key = api_key

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        payload = {
            "model": self.MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        resp = self._post_json(self.BASE, payload, {"Authorization": f"Bearer {self._key}"})
        return resp["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Provider chain builder
# ---------------------------------------------------------------------------
def build_provider_chain() -> list[LLMProvider]:
    """
    Return a list of available providers in priority order.
    Keys are read from environment variables.
    """
    chain: list[LLMProvider] = []
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    mistral_key = os.environ.get("MISTRAL_API_KEY", "").strip()

    if gemini_key:
        chain.append(GeminiProvider(gemini_key))
    if groq_key:
        chain.append(GroqProvider(groq_key))
    if mistral_key:
        chain.append(MistralProvider(mistral_key))
    return chain


# Module-level cached chain (built once after env is loaded)
_CHAIN: Optional[list[LLMProvider]] = None


def get_chain() -> list[LLMProvider]:
    global _CHAIN
    if _CHAIN is None:
        _CHAIN = build_provider_chain()
    return _CHAIN


def reset_chain() -> None:
    """Call after loading env vars so the chain is rebuilt."""
    global _CHAIN
    _CHAIN = None


def active_provider_name() -> str:
    chain = get_chain()
    return chain[0].name if chain else "Local"


# ---------------------------------------------------------------------------
# Core LLM call helpers
# ---------------------------------------------------------------------------
def llm_call(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
    """
    Try each provider in order. Return the first successful response text.
    Raises RuntimeError if all providers fail (callers should catch and
    fall back to local logic).
    """
    errors = []
    for provider in get_chain():
        try:
            return provider.complete(system_prompt, user_prompt, max_tokens)
        except Exception as exc:
            errors.append(f"{provider.name}: {exc}")
    raise RuntimeError("All LLM providers failed: " + "; ".join(errors))


def llm_json(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> dict:
    """
    Same as llm_call but attempts to parse the response as JSON.
    Strips markdown code fences if present.
    Raises RuntimeError if all providers fail, or ValueError if JSON is bad.
    """
    raw = llm_call(system_prompt, user_prompt, max_tokens)
    # Strip ```json ... ``` or ``` ... ``` fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
    return json.loads(cleaned.strip())
