from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path


class LLMProviderError(Exception):
    pass


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str) -> str:
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str | None = None) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMProviderError("OPENAI_API_KEY is not set")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._api_key = api_key

    async def complete(self, prompt: str) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self._api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = response.choices[0].message.content
        if not content:
            raise LLMProviderError("OpenAI returned empty content")
        return content


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str | None = None) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMProviderError("ANTHROPIC_API_KEY is not set")
        self.model = model or os.getenv("LLM_MODEL", "claude-3-5-sonnet-latest")
        self._api_key = api_key

    async def complete(self, prompt: str) -> str:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self._api_key)
        response = await client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [block.text for block in response.content if block.type == "text"]
        if not parts:
            raise LLMProviderError("Anthropic returned empty content")
        return "".join(parts)


def get_llm_provider() -> LLMProvider:
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "anthropic":
        return AnthropicProvider()
    if provider == "openai":
        return OpenAIProvider()
    raise LLMProviderError(f"Unsupported LLM provider: {provider}")


def parse_json_response(text: str) -> object:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str, **kwargs: str) -> str:
    template = (PROMPTS_DIR / name).read_text()
    return template.format(**kwargs)
