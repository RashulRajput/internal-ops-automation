from __future__ import annotations

import json
import os
import re
import ssl
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Optional

_SSL_CTX = ssl.create_default_context()

class LLMProvider(ABC):
    name = "unknown"
    model = "unknown"
    kind = "cloud-free"

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        raise NotImplementedError

    def _post_json(self, url: str, payload: dict, headers: dict | None = None, timeout: int = 45) -> dict:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json", **(headers or {})},
            method="POST",
        )
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=timeout) as res:
            return json.loads(res.read().decode("utf-8"))

    def _get_json(self, url: str, headers: dict | None = None, timeout: int = 8) -> dict:
        req = urllib.request.Request(url, headers={"Accept": "application/json", **(headers or {})})
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=timeout) as res:
            return json.loads(res.read().decode("utf-8"))

class GeminiProvider(LLMProvider):
    name = "Gemini Free"
    model = "gemini-2.0-flash"
    base = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        url = f"{self.base}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.25},
        }
        data = self._post_json(url, payload)
        return data["candidates"][0]["content"]["parts"][0]["text"]

class GroqProvider(LLMProvider):
    name = "Groq Free"
    model = "llama-3.3-70b-versatile"
    base = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.25,
        }
        data = self._post_json(self.base, payload, {"Authorization": f"Bearer {self.api_key}"})
        return data["choices"][0]["message"]["content"]

class HuggingFaceProvider(LLMProvider):
    name = "Hugging Face Free"
    model = "mistralai/Mistral-7B-Instruct-v0.3"
    base = "https://api-inference.huggingface.co/models"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        prompt = f"<s>[INST] {system_prompt}\n\n{user_prompt} [/INST]"
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": max_tokens, "temperature": 0.25, "return_full_text": False},
            "options": {"wait_for_model": True},
        }
        data = self._post_json(
            f"{self.base}/{self.model}",
            payload,
            {"Authorization": f"Bearer {self.api_key}"},
            timeout=60,
        )
        if isinstance(data, list) and data:
            return data[0].get("generated_text", "").strip()
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"].strip()
        raise RuntimeError(f"Unexpected Hugging Face response: {data}")

class OllamaProvider(LLMProvider):
    name = "Ollama Local"
    kind = "local"

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": max_tokens},
        }
        data = self._post_json(f"{self.base_url}/api/chat", payload, {}, timeout=30)
        return data.get("message", {}).get("content", "").strip()

    def ping(self) -> bool:
        try:
            self._get_json(f"{self.base_url}/api/tags", timeout=4)
            return True
        except Exception:
            return False

def build_provider_chain() -> list[LLMProvider]:
    chain: list[LLMProvider] = []
    mode = os.environ.get("AI_PROVIDER_MODE", "free-first").strip().lower()
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()
    ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b").strip()

    cloud_providers: list[LLMProvider] = []
    if os.environ.get("GEMINI_API_KEY", "").strip():
        cloud_providers.append(GeminiProvider(os.environ["GEMINI_API_KEY"].strip()))
    if os.environ.get("GROQ_API_KEY", "").strip():
        cloud_providers.append(GroqProvider(os.environ["GROQ_API_KEY"].strip()))
    if os.environ.get("HUGGINGFACE_API_KEY", "").strip():
        cloud_providers.append(HuggingFaceProvider(os.environ["HUGGINGFACE_API_KEY"].strip()))

    ollama = OllamaProvider(ollama_url, ollama_model)
    if mode == "ollama-first":
        chain.append(ollama)
        chain.extend(cloud_providers)
    elif mode == "ollama-only":
        chain.append(ollama)
    else:
        chain.extend(cloud_providers)
        chain.append(ollama)
    return chain

_CHAIN: Optional[list[LLMProvider]] = None

def get_chain() -> list[LLMProvider]:
    global _CHAIN
    if _CHAIN is None:
        _CHAIN = build_provider_chain()
    return _CHAIN

def reset_chain() -> None:
    global _CHAIN
    _CHAIN = None

def active_provider_name() -> str:
    for provider in get_chain():
        if isinstance(provider, OllamaProvider) and not provider.ping():
            continue
        return provider.name
    return "Local fallback"

def llm_call(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
    errors: list[str] = []
    for provider in get_chain():
        try:
            return provider.complete(system_prompt, user_prompt, max_tokens)
        except Exception as exc:
            errors.append(f"{provider.name}: {exc}")
    raise RuntimeError("All configured AI providers failed: " + "; ".join(errors))

def llm_json(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> dict:
    raw = llm_call(system_prompt, user_prompt, max_tokens)
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end >= start:
        cleaned = cleaned[start:end + 1]
    return json.loads(cleaned)

def get_provider_status() -> list[dict]:
    status: list[dict] = []
    for provider in get_chain():
        entry = {"name": provider.name, "model": provider.model, "kind": provider.kind, "configured": True, "available": False}
        try:
            if isinstance(provider, OllamaProvider):
                entry["available"] = provider.ping()
            else:
                entry["available"] = bool(provider.complete("Reply with OK only.", "ping", max_tokens=8))
        except Exception:
            entry["available"] = False
        status.append(entry)
    if not status:
        status.append({"name": "Local fallback", "model": "rules", "kind": "local", "configured": True, "available": True})
    return status

def benchmark_providers(prompt: str = "Say hello in one sentence.") -> list[dict]:
    results: list[dict[str, Any]] = []
    for provider in get_chain():
        started = time.time()
        item: dict[str, Any] = {
            "provider": provider.name,
            "model": provider.model,
            "kind": provider.kind,
            "latency_ms": 0,
            "success": False,
            "response_preview": "",
            "error": None,
        }
        try:
            response = provider.complete("You are a concise assistant.", prompt, max_tokens=80)
            item["success"] = True
            item["response_preview"] = response[:180]
        except Exception as exc:
            item["error"] = str(exc)[:250]
        item["latency_ms"] = round((time.time() - started) * 1000)
        results.append(item)
    return results

try:
    from langchain_core.language_models.chat_models import SimpleChatModel
    from langchain_core.messages import BaseMessage

    class OpsPilotLLM(SimpleChatModel):
        def _call(self, messages: list[BaseMessage], stop: Optional[list[str]] = None, **kwargs: Any) -> str:
            system_parts: list[str] = []
            user_parts: list[str] = []
            for msg in messages:
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                if msg.type == "system":
                    system_parts.append(content)
                else:
                    user_parts.append(content)
            return llm_call("\n".join(system_parts) or "You are a helpful assistant.", "\n".join(user_parts))

        @property
        def _llm_type(self) -> str:
            return "opspilot-free-first"

except ImportError:
    class OpsPilotLLM:
        def _call(self, messages: list, stop: Optional[list[str]] = None, **kwargs: Any) -> str:
            return llm_call("You are a helpful assistant.", "\n".join(str(m) for m in messages))

        @property
        def _llm_type(self) -> str:
            return "opspilot-free-first"
